#!/usr/bin/env python3

import os,sys
import pprint
import copy
from os.path import commonprefix

import networkx as nx
from lian.core.prelim_semantics import PrelimSemanticAnalysis
from lian.util import util
from lian.config import config
import lian.util.data_model as dm
from lian.config.constants import (
    LIAN_INTERNAL,
    STATE_TYPE_KIND,
    SYMBOL_DEPENDENCY_GRAPH_EDGE_KIND,
    SYMBOL_OR_STATE,
    ANALYSIS_PHASE_ID,
    CALL_OPERATION,
    SENSITIVE_OPERATIONS
)
from lian.common_structs import (
    MetaComputeFrame,
    P2ResultFlag,
    Symbol,
    State,
    ComputeFrame,
    ComputeFrameStack,
    SimpleWorkList,
    SummaryData,
    InterruptionData,
    MethodSummaryTemplate,
    SymbolDefNode,
    SymbolStateSpace,
    BasicCallGraph,
    CallGraph,
    PathManager,
    IndexMapInSummary,
    StateDefNode,
    MethodSummaryInstance,
    APath,
    StmtStatus,
    StateFlowGraph,
    CallTree,
)
from lian.basics.entry_points import EntryPointGenerator
from lian.basics.control_flow import ControlFlowAnalysis
from lian.basics.stmt_def_use_analysis import StmtDefUseAnalysis
from lian.core.stmt_states import StmtStates
from lian.core.prelim_semantics import PrelimSemanticAnalysis
from lian.util.loader import Loader
from lian.core.resolver import Resolver
from lian.core.global_stmt_states import GlobalStmtStates
from networkx.generators.classic import complete_graph


