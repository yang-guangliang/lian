#! /usr/bin/env python3
import json
import os, sys
import re
from collections import deque

import yaml

import lian.config.config as config
import networkx as nx

from lian.events.default_event_handlers.this_field_write import access_path_formatter
from lian.util import util
from lian.util.readable_gir import get_gir_str
from lian.taint.rule_manager import RuleManager, Rule
from lian.common_structs import (
    CallPath,
    SimpleWorkList,
    State,
    Symbol,
    ComputeFrameStack,
    SymbolStateSpace,
    CallSite,
)

from lian.config.constants import (
    SFG_NODE_KIND,
    SFG_EDGE_KIND,
    TAG_KEYWORD
)

from lian.taint.taint_structs import (
    TaintEnv,
    Flow,
)

class TaintRuleApplier:
    def __init__(self, taint_analysis):
        self.taint_analysis = taint_analysis
        self.loader = taint_analysis.loader
        self.sfg = taint_analysis.sfg
        self.rule_manager = taint_analysis.rule_manager

    def apply_parameter_source_rules(self, node):
        stmt_id = node.def_stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
        unit_id = self.loader.convert_stmt_id_to_unit_id(stmt_id)
        unit_path = self.loader.convert_unit_id_to_unit_path(unit_id)
        stmt = self.loader.get_stmt_gir(method_id)
        if not stmt.attrs:
            return False
        if not isinstance(stmt.attrs, str):
            return False
        attrs = stmt.attrs
        parameter_symbol = list(util.graph_successors(self.sfg, node))[0]
        for rule in self.rule_manager.all_sources:
            if rule.unit_path and rule.unit_path != unit_path:
                continue
            if rule.line_num and rule.line_num != str(stmt.line_no):
                continue
            if not rule.attr and rule.name == parameter_symbol.name:
                return True
            if rule.operation != "parameter_decl":
                continue
            if rule.attr and rule.attr not in attrs:
                continue
            if rule.name == parameter_symbol.name:
                return True
        return False

    def apply_field_read_source_rules(self, node):
        # 找到类型为 symbol 的父节点，以及该 symbol 节点的类型为 state 的子节点
        symbol_node, state_nodes = self.taint_analysis.get_stmt_define_symbol_and_states_node(node)
        if not symbol_node or not state_nodes:
            return False

        for rule in self.rule_manager.all_sources:
            if rule.operation != "field_read":
                continue

            for state_node in state_nodes:
                # 格式化访问路径
                access_path = access_path_formatter(state_node.access_path)
                if access_path == rule.target:
                    return True

        return False

    def apply_call_stmt_source_rules(self, node):
        stmt_id = node.def_stmt_id
        unit_id = self.loader.convert_stmt_id_to_unit_id(stmt_id)
        unit_path = self.loader.convert_unit_id_to_unit_path(unit_id)
        method_symbol_node, method_state_nodes = self.taint_analysis.get_stmt_first_used_symbol_and_state(node)
        defined_symbol_node, defined_state_nodes = self.taint_analysis.get_stmt_define_symbol_and_states_node(node)
        if not method_symbol_node or not defined_symbol_node:
            return False

        tag_space_id = defined_symbol_node.node_id
        apply_rule_flag = False
        for rule in self.rule_manager.all_sources:
            if rule.unit_path and rule.unit_path != unit_path:
                continue
            if rule.line_num and rule.line_num != int(node.line_no+1):
                continue
            if rule.operation != "call_stmt":
                continue
            tag_info = rule
            name = tag_info.name
            for state_node in method_state_nodes:
                state_access_path = state_node.access_path
                if isinstance(state_access_path, str):
                    continue
                access_path = access_path_formatter(state_access_path)

                if len(access_path) == 0:
                    access_path = method_symbol_node.name
                if access_path == name:
                    apply_rule_flag = True
                    tag = self.taint_analysis.taint_manager.get_symbol_tag(tag_space_id)
                    new_tag = self.taint_analysis.taint_manager.add_and_update_tag_bv(tag_info=tag_info,
                                                                                      current_taint=tag)
                    self.taint_analysis.taint_manager.set_symbols_tag([tag_space_id], new_tag)
                    for defined_state_node in defined_state_nodes:
                        self.taint_analysis.taint_manager.set_states_tag([defined_state_node.node_id], new_tag)

        return apply_rule_flag

    def should_apply_object_call_stmt_sink_rules(self, node):
        if node.node_type != SFG_NODE_KIND.STMT or node.name != "object_call_stmt":
            return False
        stmt = self.loader.get_stmt_gir(node.def_stmt_id)
        name = stmt.receiver_object + '.' + stmt.field
        for rule in self.rule_manager.all_sinks:
            if rule.name == name:
                return True
        return False

    def should_apply_call_stmt_sink_rules(self, node):
        if node.node_type != SFG_NODE_KIND.STMT or node.name != "call_stmt":
            return False
        stmt_id = node.def_stmt_id
        method_symbol_node, method_state_nodes = self.taint_analysis.get_stmt_first_used_symbol_and_state(node)

        for rule in self.rule_manager.all_sinks:
            for state_node in method_state_nodes:
                # 检查函数名是否符合规则
                if self.check_method_name(rule.name, state_node):
                    return True

        return False

    def check_method_name(self, rule_name, method_state):
        state_access_path = method_state.access_path
        rule_name_parts = rule_name.split('.')
        if len(state_access_path) < len(rule_name_parts):
            return False
        # name匹配上
        for i, item in enumerate(reversed(rule_name_parts)):
            if item == TAG_KEYWORD.ANYNAME:
                continue
            if item != state_access_path[-i - 1].key:
                return False
        return True

    def apply_propagation_rules(self, node):
        stmt_id = node.def_stmt_id
        stmt = self.loader.get_stmt_gir(stmt_id)
        operation = node.name

        # 默认认为赋值语句传播污点
        if operation == "assign_stmt":
            return True

        for rule in self.rule_manager.all_propagations:
            if rule.operation != operation:
                continue

            if operation == "field_read":
                # 1. 检查字段名列表 (field: [split, next, ...])
                if hasattr(stmt, 'field') and rule.field:
                    if stmt.field in rule.field:
                        return True
                # 2. 检查特定 target (target: request.query_string)
                symbol_node, state_nodes = self.taint_analysis.get_stmt_define_symbol_and_states_node(node)
                if state_nodes:
                    for state_node in state_nodes:
                        access_path = access_path_formatter(state_node.access_path)
                        if access_path == rule.target:
                            return True
                # 3. 简单的 src/dst 规则 (如 src: receiver)
                if not rule.field and not rule.target:
                    return True

            elif operation == "call_stmt":
                # 检查函数名是否符合规则
                method_symbol_node, method_state_nodes = self.taint_analysis.get_stmt_first_used_symbol_and_state(node)
                if method_state_nodes:
                    for state_node in method_state_nodes:
                        if self.check_method_name(rule.name, state_node):
                            return True
                # 如果都没有匹配上，但规则确实是 call_stmt 且没有指定 name（较少见），可以返回 True
                if not rule.name:
                    return True

        return False

    def get_sink_tag_by_rules(self, node):
        sink_tag = 0
        if node.node_type != SFG_NODE_KIND.STMT:
            return sink_tag

        stmt_id = node.def_stmt_id
        stmt = self.loader.get_stmt_gir(stmt_id)
        operation = node.name

        # 1. 寻找匹配的 sink 规则
        matching_rules = []
        if operation == "call_stmt":
            _, method_state_nodes = self.taint_analysis.get_stmt_first_used_symbol_and_state(node)
            for rule in self.rule_manager.all_sinks:
                if rule.operation != "call_stmt":
                    continue
                if not method_state_nodes:
                    if rule.name == stmt.name:
                        matching_rules.append(rule)
                    continue
                for state_node in method_state_nodes:
                    if self.check_method_name(rule.name, state_node):
                        matching_rules.append(rule)
                        break
        elif operation == "object_call_stmt":
            name = stmt.receiver_object + '.' + stmt.field
            for rule in self.rule_manager.all_sinks:
                if rule.name == name:
                    matching_rules.append(rule)

        # 2. 根据规则检查对应的 symbol 和 state
        for rule in matching_rules:
            targets = rule.target if isinstance(rule.target, list) else [rule.target]
            for target in targets:
                target_pos = -1
                if target == TAG_KEYWORD.ARG0:
                    target_pos = 1
                elif target == TAG_KEYWORD.ARG1:
                    target_pos = 2
                elif target == TAG_KEYWORD.ARG2:
                    target_pos = 3
                elif target == TAG_KEYWORD.ARG3:
                    target_pos = 4
                elif target == TAG_KEYWORD.ARG4:
                    target_pos = 5
                elif target == TAG_KEYWORD.RECEIVER:
                    target_pos = 0

                for pred in self.sfg.predecessors(node):
                    edge_data = self.sfg.get_edge_data(pred, node)
                    if not edge_data: continue
                    for data in edge_data.values():
                        weight = data.get('weight')
                        if weight.edge_type != SFG_EDGE_KIND.SYMBOL_IS_USED:
                            continue

                        weight_pos = weight.pos
                        if operation == "object_call_stmt":
                            weight_pos -= 1

                        # 匹配位置或者目标是通配符
                        if (target_pos != -1 and weight_pos == target_pos) or \
                            (target == TAG_KEYWORD.TARGET) or \
                            (not target):
                            sink_tag |= self.taint_analysis.get_symbol_with_states_tag(pred)

        return sink_tag


