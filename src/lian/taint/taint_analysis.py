#! /usr/bin/env python3
import json
import os,sys
import re
from collections import deque

import yaml

import lian.config.config as config
import networkx as nx

from lian.util.loader import Loader
from lian.util import util
from lian.util.readable_gir import get_gir_str
from lian.taint.rule_manager import RuleManager
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

    def read_rules(self, operation, source_rules):
        """从src.yaml文件中获取field_read语句类型的规则, 并根据每条规则创建taint_bv"""
        rules = []

        for rule in source_rules:
            if rule.operation == operation:
                rules.append(rule)
        return rules

    def get_call_name_symbol_and_state(self, node):
        if node.node_type != SFG_NODE_KIND.STMT:
            return None, None
        state_nodes = []
        predecessors = list(util.graph_predecessors(self.sfg, node))
        name_symbol_node = None
        if len(predecessors) == 0 :
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
            edge = self.sfg.get_edge_data(node, successor)
            if edge and edge[0]['weight'].edge_type == SFG_EDGE_KIND.SYMBOL_STATE:
                define_state_list.append(successor)
        return define_symbol_node, define_state_list

    def find_sources(self):
        node_list = []
        # 应该包括所有的可能symbol和state节点作为sources
        # 这里应该应用source的规则
        # 遍历sfg
        for node in self.sfg.nodes:
            if node.node_type == SFG_NODE_KIND.STMT and node.name == "call_stmt":
                if self.apply_call_stmt_source_rules(node):
                    defined_symbol_node, defined_state_node = self.find_symbol_chain(self.sfg, node)
                    node_list.append( defined_symbol_node)
            if node.node_type == SFG_NODE_KIND.STMT and node.name == "parameter_decl":
                if self.apply_parameter_source_rules(node):
                    node_list.append(node)
            if node.node_type == SFG_NODE_KIND.STMT and node.name == "field_read":
                if self.apply_field_read_source_rules(node):
                    node_list.append(node)
            # 为了兼容codeql规则
            # elif node.node_type == SFG_NODE_KIND.STMT:
            #     rules = self.rule_manager.all_sources_from_code
            #     if self.apply_rules_from_code(node, rules):
            #         node_list.append(node)

        return node_list
    def apply_parameter_source_rules(self, node):
        stmt_id = node.def_stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)

        stmt = self.loader.get_stmt_gir(method_id)
        if not stmt.attrs:
            return False
        if not isinstance(stmt.attrs, str):
            return False
        attrs = stmt.attrs
        parameter_symbol = list(util.graph_successors(self.sfg, node))[0]
        for rule in self.rule_manager.all_sources:
            if not rule.attr and rule.name == parameter_symbol.name:
                return True
            if rule.operation != "parameter_decl":
                continue
            if rule.attr and rule.attr not in attrs:
                continue
            if rule.name == parameter_symbol.name:
                return True
        return False

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

    def next_by_edge_type(self, G, src, edge_type):
        """返回从 src 出发、第一条边数据['type']==edge_type 的目标节点；无则 None"""
        for _, v, data in G.out_edges(src, data=True):
            if data.get('weight').edge_type == edge_type:
                return v
        return None

    def find_symbol_chain(self, G, A):
        """
        A ->(symbol_defined)-> B ->(symbol_state)-> C
        返回 (B, C) 任一环节缺失返回 None
        """
        B = self.next_by_edge_type(G, A, SFG_EDGE_KIND.SYMBOL_IS_DEFINED)
        if B is None:
            return None
        C = self.next_by_edge_type(G, B, SFG_EDGE_KIND.SYMBOL_STATE)
        return (B, C) if C is not None else None

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

    def apply_field_read_source_rules(self, node):
        gir = node.operation
        target = gir.split('=')[1].replace(" ", "")
        for rule in self.rule_manager.all_sources:
            if rule.operation != "field_read":
                continue
            if target == rule.target:
                return True
        return False


    def apply_call_stmt_source_rules(self, node):
        stmt_id = node.def_stmt_id
        stmt = self.loader.get_stmt_gir(stmt_id)
        method_symbol_node, method_state_nodes = self.get_call_name_symbol_and_state(node)
        defined_symbol_node, defined_state_nodes = self.get_stmt_define_symbol_and_states_node(node)
        if not method_symbol_node or not defined_symbol_node:
            return False

        tag_space_id = defined_symbol_node.node_id
        apply_rule_flag = False
        for rule in self.rule_manager.all_sources:
            if rule.operation != "call_stmt":
                continue
            tag_info = rule
            name = tag_info.name
            for state_node in method_state_nodes:
                # state_index = state_node.index
                # if not self.space[state_index] or self.space[state_index].symbol_or_state == 0:
                #     continue
                state_access_path = state_node.access_path
                if isinstance(state_access_path, str):
                    continue
                access_path = self.access_path_formatter(state_access_path)

                if len(access_path) == 0:
                    access_path = stmt.name
                if access_path == name:
                    apply_rule_flag = True
                    tag = self.taint_manager.get_symbol_tag(tag_space_id)
                    # tag = in_taint.get(tag_space_id, 0)
                    new_tag = self.taint_manager.add_and_update_tag_bv(tag_info=tag_info, current_taint=tag)
                    # taint_status.out_taint[tag_space_id] = new_tag
                    self.taint_manager.set_symbols_tag([tag_space_id], new_tag)
                    for defined_state_node in defined_state_nodes:
                        self.taint_manager.set_states_tag([defined_state_node.node_id], new_tag)

        return apply_rule_flag

    def find_sinks(self, ):
        # 找到所有的sink函数或者语句
        # 这里应该应用sink的规则
        node_list = []
        for node in self.sfg.nodes:
            if self.should_apply_call_stmt_sink_rules(node) or self.should_apply_object_call_stmt_sink_rules(node):
                node_list.append(node)
            # 为了兼容codeql的规则
            # rules = self.rule_manager.all_sinks_from_code
            # if node.node_type == SFG_NODE_KIND.STMT and self.apply_rules_from_code(node, rules):
            #     node_list.append(node)
        return node_list
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
        method_symbol_node, method_state_nodes = self.get_call_name_symbol_and_state(node)

        for rule in self.rule_manager.all_sinks:
            # todo 当规则较长时，则应该切成数组，倒序与state_access_path匹配
            # rule_access_path = rule.name.split('.')
            for state_node in method_state_nodes:
                # 检查函数名是否符合规则
                if self.check_method_name(rule.name, state_node):
                    return True
                    return self.check_tag(rule.target, used_symbols, self.taint_manager)
                    # 检查参数是否携带tag

        return False

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

    # def check_tag(self, rule_tag, used_symbols, taint_state_manager):
    #     # 暂时检测taint_env中的tag,且只考虑positional_args
    #     if len(rule_tag) == 0:
    #         return False
    #     for target_arg in rule_tag:
    #
    #         arg_index = int(target_arg[-1])
    #         if arg_index + 1 >= len(used_symbols):
    #             continue
    #         arg_symbol = self.space[used_symbols[arg_index + 1]]
    #         arg_states = arg_symbol.states
    #
    #         for state_index in arg_states:
    #             return self.check_state_tag(state_index, taint_state_manager)
    #     return False

    # def check_state_tag(self, state_index, taint_state_manager):
    #     if self.space[state_index].symbol_or_state == 0:
    #         return False
    #     state_id = self.space[state_index].state_id
    #     access_path_tag = config.NO_TAINT
    #     # if space[state_index].access_path:
    #     #     access_path = self.access_path_formatter(space[state_index].access_path)
    #     #     access_path_tag = taint_state_manager.get_access_path_tag_in_sink(access_path)
    #
    #     tag = self.taint_manager.get_state_tag(state_id)
    #     if tag != config.NO_TAINT :
    #         # 报告sink
    #         #print(space[state_index])
    #         #print(f"sink in {space[state_index].stmt_id}, tag: {tag}")
    #         return True
    #     # if access_path_tag != config.NO_TAINT:
    #     #     # 报告sink
    #     #     print(f"access_path sink in {space[state_index].stmt_id}, tag: {access_path_tag}")
    #     #     return True
    #     #print(space[state_index].fields)
    #     for value in self.space[state_index].fields.values():
    #         for field_state_index in value:
    #             return self.check_state_tag(field_state_index, taint_state_manager)
    #     return False

    def find_flows(self, sources, sinks):
        # 找到所有的taint flow
        # 这里需要应用图遍历算法对taint进行传播
        # 这里需要把taint管理器用起来，对symbol和state层面有污点的节点进行标记
        flow_list = []
        for source in sources:
            for sink in sinks:
                source_method_id = self.loader.convert_stmt_id_to_method_id(source.def_stmt_id)
                sink_method_id = self.loader.convert_stmt_id_to_method_id(sink.def_stmt_id)

                # 这里只需要method_id
                parent_method = self.loader.get_lowest_common_ancestor_in_call_path_p3(source_method_id, sink_method_id, self.current_entry_point)
                flow_list.extend(self.find_source_to_sink_path( source, sink, [parent_method]))

        return flow_list

    def find_source_to_sink_path(self, source, sink, parents):

        def nearest_attr_ancestor(G, node, val):
            """
            返回 (祖先节点, 最短距离) 其中祖先的 G.nodes[ancestor][attr] == val；
            若无满足条件的祖先，返回 (None, -1)。
            """
            if node not in G:
                return None, -1

            queue = deque([(node, 0)])  # (当前节点, 距离)
            seen = {node}

            while queue:
                cur, dist = queue.popleft()

                # 看父节点
                for p in G.predecessors(cur):
                    if p in seen:
                        continue
                    seen.add(p)

                    # 满足属性即返回
                    method_id = self.loader.convert_stmt_id_to_method_id(p.def_stmt_id)
                    if method_id == val and p.node_type != SFG_NODE_KIND.STATE:
                        return p, dist + 1

                    queue.append((p, dist + 1))

            return None, -1

        def shortest_paths_to_targets(G, start, targets):
            """
            在无权有向图里，从 start 做一次 BFS，直到找到所有 targets（或遍历完可达子图）。
            只返回 targets 中能到达的节点的最短路径（包含起止点）。
            """
            if start not in G:
                return {}
            if not targets:
                return {}

            remaining = set(targets)
            paths = {}

            # start 本身就是目标
            if start in remaining:
                paths[start] = [start]
                remaining.remove(start)
                if not remaining:
                    return paths

            pred = {start: None}
            q = deque([start])

            while q and remaining:
                cur = q.popleft()
                
                # 默认只寻找有向图的继承者节点
                neighbors = set(G.successors(cur))
                
                # 针对 %this 节点的特殊处理：将 symbol_state 边视为无向边（即允许回溯前驱节点）
                for p_node in G.predecessors(cur):
                    if cur.name == "%this" or p_node.name == "%this":
                        edge_data = G.get_edge_data(p_node, cur)
                        if edge_data:
                            for data in edge_data.values():
                                sfg_edge = data.get('weight')
                                if sfg_edge and getattr(sfg_edge, 'name', '') == "symbol_state":
                                    neighbors.add(p_node)
                                    break

                for nxt in neighbors:
                    if nxt in pred:
                        continue
                    pred[nxt] = cur

                    if nxt in remaining:
                        # reconstruct path start -> nxt
                        rev = [nxt]
                        p = cur
                        while p is not None:
                            rev.append(p)
                            p = pred[p]
                        paths[nxt] = list(reversed(rev))
                        remaining.remove(nxt)
                        if not remaining:
                            break

                    q.append(nxt)

            return paths

        flow_list = []
        for parent in parents:
            sfg_node, dist = nearest_attr_ancestor(self.sfg, source, parent)
            if not sfg_node:
                sfg_node = source

            found_paths = shortest_paths_to_targets(self.sfg, sfg_node, {source, sink})
            parent_to_source = found_paths.get(source)
            parent_to_sink = found_paths.get(sink)
            if not parent_to_source or not parent_to_sink:
                continue
            new_flow = Flow()
            new_flow.source_stmt_id = source.def_stmt_id
            new_flow.sink_stmt_id = sink.def_stmt_id
            new_flow.parent_to_source = parent_to_source
            new_flow.parent_to_sink = parent_to_sink
            flow_list.append(new_flow)
            #print(parent_to_source)
            #print(parent_to_sink)
        return flow_list

    # def find_method_parent_by_nodes(self, source_nodes, sink_nodes):
    #     if not sink_nodes or len(sink_nodes) == 0:
    #         return []
    #     if not source_nodes or len(source_nodes) == 0:
    #         return []
    #     parents = []
    #     for source_node in source_nodes:
    #         for sink_node in sink_nodes:
    #             parent = self.find_method_parent_by_node(ct, source_node, sink_node)
    #             if source_node == sink_node:
    #                 parent = source_node
    #             if not parent:
    #                 continue
    #             parents.append(parent.split("#")[-1])
    #     return parents
    #
    # def find_method_parent_by_node(self, sfg, node1, node2):
    #
    #     if node1 not in sfg or node2 not in sfg:
    #         return None
    #
    #
    #     reversed_tree = sfg.reverse()
    #
    #     roots = [n for n, d in reversed_tree.out_degree() if d == 0]
    #
    #     def root_path(node):
    #         if node in roots:  # 自己就是根
    #             return [node]
    #         # 任取一条到根的最短路径即可
    #         for r in roots:
    #             if nx.has_path(reversed_tree, node, r):
    #                 return nx.shortest_path(reversed_tree, node, r)
    #         return [node]  # 孤立节点
    #
    #     path_u = root_path(node1)
    #     path_v = root_path(node2)
    #
    #     lca = None
    #     for p, q in zip(reversed(path_u), reversed(path_v)):
    #         if p == q:
    #             lca = p
    #         else:
    #             break
    #
    #     return lca

    def add_flows_to_json(self, raw_flows):
        flow_json = []
        for each_flow in raw_flows:
            flow_dict = {
                "source_stmt_id": each_flow.source_stmt_id,
                "sink_stmt_id": each_flow.sink_stmt_id,
                "source_code": self.loader.get_stmt_source_code_with_comment(each_flow.source_stmt_id)[0].strip(),
                "sink_code": self.loader.get_stmt_source_code_with_comment(each_flow.sink_stmt_id)[0].strip(),
                "parent_to_source": [],
                "parent_to_sink": []
            }

            # parent_to_source
            last_line = -1
            for node in each_flow.parent_to_source:
                stmt_id = node.def_stmt_id
                stmt = self.loader.get_stmt_gir(stmt_id)
                if stmt.start_row == last_line:
                    continue
                last_line = stmt.start_row
                code = self.loader.get_stmt_source_code_with_comment(stmt_id)[0].strip()
                method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
                method_name = self.loader.convert_method_id_to_method_name(method_id)
                flow_dict["parent_to_source"].append({
                    "code": code,
                    "method": method_name,
                    "line": int(stmt.start_row) + 1
                })

            # parent_to_sink
            last_line = -1
            for node in each_flow.parent_to_sink:
                stmt_id = node.def_stmt_id
                stmt = self.loader.get_stmt_gir(stmt_id)
                if stmt.start_row == last_line:
                    continue
                last_line = stmt.start_row
                code = self.loader.get_stmt_source_code_with_comment(stmt_id)[0].strip()
                method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
                method_name = self.loader.convert_method_id_to_method_name(method_id)
                flow_dict["parent_to_sink"].append({
                    "code": code,
                    "method": method_name,
                    "line": int(stmt.start_row) + 1
                })

            flow_json.append(flow_dict)
        return flow_json

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
                path_node = "(" + gir_str + ")"+ " on line " + str(int(line_no) + 1)
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
                path_node = "(" + gir_str + ")"+ " on line " + str(int(line_no) + 1)
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

    def write_taint_flows(self, flows):
        yaml_list = []
        flow_id = "f1"
        for flow in flows:
            source_stmt_id = flow.source_stmt_id
            sink_stmt_id = flow.sink_stmt_id
            source_method_id = self.loader.convert_stmt_id_to_method_id(source_stmt_id)
            sink_method_id = self.loader.convert_stmt_id_to_method_id(sink_stmt_id)
            parent_method = self.loader.get_lowest_common_ancestor_in_call_path_p3(
                source_method_id, sink_method_id, self.current_entry_point
            )

            call_path = []

            if parent_method != source_method_id:
                call_path = self.loader.get_call_path_between_two_methods_in_p3(parent_method, source_method_id)[0]
            if parent_method != sink_method_id:
                call_path = self.loader.get_call_path_between_two_methods_in_p3(parent_method, sink_method_id)[0]
            call_path.append(CallSite(sink_method_id, sink_stmt_id, -1))
            current_flow = {
                "id":flow_id,
                "flow":[],
            }
            prefix, number = re.match(r"([a-zA-Z]+)(\d+)", flow_id).groups()
            flow_id = f"{prefix}{int(number) + 1}"
            previous_call_site = call_path[0]
            for call_site in call_path[1:]:
                stmt_id = call_site.call_stmt_id
                stmt = self.loader.get_stmt_gir(stmt_id)
                unit_id = self.loader.convert_stmt_id_to_unit_id(stmt_id)
                file_path = self.loader.convert_unit_id_to_unit_path(unit_id)
                method_decl_stmt = self.loader.get_stmt_gir(call_site.caller_id)
                method_signature = get_gir_str(method_decl_stmt)
                start_line = method_decl_stmt.start_row + 1
                end_line = method_decl_stmt.end_row + 1
                code = get_gir_str(stmt)
                role = "propagation"
                call_line = stmt.start_row + 1
                for site in call_path:
                    if site.callee_id == call_site.caller_id:
                        previous_call_site = site
                # taint = self.determine_taint(previous_call_site, call_site, flow)
                if call_site.caller_id == source_method_id:
                    taint = -1
                    source_stmt = self.loader.get_stmt_gir(source_stmt_id)
                    code = get_gir_str(source_stmt)
                    role = "source"
                elif call_site.caller_id == sink_method_id and call_site.call_stmt_id == sink_stmt_id:
                    sink_stmt = self.loader.get_stmt_gir(sink_stmt_id)
                    code = get_gir_str(sink_stmt)
                    role = "sink"

                previous_call_site = call_site
                flow_dict = {
                    "file_path": file_path,
                    "method_name": method_signature,
                    "method_startline": start_line,
                    "method_endline": end_line,
                    "call_line": call_line,
                    "code": code,
                    "role": role,
                }
                current_flow["flow"].append(flow_dict)
            yaml_list.append(current_flow)
        output_file = os.path.join(self.options.workspace, config.TAINT_OUTPUT_DIR, config.TAINT_FILE_NAME)
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_list, f, sort_keys=False, allow_unicode=True)

    # def determine_taint(self, previous_call_site, current_call_site, flow):
    #     context_key = hash(previous_call_site) if previous_call_site else 0
    #     status = self.loader.get_stmt_status_p3(context_key)[current_call_site.call_stmt_id]
    #     index = 0
    #     for used_symbol_index in status.used_symbols:
    #         if index == 0:
    #             index += 1
    #             continue
    #         symbol = self.space[used_symbol_index]
    #         for state_index in symbol.states:
    #             state = self.space[state_index]
    #             if self.state_is_in_flow(state.state_id, flow):
    #                 return index
    #     return -1

    # def state_is_in_flow(self, state_id, flow):
    #     for node in flow.parent_to_source:
    #         if node.node_type == SFG_NODE_KIND.STATE and node.node_id == state_id:
    #             return True
    #     for node in flow.parent_to_sink:
    #         if node.node_type == SFG_NODE_KIND.STATE and node.node_id == state_id:
    #             return True
    #     return False

    def run(self):
        if not self.options.quiet:
            print("\n########### # Phase IV: Taint Analysis # ##########")

        all_flows = []
        for method_id in self.loader.get_all_method_ids():
            self.current_entry_point = method_id
            self.sfg = self.loader.get_global_sfg_by_entry_point(method_id)
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
            # self.write_taint_flows(all_flows)