class GlobalSemanticAnalysis(PrelimSemanticAnalysis):
    def __init__(self, lian, analyzed_method_list):
        super().__init__(lian)
        self.path_manager = PathManager()
        self.analyzed_method_list = analyzed_method_list
        self.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        self.caller_unknown_callee_edge = {}

    def get_stmt_id_to_callee_info(self, callees):
        results = {}
        for each_callee in callees:
            results[each_callee.stmt_id] = each_callee
        return results

    def adjust_index_of_status_space(self, baseline_index, status, frame, space, defined_symbols, symbol_bit_vector, state_bit_vector, method_summary_template):
        for IndexMapInSummarySet in method_summary_template.used_external_symbols.values():
            for symbol in IndexMapInSummarySet:
                symbol.raw_index += baseline_index

        for symbol_def_nodes in symbol_bit_vector.bit_pos_to_id.values():
            symbol_def_nodes.index += baseline_index

        for state_def_nodes in state_bit_vector.bit_pos_to_id.values():
            state_def_nodes.index += baseline_index
        # for symbol_def_nodes in defined_symbols.values():
        #     for node in symbol_def_nodes:
        #         node.index += baseline_index
        for stmt_status in status.values():
            for each_id, value in enumerate(stmt_status.used_symbols):
                if value != -1:
                    stmt_status.used_symbols[each_id] = value + baseline_index
            for each_id, value in enumerate(stmt_status.implicitly_used_symbols):
                if value != -1:
                    stmt_status.implicitly_used_states[each_id] = value + baseline_index
            for each_id, value in enumerate(stmt_status.implicitly_defined_symbols):
                stmt_status.implicitly_defined_symbols[each_id] = value + baseline_index
            stmt_status.defined_symbol += baseline_index
        for each_space in space:
            # each_space.index += baseline_index
            a = 1
            if isinstance(each_space, Symbol):
                new_set = set()
                for each_id in each_space.states:
                    new_set.add(each_id + baseline_index)
                each_space.states = new_set
            else:
                for each_id, each_status in enumerate(each_space.array):
                    new_set = set()
                    for index in each_status:
                        new_set.add(index + baseline_index)
                    each_space.array[each_id] = new_set
                for each_field, value_set in each_space.fields.items():
                    new_set = set()
                    for index in value_set:
                        new_set.add(index + baseline_index)
                    each_space.fields[each_field] = new_set
            each_space.call_site = frame.path[-3:]

    def init_compute_frame(self, frame: ComputeFrame, frame_stack: ComputeFrameStack, global_space):
        frame.has_been_inited = True
        frame.frame_stack = frame_stack
        method_id = frame.method_id

        frame.cfg = self.loader.get_method_cfg(method_id)
        if util.is_empty(frame.cfg):
            return

        if util.is_empty(self.loader.get_symbol_state_space_p1(method_id)):
            return

        frame.stmt_state_analysis = GlobalStmtStates(
            analysis_phase_id = self.analysis_phase_id,
            event_manager = self.event_manager,
            loader = self.loader,
            resolver = self.resolver,
            compute_frame = frame,
            path_manager = self.path_manager,
            analyzed_method_list = self.analyzed_method_list,
            caller_unknown_callee_edge = self.caller_unknown_callee_edge,
            complete_graph=self.options.complete_graph,
        )

        round_number = config.FIRST_ROUND
        if method_id in self.analyzed_method_list:
            round_number = config.SECOND_ROUND
        _, parameter_decls, method_body = self.loader.get_splitted_method_gir(method_id)
        if util.is_available(parameter_decls):
            for row in parameter_decls:
                frame.stmt_id_to_stmt[row.stmt_id] = row
                frame.stmt_counters[row.stmt_id] = round_number
        if util.is_available(method_body):
            for row in method_body:
                frame.stmt_id_to_stmt[row.stmt_id] = row
                frame.stmt_counters[row.stmt_id] = round_number

        if self.loader.get_method_defined_symbols_p2(method_id):
            frame.defined_symbols = self.loader.get_method_defined_symbols_p2(method_id).copy()

        all_defs = set()
        for stmt_id in frame.defined_symbols:
            symbol_def_set = frame.defined_symbols[stmt_id]
            for symbol_def in symbol_def_set:
                all_defs.add(symbol_def)
        frame.all_defs = all_defs

        if self.loader.get_method_defined_states_p2(method_id):
            frame.defined_states = self.loader.get_method_defined_states_p2(method_id).copy()

        frame.stmt_worklist = SimpleWorkList(graph = frame.cfg)
        frame.stmt_worklist.add(util.find_cfg_first_nodes(frame.cfg))
        frame.stmts_with_symbol_update.add(util.find_cfg_first_nodes(frame.cfg))

        if len(frame_stack) > 2:
            frame.path = frame_stack[-2].path + (frame.call_stmt_id, frame.method_id)
            frame_path = APath(frame.path)
            self.path_manager.add_path(frame_path)

        # avoid changing the content of the loader
        status = copy.deepcopy(self.loader.get_stmt_status_p2(method_id))
        symbol_state_space = self.loader.get_symbol_state_space_p2(method_id).copy()
        defined_symbols = self.loader.get_method_defined_symbols_p2(method_id).copy()
        state_bit_vector = self.loader.get_state_bit_vector_p2(method_id).copy()
        symbol_bit_vector = self.loader.get_symbol_bit_vector_p2(method_id).copy()
        frame.state_bit_vector_manager = state_bit_vector
        frame.symbol_bit_vector_manager = symbol_bit_vector
        method_summary_template = self.loader.get_method_summary_template(method_id).copy()
        frame.method_summary_template = method_summary_template
        self.adjust_index_of_status_space(len(global_space), status, frame, symbol_state_space, defined_symbols, symbol_bit_vector, state_bit_vector, method_summary_template)
        frame.stmt_id_to_status = status
        frame.defined_symbols = defined_symbols
        for item in symbol_state_space:
            global_space.add(item)

        frame.symbol_state_space = global_space
        frame.stmt_id_to_callee_info = self.get_stmt_id_to_callee_info(self.loader.get_method_internal_callees(method_id))

        frame.state_bit_vector_manager = self.loader.get_state_bit_vector_p2(method_id).copy()
        frame.method_def_use_summary = self.loader.get_method_def_use_summary(method_id).copy()

        frame.external_symbol_id_to_initial_state_index = frame.method_summary_template.external_symbol_to_state
        frame.space_summary = self.loader.get_symbol_state_space_summary_p2(method_id).copy()
        frame.symbol_graph.graph = self.loader.get_method_symbol_graph_p2(method_id).copy()
        frame.method_summary_instance.copy_template_to_instance(frame.method_summary_template)
        self.adjust_defined_symbols_and_init_bit_vector(frame, method_id)
        return frame

    def collect_external_symbol_states(self, frame: ComputeFrame, stmt_id, stmt, symbol_id, summary: MethodSummaryTemplate, old_key_state_indexes: set):
        # key_dynamic_content = summary.key_dynamic_content
        # if self.options.debug:
        #     print(f"@enter collect_external_symbol_states: symbol_id {symbol_id}, old_key_states {old_key_state_indexes}")
        if frame.stmt_counters[stmt_id] != config.FIRST_ROUND:
            return old_key_state_indexes

        new_state_indexes = set()

        status = frame.stmt_id_to_status[stmt_id]
        old_length = len(frame.symbol_state_space)
        for old_key_state_index in old_key_state_indexes:
            old_key_state = frame.symbol_state_space[old_key_state_index]
            if not(old_key_state and isinstance(old_key_state, State)):
                continue

            if old_key_state.data_type in (LIAN_INTERNAL.METHOD_DECL, LIAN_INTERNAL.CLASS_DECL):
                new_state_indexes.add(old_key_state_index)
                continue

            if old_key_state.symbol_or_state != SYMBOL_OR_STATE.EXTERNAL_KEY_STATE:
                continue

            # TODO JAVA CASE 处理java中 call this()的情况，应该去找它的构造函数
            if stmt.operation in CALL_OPERATION and old_key_state.data_type == LIAN_INTERNAL.THIS:
                continue

            if old_key_state.state_type != STATE_TYPE_KIND.ANYTHING:
                continue

            resolved_state_indexes = self.resolver.resolve_symbol_states(old_key_state, frame.frame_stack, frame, stmt_id, stmt, status)
            util.add_to_dict_with_default_set(frame.method_summary_instance.resolver_result, old_key_state_index, resolved_state_indexes)
            for each_resolved_state_index in resolved_state_indexes:
                each_resolved_state: State = frame.symbol_state_space[each_resolved_state_index]
                each_resolved_state.state_id = old_key_state.state_id
            new_state_indexes.update(resolved_state_indexes)

        # append callee space to caller space
        new_length = len(frame.symbol_state_space)
        while old_length < new_length:
            item = frame.symbol_state_space[old_length]
            if isinstance(item, State):
                status.defined_states.add(old_length)
            old_length += 1

        # update external symbols
        # used_external_symbols[symbol_id] = {IndexMapInSummary(raw_index = index, new_index = -1) for index in new_state_indexes}
        # if self.options.debug:
        #     for index in new_state_indexes:
        #         print(f"@exit collect_external_symbol_states: stmt_id {stmt_id}, symbol_id {symbol_id}, {frame.symbol_state_space[index]}")
        return new_state_indexes

    def generate_analysis_summary_and_s2space(self, frame: ComputeFrame):
        summary_data = SummaryData()
        return summary_data

    def save_analysis_summary_and_space(self, frame: ComputeFrame, method_summary: MethodSummaryInstance, compact_space: SymbolStateSpace, caller_frame: ComputeFrame = None):
        if not caller_frame:
            caller_frame: ComputeFrame = frame.frame_stack[-2]
        caller_frame.summary_collection[frame.call_site] = method_summary
        caller_frame.symbol_state_space_collection[frame.call_site] = compact_space
        self.loader.save_symbol_state_space_summary_p3(frame.call_site, compact_space)
        self.loader.save_method_summary_instance(frame.call_site, method_summary)
        # print("method_summary_instance:")
        # pprint.pprint(method_summary)
        # print("compact_space:")
        # pprint.pprint(compact_space)
        # self.loader.save_symbol_state_space_summary_p3(frame.method_id, compact_space)
        # self.loader.save_method_summary_template(frame.method_id, frame.method_summary_template)

    def save_result_to_last_frame_v1(self, frame_stack: ComputeFrameStack, current_frame: ComputeFrame, summary: MethodSummaryTemplate):
        self.save_result_to_last_frame_v2(frame_stack, current_frame, summary, current_frame.space_summary)

    def save_result_to_last_frame_v2(self, frame_stack: ComputeFrameStack, current_frame: ComputeFrame, summary: MethodSummaryTemplate, s2space: SymbolStateSpace):
        summary_data = SummaryData(summary, s2space)
        self.save_result_to_last_frame_v3(frame_stack, current_frame, summary_data)

    def save_result_to_last_frame_v3(self, frame_stack: ComputeFrameStack, current_frame: ComputeFrame, summary_data):
        last_frame: MetaComputeFrame = frame_stack[-2]
        key = (current_frame.caller_id, current_frame.call_stmt_id)
        last_frame.summary_collection[key] = summary_data

    def analyze_frame_stack(self, frame_stack: ComputeFrameStack, global_space, sfg: StateFlowGraph):
        frame_path = None
        while len(frame_stack) >= 2:
            # get current compute frame
            # print(f"\frame_stack: {frame_stack._stack}")
            frame: ComputeFrame = frame_stack.peek()
            # caller_id = frame.caller_id
            # call_stmt_id = frame.call_stmt_id
            caller_frame = frame_stack[-2]
            if not isinstance(caller_frame, ComputeFrame):
                frame_path = APath(frame.call_site)

            method_name = self.loader.convert_method_id_to_method_name(frame.method_id)
            if not self.options.quiet:
                print(f"Analyzing <method {frame.method_id} name: {method_name}>")

            if frame.content_to_be_analyzed:
                if self.options.debug:
                    util.debug(f"\t<method {frame.method_id}> has content to be analyzed: {frame.content_to_be_analyzed}")
                # check if all children have been analyzed
                children_done_flag = True
                for key in frame.content_to_be_analyzed:
                    value = frame.content_to_be_analyzed[key]
                    if not value:
                        frame.content_to_be_analyzed[key] = True
                        caller_id, call_stmt_id, callee_id = key
                        new_frame = ComputeFrame(
                            method_id = callee_id,
                            caller_id = caller_id,
                            call_stmt_id = call_stmt_id,
                            loader = self.loader,
                            space = global_space,
                            params_list = frame.args_list,
                            classes_of_method = frame.callee_classes_of_method,
                            this_class_ids = frame.callee_this_class_ids,
                            state_flow_graph = sfg,
                        )
                        frame_stack.add(new_frame)
                        children_done_flag = False
                        break
                if not children_done_flag:
                    continue

            else:
                self.path_manager.add_path(frame_path)
                summary_instance: MethodSummaryInstance = self.loader.get_method_summary_instance(frame.call_site)
                summary_compact_space: SymbolStateSpace = self.loader.get_symbol_state_space_summary_p3(frame.call_site)
                if summary_instance and summary_compact_space:
                    self.save_analysis_summary_and_space(frame, summary_instance.copy(), summary_compact_space.copy(), caller_frame)
                    frame_stack.pop()
                    continue

                # gl:这都什么意思

                # check if there is an available method summary
                # p2_summary_template = self.loader.get_method_summary_template(frame.method_id)
                # 如果没有summary->函数体为空->跳过
                # if util.is_empty(p2_summary_template):
                #     frame_stack.pop()
                #     continue

                #summary_compact_space: SymbolStateSpace = self.loader.get_symbol_state_space_summary_p2(frame.method_id)
                #summary_template: MethodSummaryTemplate = p2_summary_template.copy()
                # if not summary_template.dynamic_call_stmts:
                #     if self.options.quiet:
                #         util.debug(f"\t<method {frame.method_id}> does not need to be processed")

                #     self.save_analysis_summary_and_space(frame, summary_template.copy(), summary_compact_space.copy(), caller_frame)
                #     frame_stack.pop()
                #     continue

                if not frame.has_been_inited:
                    if self.init_compute_frame(frame, frame_stack, global_space) is None:
                        self.analyzed_method_list.add(frame.method_id)
                        frame_stack.pop()
                        continue

            result: P2ResultFlag = self.analyze_stmts(frame)
            if util.is_available(result) and result.interruption_flag:
                frame.interruption_flag = True
                data: InterruptionData = result.interruption_data
                new_callee = False
                frame.args_list = data.args_list
                frame.callee_classes_of_method = data.classes_of_method
                frame.callee_this_class_ids = data.this_class_ids
                for callee_id in data.callee_ids:
                    key = (data.caller_id, data.call_stmt_id, callee_id)
                    if key not in frame.content_to_be_analyzed:
                        frame.content_to_be_analyzed[key] = False
                        new_callee = True

                if new_callee:
                    continue

            # gl：为什么有的保存，有的不保存
            summary_data = self.generate_analysis_summary_and_s2space(frame)
            self.save_result_to_last_frame_v3(frame_stack, frame, summary_data)
            summary, space = self.generate_and_save_analysis_summary(frame, frame.method_summary_instance)
            self.save_analysis_summary_and_space(frame, summary, space, caller_frame)
            self.loader.save_stmt_status_p3(frame.call_site, frame.stmt_id_to_status)
            self.loader.save_method_defined_symbols_p3(frame.call_site, frame.defined_symbols)
            # self.loader.save_symbol_bit_vector_p3(frame.call_site, frame.symbol_bit_vector_manager)
            # self.loader.save_state_bit_vector_p3(frame.call_site, frame.state_bit_vector_manager)
            # self.loader.save_method_symbol_graph_p3(frame.call_site, frame.symbol_graph.graph)

            frame_stack.pop()
            if not self.options.quiet:
                print(f"<method {frame.method_id}> is Done")

        meta_frame: MetaComputeFrame = frame_stack[0]
        return meta_frame.summary_collection

    def init_frame_stack(self, entry_method_id, global_space, sfg):
        frame_stack = ComputeFrameStack()
        frame_stack.add(MetaComputeFrame()) #  used for collecting the final results
        entry_frame = ComputeFrame(method_id = entry_method_id, loader = self.loader, space = global_space, state_flow_graph=sfg)
        # entry_frame.path = tuple([entry_method_id])
        entry_frame.path = (entry_method_id,)
        entry_frame_path = APath(entry_frame.path)
        self.path_manager.add_path(entry_frame_path)
        frame_stack.add(entry_frame)
        return frame_stack

    def save_call_tree(self):
        # call_path中若只有一个函数，则不建call_tree
        entry_points_to_path = {}
        for call_path in self.path_manager.paths:
            if call_path[0] not in entry_points_to_path:
                entry_points_to_path[call_path[0]] = []
            entry_points_to_path[call_path[0]].append((call_path.path))


        for entry_point, call_paths in entry_points_to_path.items():
            if len(call_paths) == 0:
                continue
            current_tree = CallTree(entry_point)

            method_id_to_max_node_id = {}
            # 同一entry_point的callpaths从长到短排序，取最大前缀长度
            call_paths = sorted(call_paths, key=len, reverse=True)
            common_length = len(commonprefix(call_paths))
            if common_length % 2 == 0 and common_length != 0:
                common_length -= 1
            # 先建前缀
            self.convert_prefix_to_tree(call_paths[0], common_length, current_tree)
            # 再建后续
            for path in call_paths:
                if len(path) <= common_length:
                    continue
                self.convert_path_to_tree(path, common_length - 1, method_id_to_max_node_id, current_tree)
            self.add_unknown_callee_edge(current_tree)
            # current_tree.show()
            if current_tree.graph.number_of_edges() == 0:
                current_tree.graph.add_node(str(entry_point))
            self.loader.save_global_call_tree_by_entry_point(entry_point, current_tree.graph)

    def add_unknown_callee_edge(self, current_tree):
        node_list = []

        for node in current_tree.graph.nodes:
            node_name = node.split("#")[-1]
            if node_name  in self.caller_unknown_callee_edge:
                node_list.append(node)

        for node in node_list:
            node_name = node.split("#")[-1]
            for unknown_callee in self.caller_unknown_callee_edge[node_name]:
                current_tree.add_edge(node, unknown_callee[1], unknown_callee[0])

    def convert_prefix_to_tree(self, path, common_length, current_tree):
        index = 0
        while index <= common_length-3:
            if len(path) <= 1:
                break
            caller_id = path[index]
            call_stmt_id = path[index + 1]
            callee_id = path[index + 2]
            current_tree.add_edge(str(caller_id), str(callee_id), str(call_stmt_id))
            index += 2

    def convert_path_to_tree(self, path, common_index, method_id_to_max_node_id, current_tree):
        index = common_index
        while index <= len(path) - 3:
            #print(path)
            if len(path) <= 1:
                break

            caller_id = path[index]
            call_stmt_id = path[index + 1]
            callee_id = path[index + 2]
            if method_id_to_max_node_id.get(caller_id, 0) != 0 :
                caller_node_id = str(method_id_to_max_node_id.get(caller_id, 0)-1) + '#' + str(caller_id)
            # method_id_to_max_node_id[caller_id] = method_id_to_max_node_id.get(caller_id, 0) + 1
            callee_node_id = str(method_id_to_max_node_id.get(callee_id, 0)) + '#' + str(callee_id)
            method_id_to_max_node_id[callee_id] = method_id_to_max_node_id.get(callee_id, 0) + 1
            if index == common_index:
                current_tree.add_edge(str(caller_id), callee_node_id, str(call_stmt_id))
            else:
                current_tree.add_edge(caller_node_id, callee_node_id, str(call_stmt_id))
            index += 2

    def find_method_parent_by_name(self, method1, method2, method1_class = None, method2_class = None):
        method1_ids = self.convert_method_name_to_method_ids(method1)
        method2_ids = self.convert_method_name_to_method_ids(method2)

        if method1_class:
            method1_class_ids = self.loader.convert_class_name_to_class_ids(method1_class)
            for class_id in method1_class_ids:
                methods_in_class = self.loader.convert_class_id_to_method_ids(class_id)
                method1_ids = method1_ids & methods_in_class
        if method2_class:
            method2_class_ids = self.loader.convert_class_name_to_class_ids(method2_class)
            for class_id in method2_class_ids:
                methods_in_class = self.loader.convert_class_id_to_method_ids(class_id)
                method2_ids = method2_ids & methods_in_class


    def find_method_parent_by_id(self, call_tree, method1_id, method2_id):

        if method1_id not in call_tree or method2_id not in call_tree:
            return None

        method1_ancestors = {str(method1_id)}
        method2_ancestors = {str(method2_id)}

        reversed_tree = call_tree.reverse()

        roots = [n for n, d in reversed_tree.out_degree() if d == 0]

        def root_path(node):
            if node in roots:  # 自己就是根
                return [node]
            # 任取一条到根的最短路径即可
            for r in roots:
                if nx.has_path(reversed_tree, node, r):
                    return nx.shortest_path(reversed_tree, node, r)
            return [node]  # 孤立节点

        path_u = root_path(method1_id)
        path_v = root_path(method2_id)

        # path_u = list(nx.all_simple_paths(reversed_tree, method1_id, [n for n, d in reversed_tree.degree() if d == 0]))[0]
        # path_v = list(nx.all_simple_paths(reversed_tree, method2_id, [n for n, d in reversed_tree.degree() if d == 0]))[0]

        lca = None

        for p, q in zip(reversed(path_u), reversed(path_v)):
            if p == q:
                lca = p
            else:
                break

        return lca


    def is_specified_method(self, method_id, node):
        if method_id == node.split("#")[-1]:
            return True
        return False

    def run(self):
        if not self.options.quiet:
            print("\n########### # Phase III: Global (Top-down) Semantic Analysis ##########")
        global_space = SymbolStateSpace()
        for entry_point in self.loader.get_entry_points():
            # for path in self.call_graph.find_paths(entry_point):
            #     self.path_manager.add_path(path)
            # print(f"all paths in II: {self.path_manager.paths}")

            # 判断是否有@app装饰器
            # if not self.is_decorated_by_app(entry_point):
            #     continue
            sfg = StateFlowGraph(entry_point)
            frame_stack = self.init_frame_stack(entry_point, global_space, sfg)
            self.analyze_frame_stack(frame_stack, global_space, sfg)
            self.loader.save_graph_as_dot(sfg.graph, entry_point, self.analysis_phase_id)
            self.loader.save_global_sfg_by_entry_point(entry_point, sfg)
        # gl: 为啥是0
        self.loader.save_symbol_state_space_p3(0, global_space)
        self.save_call_tree()
        self.loader.save_global_call_path(self.path_manager.paths)


        self.loader.export()
        all_paths = self.loader.get_global_call_path()
        # print("所有的APaths: ",all_paths)

    def is_decorated_by_app(self, method_id):
        source_code = self.loader.get_stmt_parent_method_source_code(method_id)
        if "@.app" in source_code:
            return True
        return False
