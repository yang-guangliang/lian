#! /usr/bin/env python3
import os,sys
from types import SimpleNamespace
import config1 as config
import networkx as nx
sys.path.extend([config.LIAN_DIR])


from lian.main import Lian
from lian.util.loader import Loader
from lian.util import util
from lian.config.constants import (
    SFG_EDGE_KIND,
    SFG_NODE_KIND,
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
    SFG_EDGE_KIND,
    TAG_KEYWORD
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
                if self.apply_call_stmt_source_rules(node):
                    defined_symbol_node, defined_state_node = self.find_symbol_chain(sfg, node)
                    node_list.append(defined_state_node)

        return node_list

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

    def apply_call_stmt_source_rules(self, node):
        stmt_id = node.def_stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
        space = self.loader.get_symbol_state_space_p2(method_id)
        status = self.loader.get_stmt_status_p2(method_id)[stmt_id]
        stmt = self.loader.convert_stmt_id_to_stmt(stmt_id)
        method_symbol = space[status.used_symbols[0]]
        tag_space_id = space[status.defined_symbol].symbol_id
        method_states = method_symbol.states
        defined_symbol = space[status.defined_symbol]
        apply_rule_flag = False
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
                    for state_index in defined_symbol.states:
                        if state:= space[state_index] :
                            if isinstance(state, State):
                                self.taint_manager.set_states_tag([state.state_id], new_tag)

        return apply_rule_flag

    def find_sinks(self, sfg, ct):
        # 找到所有的sink函数或者语句
        # 这里应该应用sink的规则
        node_list = []
        for node in sfg.nodes:
            if self.should_apply_call_stmt_sink_rules(node):
                node_list.append(node)
        return node_list

    def should_apply_call_stmt_sink_rules(self, node):
        if node.node_type != SFG_NODE_KIND.STMT or node.name != "call_stmt":
            return False
        stmt_id = node.def_stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
        space = self.loader.get_symbol_state_space_p2(method_id)
        status = self.loader.get_stmt_status_p2(method_id)[stmt_id]
        stmt = self.loader.convert_stmt_id_to_stmt(stmt_id)

        method_symbol = space[status.used_symbols[0]]
        used_symbols = status.used_symbols
        method_index = used_symbols[0]
        method_symbol = space[method_index]

        for rule in self.rule_manager.all_sinks:
            # todo 当规则较长时，则应该切成数组，倒序与state_access_path匹配
            # rule_access_path = rule.name.split('.')
            for state in method_symbol.states:
                # 检查函数名是否符合规则
                if self.check_method_name(rule.name, state, space):
                    return True
                    # 检查参数是否携带tag

        return False

    def check_method_name(self, rule_name, method_state, space):
        apply_flag = True
        if not isinstance(space[method_state], State):
            return False

        state_access_path = space[method_state].access_path
        access_path = self.access_path_formatter(state_access_path)
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
                print(666666666666666)
                print(self.find_path(sfg, source, sink))
                # if self.find_method_parent_by_id(sfg, source, sink):
                #     print(self.find_method_parent_by_id(sfg, source, sink))
        return flow_list
    def find_path(self, sfg, source, sink):
        U = sfg.to_undirected()  # 1. 无向化
        paths = nx.all_simple_paths(U, source, sink)  # 2. 枚举简单路径
        return max(paths, key=len, default=[])


    def find_method_parent_by_id(self, sfg, node1, node2):

        if node1 not in sfg or node2 not in sfg:
            return None


        reversed_tree = sfg.reverse()

        roots = [n for n, d in reversed_tree.out_degree() if d == 0]

        def root_path(node):
            if node in roots:  # 自己就是根
                return [node]
            # 任取一条到根的最短路径即可
            for r in roots:
                if nx.has_path(reversed_tree, node, r):
                    return nx.shortest_path(reversed_tree, node, r)
            return [node]  # 孤立节点

        path_u = root_path(node1)
        path_v = root_path(node2)


        lca = None
        print(path_u)
        print(path_v)
        for p, q in zip(reversed(path_u), reversed(path_v)):
            if p == q:
                lca = p
            else:
                break
        print(node1)
        print(node2)
        print(lca)
        print(nx.shortest_path(reversed_tree, lca, node1))
        print(nx.shortest_path(reversed_tree, lca, node2))

        return lca

    def run(self):

        self.lian = Lian().run()
        self.loader = self.lian.loader

        for method_id in self.loader.get_all_method_ids():
            call_tree = self.loader.get_global_call_tree_by_entry_point(method_id)
            sfg = self.loader.get_global_sfg_by_entry_point(method_id)
            if not sfg:
                continue
            self.taint_manager = TaintEnv()
            sources = self.find_sources(sfg, call_tree)
            sinks = self.find_sinks(sfg, call_tree)
            flows = self.find_flows(sfg, call_tree, sources, sinks)
            print(flows)

def main():
    TaintAnalysis().run()

if __name__ == "__main__":
    main()
