#! /usr/bin/env python3
import os,sys
from collections import deque
import lian.config.config as config
import networkx as nx
# sys.path.extend([config.LIAN_DIR])

# from lian.main import Lian
from lian.util.loader import Loader
from lian.util import util
from lian.taint.rule_manager import RuleManager
from lian.common_structs import (
    APath,
    SimpleWorkList,
    State,
    Symbol,
    ComputeFrameStack,
    SymbolStateSpace,
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
            elif node.node_type == SFG_NODE_KIND.STMT:
                rules = self.rule_manager.all_sources_from_code
                if self.apply_rules_from_code(node, rules):
                    node_list.append(node)

        return node_list

    def apply_rules_from_code(self, node, rules):
        stmt_id = node.def_stmt_id
        space = self.loader.get_symbol_state_space_p3(0)
        status = self.loader.get_stmt_status_p3(node.context)[stmt_id]
        stmt = self.loader.convert_stmt_id_to_stmt(stmt_id)
        for rule in rules:

            if str(stmt.start_row) != rule.line_num:
                continue

            symbol_in_stmt = False
            if space[status.defined_symbol].name == rule.symbol_name:
                symbol_in_stmt = True
            for symbol_index in status.used_symbols:
                symbol = space[symbol_index]
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

    def apply_call_stmt_source_rules(self, node):
        stmt_id = node.def_stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
        space = self.loader.get_symbol_state_space_p3(0)
        status = self.loader.get_stmt_status_p3(node.context)[stmt_id]
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
            rules = self.rule_manager.all_sinks_from_code
            if node.node_type == SFG_NODE_KIND.STMT and self.apply_rules_from_code(node, rules):
                node_list.append(node)
        return node_list

    def should_apply_call_stmt_sink_rules(self, node):
        if node.node_type != SFG_NODE_KIND.STMT or node.name != "call_stmt":
            return False
        stmt_id = node.def_stmt_id
        method_id = self.loader.convert_stmt_id_to_method_id(stmt_id)
        space = self.loader.get_symbol_state_space_p3(0)
        status = self.loader.get_stmt_status_p3(node.context)[stmt_id]
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
                    return self.check_tag(rule.target, used_symbols, space, self.taint_manager)
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

    def check_tag(self, rule_tag, used_symbols, space, taint_state_manager):
        # 暂时检测taint_env中的tag,且只考虑positional_args
        if len(rule_tag) == 0:
            return False
        for target_arg in rule_tag:

            arg_index = int(target_arg[-1])
            if arg_index + 1 >= len(used_symbols):
                continue
            arg_symbol = space[used_symbols[arg_index + 1]]
            arg_states = arg_symbol.states

            for state_index in arg_states:
                return self.check_state_tag(state_index, space, taint_state_manager)
        return False

    def check_state_tag(self, state_index, space, taint_state_manager):
        if space[state_index].symbol_or_state == 0:
            return False
        state_id = space[state_index].state_id
        access_path_tag = config.NO_TAINT
        # if space[state_index].access_path:
        #     access_path = self.access_path_formatter(space[state_index].access_path)
        #     access_path_tag = taint_state_manager.get_access_path_tag_in_sink(access_path)

        tag = self.taint_manager.get_state_tag(state_id)
        if tag != config.NO_TAINT :
            # 报告sink
            #print(space[state_index])
            #print(f"sink in {space[state_index].stmt_id}, tag: {tag}")
            return True
        # if access_path_tag != config.NO_TAINT:
        #     # 报告sink
        #     print(f"access_path sink in {space[state_index].stmt_id}, tag: {access_path_tag}")
        #     return True
        #print(space[state_index].fields)
        for value in space[state_index].fields.values():
            for field_state_index in value:
                return self.check_state_tag(field_state_index, space, taint_state_manager)
        return False

    def is_specified_method(self, method_id, node):
        if method_id == node.split("#")[-1]:
            return True
        return False

    def find_flows(self, sfg, ct, sources, sinks):
        # 找到所有的taint flow
        # 这里需要应用图遍历算法对taint进行传播
        # 这里需要把taint管理器用起来，对symbol和state层面有污点的节点进行标记
        flow_list = []
        for source in sources:
            for sink in sinks:
                source_method_id = self.loader.convert_stmt_id_to_method_id(source.def_stmt_id)
                sink_method_id = self.loader.convert_stmt_id_to_method_id(sink.def_stmt_id)
                source_method_nodes = []
                sink_method_nodes = []
                for node in ct.nodes:
                    if self.is_specified_method(str(source_method_id), node):
                        source_method_nodes.append(node)
                    if self.is_specified_method(str(sink_method_id), node):
                        sink_method_nodes.append(node)
                # 这里只需要method_id
                parent_methods = self.find_method_parent_by_nodes(ct, source_method_nodes, sink_method_nodes)
                flow_list.extend(self.find_source_to_sink_path(sfg, source, sink, parent_methods))

        return flow_list

    def find_source_to_sink_path(self, sfg, source, sink, parents):

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
                    if str(method_id) == val:
                        return p, dist + 1

                    queue.append((p, dist + 1))

            return None, -1

        flow_list = []
        for parent in parents:
            sfgnode, dist = nearest_attr_ancestor(sfg, source, parent)
            if not sfgnode:
                continue
            try:
                parent_to_source = nx.shortest_path(sfg, sfgnode, source)
            except nx.NetworkXNoPath:
                parent_to_source = None
            try:
                parent_to_sink = nx.shortest_path(sfg, sfgnode, sink)
            except nx.NetworkXNoPath:
                parent_to_sink = None
            if not parent_to_source or not parent_to_sink:
                continue
            new_flow = Flow()
            new_flow.parent_to_source = parent_to_source
            new_flow.parent_to_sink = parent_to_sink
            flow_list.append(new_flow)
            #print(parent_to_source)
            #print(parent_to_sink)


        return flow_list

    def find_method_parent_by_nodes(self, ct, source_nodes, sink_nodes):
        if not sink_nodes or len(sink_nodes) == 0:
            return []
        if not source_nodes or len(source_nodes) == 0:
            return []
        parents = []
        for source_node in source_nodes:
            for sink_node in sink_nodes:
                parent = self.find_method_parent_by_node(ct, source_node, sink_node)
                if source_node == sink_node:
                    parent = source_node
                if not parent:
                    continue
                parents.append(parent.split("#")[-1])
        return parents

    def find_method_parent_by_node(self, sfg, node1, node2):

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
        for p, q in zip(reversed(path_u), reversed(path_v)):
            if p == q:
                lca = p
            else:
                break

        return lca

    def run(self):
        if not self.options.quiet:
            print("\n########### # Phase IV: Taint Analysis # ##########")

        for method_id in self.loader.get_all_method_ids():
            call_tree = self.loader.get_global_call_tree_by_entry_point(method_id)
            sfg = self.loader.get_global_sfg_by_entry_point(method_id)
            if not sfg:
                continue
            self.taint_manager = TaintEnv()
            sources = self.find_sources(sfg, call_tree)
            sinks = self.find_sinks(sfg, call_tree)
            flows = self.find_flows(sfg, call_tree, sources, sinks)

            if self.options.debug:
                # gl:麻烦进行美化
                self.print_flows(flows)

    def print_flows(self, flows):
        for flow in flows:
            print("--------------------------------")
            for node in flow.parent_to_sink:
                stmt_id = node.def_stmt_id
                stmt = self.loader.get_stmt_gir(stmt_id)
                line_no = stmt.start_row
                print(node,"in line ", line_no)

def main():
    TaintAnalysis().run()

if __name__ == "__main__":
    main()
