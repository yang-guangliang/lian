#!/usr/bin/env python3

import os,sys
import pprint
import copy

from lian.core.static_semantics import StaticSemanticAnalysis
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
    StmtStatus
)
from lian.basics.entry_points import EntryPointGenerator
from lian.basics.control_flow import ControlFlowAnalysis
from lian.basics.stmt_def_use_analysis import StmtDefUseAnalysis
from lian.core.static_stmt_states import StaticStmtStates
from lian.core.static_semantics import StaticSemanticAnalysis
from lian.util.loader import Loader
from lian.core.resolver import Resolver
from lian.core.dynamic_stmt_states import GlobalStmtStates

class DynamicSemanticAnalysis(StaticSemanticAnalysis):
    def __init__(self, lian, analyzed_method_list):
        super().__init__(lian)
        self.path_manager = PathManager()
        self.analyzed_method_list = analyzed_method_list
        self.analysis_phase_id = ANALYSIS_PHASE_ID.DYNAMIC_SEMANTICS

    def get_stmt_id_to_callee_info(self, callees):
        """
        构建语句ID到被调用者信息的映射：
        参数：callees - 包含被调用者信息的对象列表
        返回：stmt_id -> 被调用者对象的字典
        """
        results = {}
        for each_callee in callees:
            results[each_callee.stmt_id] = each_callee
        return results

    def adjust_index_of_status_space(self, baseline_index, status, frame, space, defined_symbols, symbol_bit_vector, state_bit_vector):
        for symbol_def_nodes in symbol_bit_vector.bit_pos_to_id.values():
            symbol_def_nodes.index += baseline_index
        for state_def_nodes in state_bit_vector.bit_pos_to_id.values():
            state_def_nodes.index += baseline_index
        for symbol_def_nodes in defined_symbols.values():
            for node in symbol_def_nodes:
                node.index += baseline_index
        for stmt_status in status.values():
            for each_id, value in enumerate(stmt_status.used_symbols):
                stmt_status.used_symbols[each_id] = value + baseline_index
            for each_id, value in enumerate(stmt_status.implicitly_used_symbols):
                stmt_status.implicitly_used_states[each_id] = value + baseline_index
            for each_id, value in enumerate(stmt_status.implicitly_defined_symbols):
                stmt_status.implicitly_defined_symbols[each_id] = value + baseline_index
            stmt_status.defined_symbol += baseline_index
        for each_space in space:
            # each_space.index += baseline_index
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
        # print(space)

    def init_compute_frame(self, frame: ComputeFrame, frame_stack: ComputeFrameStack, global_space):
        """
        初始化计算帧环境：
        1. 设置方法参数/语句初始状态
        2. 初始化动态内容分析器
        3. 加载符号定义、状态定义及控制流图
        4. 构建符号图和状态空间初始视图
        """
        frame.has_been_inited = True
        frame.frame_stack = frame_stack
        method_id = frame.method_id

        frame.cfg = self.loader.get_method_cfg(method_id)
        if util.is_empty(frame.cfg):
            return

        frame.stmt_state_analysis = GlobalStmtStates(
            analysis_phase_id = self.analysis_phase_id,
            event_manager = self.event_manager,
            loader = self.loader,
            resolver = self.resolver,
            compute_frame = frame,
            path_manager = self.path_manager,
            analyzed_method_list = self.analyzed_method_list
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

        frame.defined_symbols = self.loader.load_method_defined_symbols_p2(method_id).copy()
        all_defs = set()
        for stmt_id in frame.defined_symbols:
            symbol_def_set = frame.defined_symbols[stmt_id]
            for symbol_def in symbol_def_set:
                all_defs.add(symbol_def)
        frame.all_defs = all_defs

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
        frame.symbol_bit_vector_manager = copy.deepcopy(self.loader.get_symbol_bit_vector_p2(method_id))
        self.adjust_index_of_status_space(len(global_space), status, frame, symbol_state_space, defined_symbols, symbol_bit_vector, state_bit_vector)
        frame.stmt_id_to_status = status
        frame.defined_symbols = defined_symbols
        for item in symbol_state_space:
            global_space.add(item)

        frame.symbol_state_space = global_space
        frame.stmt_id_to_callee_info = self.get_stmt_id_to_callee_info(self.loader.get_method_internal_callees(method_id))

        frame.state_bit_vector_manager = self.loader.get_state_bit_vector_p2(method_id).copy()
        frame.method_def_use_summary = self.loader.get_method_def_use_summary(method_id).copy()
        frame.method_summary_template = self.loader.get_method_summary_template(method_id).copy()
        frame.external_symbol_id_to_initial_state_index = frame.method_summary_template.external_symbol_to_state
        frame.space_summary = self.loader.get_symbol_state_space_summary_p2(method_id).copy()
        frame.symbol_graph.graph = self.loader.get_method_symbol_graph_p2(method_id).copy()
        frame.method_summary_instance.copy_template_to_instance(frame.method_summary_template)
        self.adjust_defined_symbols_and_init_bit_vector(frame, method_id)
        return frame

    def collect_external_symbol_states(self, frame: ComputeFrame, stmt_id, stmt, symbol_id, summary: MethodSummaryTemplate, old_key_state_indexes: set):
        # key_dynamic_content = summary.key_dynamic_content
        # if config.DEBUG_FLAG:
        #     print(f"进入collect_external_symbol_states: symbol_id {symbol_id}, old_key_states {old_key_state_indexes}")
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
        # if config.DEBUG_FLAG:
        #     for index in new_state_indexes:
        #         print(f"finally collect_external_symbol_states: stmt_id {stmt_id}, symbol_id {symbol_id}, {frame.symbol_state_space[index]}")
        return new_state_indexes

    def generate_analysis_summary_and_s2space(self, frame: ComputeFrame):
        summary_data = SummaryData()
        return summary_data

    def save_analysis_summary_and_space(self, frame: ComputeFrame, method_summary: MethodSummaryInstance, compact_space: SymbolStateSpace, caller_frame: ComputeFrame = None):
        """
        保存分析结果到上层帧：
        1. 关联调用点与方法摘要实例
        2. 存储压缩后的符号状态空间
        3. 更新调用链上下文中的汇总数据
        """
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
        """
        分版本保存中间分析结果到调用链末端帧：
        通过不同版本实现结果传递的阶段性存储
        """
        self.save_result_to_last_frame_v2(frame_stack, current_frame, summary, current_frame.space_summary)

    def save_result_to_last_frame_v2(self, frame_stack: ComputeFrameStack, current_frame: ComputeFrame, summary: MethodSummaryTemplate, s2space: SymbolStateSpace):
        summary_data = SummaryData(summary, s2space)
        self.save_result_to_last_frame_v3(frame_stack, current_frame, summary_data)

    def save_result_to_last_frame_v3(self, frame_stack: ComputeFrameStack, current_frame: ComputeFrame, summary_data):
        last_frame: MetaComputeFrame = frame_stack[-2]
        key = (current_frame.caller_id, current_frame.call_stmt_id)
        last_frame.summary_collection[key] = summary_data

    def analyze_frame_stack(self, frame_stack: ComputeFrameStack, global_space):
        """
        执行调用栈级分析流程：
        1. 处理动态调用分析需求
        2. 管理调用点摘要存储
        3. 处理未解析动态调用中断
        4. 生成最终方法摘要并保存结果
        """
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
            if config.DEBUG_FLAG:
                util.debug(f"\n\tPhase III Analysis is in progress <method {frame.method_id} name: {method_name}> \n")

            if frame.content_to_be_analyzed:
                if config.DEBUG_FLAG:
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
                #     if config.DEBUG_FLAG:
                #         util.debug(f"\t<method {frame.method_id}> does not need to be processed")

                #     self.save_analysis_summary_and_space(frame, summary_template.copy(), summary_compact_space.copy(), caller_frame)
                #     frame_stack.pop()
                #     continue

                if not frame.has_been_inited:
                    self.init_compute_frame(frame, frame_stack, global_space)

            result: P2ResultFlag = self.analyze_stmts(frame)
            if util.is_available(result) and result.interruption_flag:
                frame.interruption_flag = True
                data: InterruptionData = result.interruption_data
                new_callee = False
                frame.args_list = data.args_list
                frame.callee_classes_of_method = data.classes_of_method
                for callee_id in data.callee_ids:
                    key = (data.caller_id, data.call_stmt_id, callee_id)
                    # print(key)
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

            #pop之前，把parameter的states存到callerframe里去
            # for param in frame.params_list:
            #     param.
            #     caller_frame.symbol_state_space[param_id] = param_states
            # caller_frame.callee_param =

            frame_stack.pop()
            if config.DEBUG_FLAG:
                util.debug(f"\n\t<method {frame.method_id}> is Done\n")

        meta_frame: MetaComputeFrame = frame_stack[0]
        return meta_frame.summary_collection

    def init_frame_stack(self, entry_method_id, global_space):
        """
        初始化调用栈框架：
        1. 创建元帧用于结果收集
        2. 初始化入口方法计算帧
        3. 配置初始调用路径信息
        返回：初始化完成的调用栈对象
        """
        frame_stack = ComputeFrameStack()
        frame_stack.add(MetaComputeFrame()) #  used for collecting the final results
        entry_frame = ComputeFrame(method_id = entry_method_id, loader = self.loader, space = global_space)
        # entry_frame.path = tuple([entry_method_id])
        entry_frame.path = (entry_method_id,)
        entry_frame_path = APath(entry_frame.path)
        self.path_manager.add_path(entry_frame_path)
        frame_stack.add(entry_frame)
        return frame_stack

    def save_call_tree(self):
        dynamic_call_tree = CallGraph()
        for call_path in self.path_manager.paths:
            path = call_path.path
            index = 0
            while index <= len(path) - 3:
                print(path)
                if len(path) <= 1:
                    break
                caller_id = path[index]
                call_stmt_id = path[index + 1]
                callee_id = path[index + 2]
                dynamic_call_tree.add_edge(caller_id, callee_id, call_stmt_id)
                index += 2

        self.loader.save_dynamic_call_tree(dynamic_call_tree)
        self.loader.save_dynamic_call_path(self.path_manager.paths)

    def run(self):
        """
        执行全局分析主流程：
        1. 加载所有入口方法
        2. 为每个入口点初始化调用栈
        3. 遍历调用栈执行深度分析
        4. 持久化最终调用图和摘要数据
        """
        if config.DEBUG_FLAG:
            util.debug("\n\t++++++++++++++++++++++++++++++++++++++++++++++++\n"
                       "\t======== Phase III analysis is ongoing =========\n"
                       "\t++++++++++++++++++++++++++++++++++++++++++++++++\n")
        global_space = SymbolStateSpace()
        for entry_point in self.loader.get_entry_points():
            # for path in self.call_graph.find_paths(entry_point):
            #     self.path_manager.add_path(path)
            # print(f"all paths in II: {self.path_manager.paths}")
            frame_stack = self.init_frame_stack(entry_point, global_space)
            self.analyze_frame_stack(frame_stack, global_space)
        # gl: 为啥是0
        self.loader.save_symbol_state_space_p3(0, global_space)
        self.save_call_tree()


        self.loader.export()
        all_APaths = self.loader.get_dynamic_call_path()
        # print("所有的APaths: ",all_APaths)




