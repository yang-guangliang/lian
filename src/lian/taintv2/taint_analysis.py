#! /usr/bin/env python3
import os,sys
from types import SimpleNamespace
import config1 as config
print(config.LIAN_DIR)
sys.path.extend([config.LIAN_DIR])


from lian.main import Lian
from lian.util.loader import Loader
from lian.util import util
from lian.config.constants import (

)

from lian.common_structs import (
    APath,
    SimpleWorkList,
    State,
    Symbol,
    ComputeFrameStack,
    SymbolStateSpace,
)

from constants import (
    SFG_NODE_KIND,
    SFG_EDGE_KIND
)

from taint_structs import TaintEnv
from rule_manager import RuleManager

class TaintAnalysis:
    def __init__(self):
        self.lian = None
        self.loader = None
        self.taint_manager = None
        self.rule_manager = RuleManager()

    def read_rules(self, operation, source_rules):
        """从src.yaml文件中获取field_read语句类型的规则, 并根据每条规则创建taint_bv"""
        rules = []

        for rule in source_rules:
            if rule.operation == operation:
                rules.append(rule)
        return rules

    def find_sources(self, sfg, ct):
        node_list = []
        # 应该包括所有的可能symbol和state节点作为sources
        # 这里应该应用source的规则
        # 遍历sfg
        for node in sfg.nodes:
            if node.node_type == SFG_NODE_KIND.STMT and node.name == "call_stmt":
                self.apply_call_stmt_source_rules(node)
            print(node)
            print(type(node))
        return node_list

    def apply_call_stmt_source_rules(self, node):
        stmt_id = node.stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
        space = self.loader.get_symbol_state_space_p2(method_id)
        status = self.loader.get_stmt_status_p2(method_id)[stmt_id]
        stmt = self.loader.convert_stmt_id_to_stmt(stmt_id)
        method_symbol = space[status.used_symbols[0]]
        tag_space_id = space[status.defined_symbol].symbol_id
        method_states = method_symbol.states

        for rule in self.rule_manager.all_sources:
            if rule.operation != "call_stmt":
                continue
            tag_info = rule
            name = tag_info.name
            for state_index in method_states:
                if not space[state_index] or space[state_index].symbol_or_state == 0:
                    continue
                state_access_path = space[state_index].access_path
                if isinstance(state_access_path, str):
                    continue
                access_path = util.access_path_formatter(state_access_path)

                if len(access_path) == 0:
                    access_path = stmt.name
                if access_path == name:
                    tag = self.taint_manager.get_symbol_tag(tag_space_id)
                    # tag = in_taint.get(tag_space_id, 0)
                    new_tag = self.taint_manager.add_and_update_tag_bv(tag_info=tag_info, current_taint=tag)
                    taint_status.out_taint[tag_space_id] = new_tag





    def find_sinks(self, sfg, ct):
        # 找到所有的sink函数或者语句
        # 这里应该应用sink的规则
        node_list = []

        return node_list

    def apply_call_stmt_sink_rules(self, rules, taint_status, frame, space, taint_state_manager):
        status = frame.stmt_id_to_status[self.stmt_id]
        method_symbol = space[status.used_symbols[0]]
        used_symbols = status.used_symbols
        method_index = used_symbols[0]
        method_symbol = space[method_index]

        for rule in rules:
            # todo 当规则较长时，则应该切成数组，倒序与state_access_path匹配
            # rule_access_path = rule.name.split('.')
            for state in method_symbol.states:
                # 检查函数名是否符合规则
                if self.check_method_name(rule.name, state, space):
                    # 检查参数是否携带tag
                    self.check_tag(rule.target, used_symbols, space, taint_state_manager)

    def check_method_name(self, rule_name, method_state, space):
        apply_flag = True
        if not isinstance(space[method_state], State):
            return False

        state_access_path = space[method_state].access_path
        access_path = util.access_path_formatter(state_access_path)
        access_path = access_path.split('.')
        rule_name = rule_name.split('.')
        if len(access_path) < len(rule_name):
            return False
        # name匹配上
        for i, item in enumerate(reversed(rule_name)):
            if item == TAG_KEYWORD.ANYNAME:
                continue
            if item != access_path[-i - 1]:
                apply_flag = False
                break

        return apply_flag

    def find_flows(self, sfg, ct, sources, sinks):
        # 找到所有的taint flow
        # 这里需要应用图遍历算法对taint进行传播
        # 这里需要把taint管理器用起来，对symbol和state层面有污点的节点进行标记
        flow_list = []
        for source in sources:
            for sink in sinks:
                if sfg.has_edge(source, sink):
                    flow_list.append((source, sink))
        return flow_list

    def run(self):

        self.lian = Lian().run()
        self.loader = self.lian.loader

        for method_id in self.loader.get_all_method_ids():
            call_tree = self.loader.get_global_call_tree_by_entry_point(method_id)
            sfg = self.loader.get_method_sfg(method_id)
            self.taint_manager = TaintEnv()
            for node in sfg.nodes:
                print(node)
            sources = self.find_sources(sfg, call_tree)
            sinks = self.find_sinks(sfg, call_tree)
            flows = self.find_flows(sfg, call_tree, sources, sinks)

def main():
    TaintAnalysis().run()

if __name__ == "__main__":
    main()