class TaintAnalysis:
    def __init__(self, lian, options):
        self.lian = lian
        self.loader = self.lian.loader
        self.options = options
        self.default_settings = options.default_settings
        self.taint_manager: TaintEnv = None
        self.rule_manager = RuleManager(options.default_settings)
        self.current_entry_point = -1
        self.sfg = None
        self.rule_applier = TaintRuleApplier(self)

    def _update_sfg(self, sfg):
        self.sfg = sfg
        self.rule_applier.sfg = sfg

    def read_rules(self, operation, source_rules):
        """从src.yaml文件中获取field_read语句类型的规则, 并根据每条规则创建taint_bv"""
        rules = []

        for rule in source_rules:
            if rule.operation == operation:
                rules.append(rule)
        return rules

    def get_stmt_first_used_symbol_and_state(self, node):
        if node.node_type != SFG_NODE_KIND.STMT:
            return None, None
        state_nodes = []
        predecessors = list(util.graph_predecessors(self.sfg, node))
        name_symbol_node = None
        if len(predecessors) == 0:
            return None, None
        for predecessor in predecessors:
            edge = self.sfg.get_edge_data(predecessor, node)
            if edge and edge[0]['weight'].pos == 0:
                name_symbol_node = predecessor
        name_symbol_successors = list(util.graph_successors(self.sfg, name_symbol_node))
        for successor in name_symbol_successors:
            if successor.node_type == SFG_NODE_KIND.STATE:
                state_nodes.append(successor)
        return name_symbol_node, state_nodes

    def get_stmt_define_symbol_and_states_node(self, node):
        if node.node_type != SFG_NODE_KIND.STMT:
            return None, None
        successors = list(util.graph_successors(self.sfg, node))
        define_symbol_node = None
        for successor in successors:
            edge = self.sfg.get_edge_data(node, successor)
            if edge and edge[0]['weight'].edge_type == SFG_EDGE_KIND.SYMBOL_IS_DEFINED:
                define_symbol_node = successor
        define_symbol_successors = list(util.graph_successors(self.sfg, define_symbol_node))
        define_state_list = []
        for successor in define_symbol_successors:
            edge = self.sfg.get_edge_data(define_symbol_node, successor)
            if edge and edge[0]['weight'].edge_type == SFG_EDGE_KIND.SYMBOL_STATE:
                define_state_list.append(successor)
        return define_symbol_node, define_state_list

    def find_sources(self):
        node_list = []
        # 应该包括所有的可能symbol和state节点作为sources
        # 这里应该应用source的规则
        # 遍历sfg
        for node in self.sfg.nodes:
            if node.node_type != SFG_NODE_KIND.STMT:
                continue
            if node.name == "call_stmt":
                if self.rule_applier.apply_call_stmt_source_rules(node):
                    defined_symbol_node, defined_state_nodes = self.get_stmt_define_symbol_and_states_node(node)
                    node_list.append(defined_symbol_node)
            if node.name == "parameter_decl":
                if self.rule_applier.apply_parameter_source_rules(node):
                    defined_symbol_node, defined_state_nodes = self.get_stmt_define_symbol_and_states_node(node)
                    node_list.append(defined_symbol_node)
            if node.name == "field_read":
                if self.rule_applier.apply_field_read_source_rules(node):
                    defined_symbol_node, defined_state_nodes = self.get_stmt_define_symbol_and_states_node(node)
                    node_list.append(defined_symbol_node)
            # 为了兼容codeql规则
            # elif node.node_type == SFG_NODE_KIND.STMT:
            #     rules = self.rule_manager.all_sources_from_code
            #     if self.apply_rules_from_code(node, rules):
            #         node_list.append(node)

        return node_list

    def apply_rules_from_code(self, node, rules):
        stmt_id = node.def_stmt_id

        status = self.get_stmt_status(node, stmt_id)
        stmt = self.loader.get_stmt_gir(stmt_id)
        for rule in rules:
            if str(stmt.start_row) != rule.line_num:
                continue
            symbol_in_stmt = False
            if self.space[status.defined_symbol].name == rule.symbol_name:
                symbol_in_stmt = True
            for symbol_index in status.used_symbols:
                symbol = self.space[symbol_index]
                if symbol.name == rule.symbol_name:
                    symbol_in_stmt = True
            if not symbol_in_stmt:
                continue

    def access_path_formatter(self, state_access_path):
        key_list = []
        for item in state_access_path:
            key = item.key
            key = key if isinstance(key, str) else str(key)
            if key != "":
                key_list.append(key)

        # 使用点号连接所有 key 值
        access_path = '.'.join(key_list)
        return access_path

    def find_sinks(self):
        # 找到所有的sink函数或者语句
        # 这里应该应用sink的规则
        node_list = []
        for node in self.sfg.nodes:
            if self.rule_applier.should_apply_call_stmt_sink_rules(
                node) or self.rule_applier.should_apply_object_call_stmt_sink_rules(node):
                node_list.append(node)
        return node_list

    def check_method_name(self, rule_name, method_state):
        apply_flag = True

        state_access_path = method_state.access_path

        rule_name = rule_name.split('.')
        if len(state_access_path) < len(rule_name):
            return False
        # name匹配上
        for i, item in enumerate(reversed(rule_name)):
            if item == TAG_KEYWORD.ANYNAME:
                continue
            if item != state_access_path[-i - 1].key:
                apply_flag = False
                break

        return apply_flag

    def get_state_with_inclusion_tag(self, state_node):
        """获取 state 节点及其所有通过 inclusion 关系包含的子 state 节点的污点标记总和"""
        tag = 0
        state_worklist = deque([state_node])
        state_visited = {state_node}
        while state_worklist:
            curr_state = state_worklist.popleft()
            tag |= self.taint_manager.get_state_tag(curr_state.node_id)

            for next_state in self.sfg.successors(curr_state):
                if next_state.node_type == SFG_NODE_KIND.STATE and next_state not in state_visited:
                    s_edge_data = self.sfg.get_edge_data(curr_state, next_state)
                    if s_edge_data:
                        for s_data in s_edge_data.values():
                            if s_data.get('weight').edge_type in (
                                    SFG_EDGE_KIND.STATE_INCLUSION,
                                    SFG_EDGE_KIND.INDIRECT_STATE_INCLUSION):
                                state_visited.add(next_state)
                                state_worklist.append(next_state)
                                break
        return tag

    def get_symbol_with_states_tag(self, symbol_node):
        """获取 symbol 节点及其指向的所有 state 节点的污点标记总和"""
        tag = self.taint_manager.get_symbol_tag(symbol_node.node_id)
        for v in self.sfg.successors(symbol_node):
            v_edge_data = self.sfg.get_edge_data(symbol_node, v)
            if v_edge_data:
                for v_data in v_edge_data.values():
                    if v_data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_STATE:
                        tag |= self.get_state_with_inclusion_tag(v)
        return tag

    def get_sink_tag_by_rules(self, node):
        sink_tag = 0
        if node.node_type != SFG_NODE_KIND.STMT:
            return sink_tag

        stmt_id = node.def_stmt_id
        stmt = self.loader.get_stmt_gir(stmt_id)
        operation = node.name

        # 1. 寻找匹配的 sink 规则
        matching_rules = []
        if operation == "call_stmt":
            _, method_state_nodes = self.get_stmt_first_used_symbol_and_state(node)
            for rule in self.rule_manager.all_sinks:
                if rule.operation != "call_stmt":
                    continue
                if not method_state_nodes:
                    if rule.name == stmt.name:
                        matching_rules.append(rule)
                    continue
                for state_node in method_state_nodes:
                    if self.check_method_name(rule.name, state_node):
                        matching_rules.append(rule)
                        break
        elif operation == "object_call_stmt":
            name = stmt.receiver_object + '.' + stmt.field
            for rule in self.rule_manager.all_sinks:
                if rule.name == name:
                    matching_rules.append(rule)

        # 2. 根据规则检查对应的 symbol 和 state
        for rule in matching_rules:
            targets = rule.target if isinstance(rule.target, list) else [rule.target]
            for target in targets:
                target_pos = -1
                if target == TAG_KEYWORD.ARG0:
                    target_pos = 1
                elif target == TAG_KEYWORD.ARG1:
                    target_pos = 2
                elif target == TAG_KEYWORD.ARG2:
                    target_pos = 3
                elif target == TAG_KEYWORD.ARG3:
                    target_pos = 4
                elif target == TAG_KEYWORD.ARG4:
                    target_pos = 5
                elif target == TAG_KEYWORD.RECEIVER:
                    target_pos = 0

                for pred in self.sfg.predecessors(node):
                    edge_data = self.sfg.get_edge_data(pred, node)
                    if not edge_data: continue
                    for data in edge_data.values():
                        weight = data.get('weight')
                        if weight.edge_type != SFG_EDGE_KIND.SYMBOL_IS_USED:
                            continue

                        weight_pos = weight.pos
                        if operation == "object_call_stmt":
                            weight_pos -= 1

                        # 匹配位置或者目标是通配符
                        if (target_pos != -1 and weight_pos == target_pos) or \
                            (target == TAG_KEYWORD.TARGET) or \
                            (not target):
                            sink_tag |= self.get_symbol_with_states_tag(pred)

        return sink_tag

    def find_flows(self, sources, sinks):
        # 找到所有的taint flow
        # 每次处理一个 source 和 一个 sink 的组合
        flow_list = []

        for source in sources:
            for sink in sinks:
                # 1. 污点传播 (针对单一 Source)
                # 为每一次 (source, sink) 组合使用独立的污点管理器，确保隔离
                original_manager = self.taint_manager
                self.taint_manager = TaintEnv()

                # 执行污点传播并获取该 source 的 tag
                tag = self.propagate_taint(source)

                # 2. Sink 检查 (针对单一 Sink)
                sink_tag = self.rule_applier.get_sink_tag_by_rules(sink)

                if (sink_tag & tag) != 0:
                    print("found taint sink")
                    flow = self.reconstruct_define_use_path(source, sink)
                    flow_list.append(flow)

                # 恢复管理器
                self.taint_manager = original_manager

        return flow_list

    def _get_node_tag(self, u):
        """获取节点的污点标记。对于 STMT 节点，其标记来源于它所使用的 SYMBOL。"""
        if u.node_type == SFG_NODE_KIND.SYMBOL:
            return self.taint_manager.get_symbol_tag(u.node_id)
        elif u.node_type == SFG_NODE_KIND.STATE:
            return self.taint_manager.get_state_tag(u.node_id)
        elif u.node_type == SFG_NODE_KIND.STMT:
            u_tag = 0
            for pred in self.sfg.predecessors(u):
                edge_data = self.sfg.get_edge_data(pred, u)
                if edge_data:
                    for data in edge_data.values():
                        if data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_IS_USED:
                            u_tag |= self.taint_manager.get_symbol_tag(pred.node_id)
            return u_tag
        return 0

    def _init_source_contamination(self, source, tag, worklist):
        """对初始 source 节点进行污染标记"""
        if source.node_type == SFG_NODE_KIND.SYMBOL:
            self.taint_manager.set_symbol_tag(source.node_id, tag)
            worklist.append(source)
            # 污染变量对应的初始状态
            for v in self.sfg.successors(source):
                edge_data = self.sfg.get_edge_data(source, v)
                if edge_data:
                    for data in edge_data.values():
                        if data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_STATE:
                            self.taint_manager.set_states_tag([v.node_id], tag)
                            if v not in worklist:
                                worklist.append(v)
        elif source.node_type == SFG_NODE_KIND.STATE:
            self.taint_manager.set_states_tag([source.node_id], tag)
            worklist.append(source)
        elif source.node_type == SFG_NODE_KIND.STMT:
            worklist.append(source)

    def _propagate_from_symbol(self, u, u_tag, worklist):
        """处理从 SYMBOL 节点向下的传播"""
        for v in self.sfg.successors(u):
            edge_data = self.sfg.get_edge_data(u, v)
            if edge_data:
                for data in edge_data.values():
                    etype = data.get('weight').edge_type
                    # 传播到状态或使用该变量的语句
                    if etype == SFG_EDGE_KIND.SYMBOL_STATE:
                        v_tag = self.taint_manager.get_state_tag(v.node_id)
                        if (u_tag | v_tag) != v_tag:
                            self.taint_manager.set_states_tag([v.node_id], u_tag | v_tag)
                            worklist.append(v)
                    elif etype == SFG_EDGE_KIND.SYMBOL_IS_USED:
                        worklist.append(v)

    def _propagate_from_state(self, u, u_tag, worklist):
        """处理从 STATE 节点向下的传播"""
        # 1. 传播到指向该值的变量 (逆向回溯)
        for v in self.sfg.predecessors(u):
            edge_data = self.sfg.get_edge_data(v, u)
            if edge_data:
                for data in edge_data.values():
                    if data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_STATE:
                        v_tag = self.taint_manager.get_symbol_tag(v.node_id)
                        if (u_tag | v_tag) != v_tag:
                            self.taint_manager.set_symbol_tag(v.node_id, u_tag | v_tag)
                            worklist.append(v)

        # 2. 传播到其包含的子状态 (inclusion)
        for v in self.sfg.successors(u):
            if v.node_type == SFG_NODE_KIND.STATE:
                edge_data = self.sfg.get_edge_data(u, v)
                if edge_data:
                    for data in edge_data.values():
                        if data.get('weight').edge_type in (SFG_EDGE_KIND.STATE_INCLUSION,
                                                            SFG_EDGE_KIND.INDIRECT_STATE_INCLUSION):
                            v_tag = self.taint_manager.get_state_tag(v.node_id)
                            if (u_tag | v_tag) != v_tag:
                                self.taint_manager.set_states_tag([v.node_id], u_tag | v_tag)
                                worklist.append(v)

    def _propagate_from_stmt(self, u, u_tag, worklist):
        """处理从 STMT 节点向下的传播"""
        # 根据规则判断语句是否传播污点
        if self.rule_applier.apply_propagation_rules(u):
            for v in self.sfg.successors(u):
                edge_data = self.sfg.get_edge_data(u, v)
                if edge_data:
                    for data in edge_data.values():
                        # 传播到该语句定义的变量
                        if data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_IS_DEFINED:
                            v_tag = self.taint_manager.get_symbol_tag(v.node_id)
                            if (u_tag | v_tag) != v_tag:
                                self.taint_manager.set_symbol_tag(v.node_id, u_tag | v_tag)
                            worklist.append(v)

    def propagate_taint(self, source):
        """
        从给定的 source 开始在 SFG 中传播污点。
        返回为该 source 分配的位标记 (tag)。
        """
        # 为当前 source 分配一个独立的 tag
        tag_info = Rule(name=f"Source_{source.def_stmt_id}", operation="source_propagation", rule_id=id(source))
        tag = self.taint_manager.add_and_update_tag_bv(tag_info, 0)

        worklist = deque()
        self._init_source_contamination(source, tag, worklist)

        # BFS 传播
        while worklist:
            u = worklist.popleft()
            u_tag = self._get_node_tag(u)
            
            if u_tag == 0:
                continue

            if u.node_type == SFG_NODE_KIND.SYMBOL:
                self._propagate_from_symbol(u, u_tag, worklist)
            elif u.node_type == SFG_NODE_KIND.STATE:
                self._propagate_from_state(u, u_tag, worklist)
            elif u.node_type == SFG_NODE_KIND.STMT:
                self._propagate_from_stmt(u, u_tag, worklist)
        return tag
        return tag

    def reconstruct_define_use_path(self, source, sink):
        """
        采用深度优先的方式从 source 开始遍历 SFG 来寻找路径。
        当遍历到 sink_stmt 时，则找到路径；
        如果遍历完整个可达子图都没有遇到 sink，则选一条遍历过程中产生的路径，并加上 sink_stmt。
        """
        visited = set()
        longest_path = []

        def dfs(u, path_stmts):
            nonlocal longest_path
            if u in visited:
                return None
            visited.add(u)

            # 如果当前节点是语句，加入路径
            new_path = list(path_stmts)
            if u.node_type == SFG_NODE_KIND.STMT:
                if not new_path or new_path[-1] != u:
                    new_path.append(u)

            # 记录遍历过程中最长的一条路径作为备选
            if len(new_path) >= len(longest_path):
                longest_path = new_path

            # 到达终点
            if u == sink:
                return new_path

            # 深度优先遍历继承者
            for v in self.sfg.successors(u):
                # 这里可以根据需要过滤边类型，但根据要求我们遍历整个 SFG
                result = dfs(v, new_path)
                if result:
                    return result

            return None

        # 执行 DFS，初始路径根据 source 类型决定
        initial_stmts = []
        # if source.node_type == SFG_NODE_KIND.STMT:
        #     initial_stmts = [source]

        final_path = dfs(source, initial_stmts)

        if final_path is None:
            # 如果没找到 sink，选一条遍历到的路径并强行加上 sink
            if not longest_path or longest_path[-1] != sink:
                final_path = longest_path + [sink]
            else:
                final_path = longest_path

        flow = Flow()
        flow.source_stmt_id = source.def_stmt_id
        flow.sink_stmt_id = sink.def_stmt_id
        flow.parent_to_sink = final_path
        return flow

    def get_all_forward_nodes(self, source):
        """
        从 source 开始，遍历 SFG 返回所有与 taint 有关的 symbol、state、stmt 节点。
        遵循传播逻辑：
        - SYMBOL -> STATE (SYMBOL_STATE), SYMBOL -> STMT (SYMBOL_IS_USED), SYMBOL -> SYMBOL (SYMBOL_FLOW)
        - STATE -> SYMBOL (逆向 SYMBOL_STATE), STATE -> STATE (STATE_INCLUSION/COPY)
        - STMT -> SYMBOL (SYMBOL_IS_DEFINED)
        """
        worklist = deque([source])
        visited = {source}

        while worklist:
            u = worklist.popleft()

            if u.node_type == SFG_NODE_KIND.SYMBOL:
                # 1. 向下传播到 STATE, STMT, 或其他 SYMBOL
                for v in self.sfg.successors(u):
                    if v in visited: continue
                    edge_data = self.sfg.get_edge_data(u, v)
                    if not edge_data: continue
                    for data in edge_data.values():
                        etype = data.get('weight').edge_type
                        if etype in (SFG_EDGE_KIND.SYMBOL_STATE, SFG_EDGE_KIND.SYMBOL_IS_USED,
                                     SFG_EDGE_KIND.SYMBOL_FLOW, SFG_EDGE_KIND.INDIRECT_SYMBOL_FLOW):
                            visited.add(v)
                            worklist.append(v)
                            break

            elif u.node_type == SFG_NODE_KIND.STATE:
                # 1. 找到该值所属的所有 SYMBOL (逆着 SYMBOL_STATE 边)
                for v in self.sfg.predecessors(u):
                    if v in visited: continue
                    edge_data = self.sfg.get_edge_data(v, u)
                    if not edge_data: continue
                    for data in edge_data.values():
                        if data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_STATE:
                            visited.add(v)
                            worklist.append(v)
                            break
                # 2. 向下传播到包含的子状态
                for v in self.sfg.successors(u):
                    if v in visited: continue
                    edge_data = self.sfg.get_edge_data(u, v)
                    if not edge_data: continue
                    for data in edge_data.values():
                        etype = data.get('weight').edge_type
                        if etype in (SFG_EDGE_KIND.STATE_INCLUSION, SFG_EDGE_KIND.INDIRECT_STATE_INCLUSION,
                                     SFG_EDGE_KIND.STATE_COPY):
                            visited.add(v)
                            worklist.append(v)
                            break

            elif u.node_type == SFG_NODE_KIND.STMT:
                # 1. 语句定义的变量受到污染
                for v in self.sfg.successors(u):
                    if v in visited: continue
                    edge_data = self.sfg.get_edge_data(u, v)
                    if not edge_data: continue
                    for data in edge_data.values():
                        if data.get('weight').edge_type == SFG_EDGE_KIND.SYMBOL_IS_DEFINED:
                            visited.add(v)
                            worklist.append(v)
                            break
        return visited

    def get_all_backward_nodes(self, sink_symbol):
        """
        从 sink 的 symbol 开始，逆着 def_use 链遍历 SFG，返回所有与 sink symbol 有关的 symbol、stmt 节点。
        """
        if sink_symbol.node_type != SFG_NODE_KIND.SYMBOL:
            return set()

        worklist = deque([sink_symbol])
        visited = {sink_symbol}

        while worklist:
            u = worklist.popleft()

            # 逆着数据流方向查找前驱
            for v in self.sfg.predecessors(u):
                if v in visited: continue
                edge_data = self.sfg.get_edge_data(v, u)
                if not edge_data: continue

                is_related = False
                for data in edge_data.values():
                    etype = data.get('weight').edge_type
                    if u.node_type == SFG_NODE_KIND.SYMBOL:
                        # SYMBOL 是被谁定义的 (STMT -> SYMBOL) 或 从哪个 SYMBOL 流过来的 (SYMBOL -> SYMBOL)
                        if etype in (SFG_EDGE_KIND.SYMBOL_IS_DEFINED,
                                     SFG_EDGE_KIND.SYMBOL_FLOW, SFG_EDGE_KIND.INDIRECT_SYMBOL_FLOW):
                            is_related = True
                    elif u.node_type == SFG_NODE_KIND.STMT:
                        # STMT 使用了哪个 SYMBOL (SYMBOL -> STMT)
                        if etype == SFG_EDGE_KIND.SYMBOL_IS_USED:
                            is_related = True

                    if is_related:
                        # 后向遍历仅关注 SYMBOL 和 STMT
                        if v.node_type in (SFG_NODE_KIND.SYMBOL, SFG_NODE_KIND.STMT):
                            visited.add(v)
                            worklist.append(v)
                        break
        return visited

    def print_and_write_flows(self, flows):
        print(f"Found {len(flows)} taint flows.")
        flow_json = []
        # 打印所有的污点流
        for each_flow in flows:
            source_stmt = self.loader.get_stmt_gir(each_flow.source_stmt_id)
            source_gir = get_gir_str(source_stmt)
            source_method_id = self.loader.convert_stmt_id_to_method_id(each_flow.source_stmt_id)
            source_method_name = self.loader.convert_method_id_to_method_name(source_method_id)

            sink_stmt = self.loader.get_stmt_gir(each_flow.sink_stmt_id)
            sink_gir = get_gir_str(sink_stmt)
            sink_line_no = int(sink_stmt.start_row)
            source_line_no = int(source_stmt.start_row)

            source_unit_id = self.loader.convert_stmt_id_to_unit_id(each_flow.source_stmt_id)
            source_file_path = self.loader.convert_unit_id_to_unit_path(source_unit_id)
            sink_unit_id = self.loader.convert_stmt_id_to_unit_id(each_flow.sink_stmt_id)
            sink_file_path = self.loader.convert_unit_id_to_unit_path(sink_unit_id)

            print(f"Found a flow to sink {sink_gir} on line {sink_line_no + 1}")
            print("\tSource :", source_gir, f"(in {source_method_name})")

            line_no = -1
            path_parent_source_node_list = []
            path_parent_source_file_node_list = []
            for node in reversed(each_flow.parent_to_source):
                stmt_id = node.def_stmt_id
                stmt = self.loader.get_stmt_gir(stmt_id)
                if stmt.start_row == line_no:
                    continue
                line_no = stmt.start_row
                gir_str = get_gir_str(stmt)

                method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
                method_name = self.loader.convert_method_id_to_method_name(method_id)
                path_node = "(" + gir_str + ")" + " on line " + str(int(line_no) + 1)
                unit_id = self.loader.convert_stmt_id_to_unit_id(stmt_id)
                file_path = self.loader.convert_unit_id_to_unit_path(unit_id)
                path_node_in_file = {
                    "start_line": int(stmt.start_row + 1),
                    "end_line": int(stmt.end_row + 1),
                    "file_path": file_path,
                    "gir": gir_str,
                    "stmt_id": stmt_id,
                }
                path_parent_source_node_list.append(path_node)
                path_parent_source_file_node_list.append(path_node_in_file)

            line_no = -1
            path_parent_sink_node_list = []
            path_parent_sink_file_node_list = []
            for node in each_flow.parent_to_sink:
                stmt_id = node.def_stmt_id
                stmt = self.loader.get_stmt_gir(stmt_id)
                if stmt.start_row == line_no:
                    continue
                line_no = stmt.start_row
                gir_str = get_gir_str(stmt)

                method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
                method_name = self.loader.convert_method_id_to_method_name(method_id)
                path_node = "(" + gir_str + ")" + " on line " + str(int(line_no) + 1)
                unit_id = self.loader.convert_stmt_id_to_unit_id(stmt_id)
                file_path = self.loader.convert_unit_id_to_unit_path(unit_id)
                path_node_in_file = {
                    "start_line": int(stmt.start_row + 1),
                    "end_line": int(stmt.end_row + 1),
                    "file_path": file_path,
                    "gir": gir_str,
                    "stmt_id": stmt_id,
                }
                path_parent_sink_node_list.append(path_node)
                path_parent_sink_file_node_list.append(path_node_in_file)

            if not self.is_sublist(path_parent_source_node_list, path_parent_sink_node_list):
                path_parent_sink_node_list = path_parent_source_node_list + path_parent_sink_node_list
            if not self.is_sublist(path_parent_source_file_node_list, path_parent_sink_file_node_list):
                path_parent_sink_file_node_list = path_parent_source_file_node_list + path_parent_sink_file_node_list
            print("\t\tData Flow:", path_parent_sink_node_list)

            flow_json.append({
                "source_stmt_id": each_flow.source_stmt_id,
                "sink_stmt_id": each_flow.sink_stmt_id,
                "source": source_gir,
                "sink": sink_gir,
                "source_line": source_line_no + 1,
                "sink_line": sink_line_no + 1,
                "source_file_path": source_file_path,
                "sink_file_path": sink_file_path,
                "data_flow": path_parent_sink_file_node_list,
            })

        output_dir = os.path.join(self.options.workspace, config.TAINT_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "taint_data_flow.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(flow_json, f, ensure_ascii=False, indent=2)
        print(f"Wrote taint data flows to {output_file}")

    def is_sublist(self, sub, lst):
        return str(sub)[1:-1] in str(lst)[1:-1]

    def run(self):
        if not self.options.quiet:
            print("\n########### # Phase IV: Taint Analysis # ##########")

        all_flows = []
        for method_id in self.loader.get_all_method_ids():
            self.current_entry_point = method_id
            self.sfg = self.loader.get_global_sfg_by_entry_point(method_id)
            self._update_sfg(self.sfg)
            if not self.sfg:
                continue
            self.taint_manager = TaintEnv()
            sources = self.find_sources()
            sinks = self.find_sinks()
            
            flows = self.find_flows(sources, sinks)
            all_flows.extend(flows)

        if len(all_flows) == 0:
            print("No taint flows found.")
        else:
            if not self.options.quiet:
                self.print_and_write_flows(all_flows)

