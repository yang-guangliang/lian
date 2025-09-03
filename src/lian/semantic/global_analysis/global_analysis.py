#!/usr/bin/env python3

import os,sys
import pprint
import copy

from lian.semantic.global_analysis.global_stmt_state_analysis import GlobalStmtStateAnalysis
from lian.semantic.summary_analysis.summary_generation import SemanticSummaryGeneration
from lian.util import util
from lian.config import config
import lian.util.data_model as dm
from lian.config.constants import (
    LIAN_INTERNAL,
    STATE_TYPE_KIND,
    SYMBOL_DEPENDENCY_GRAPH_EDGE_KIND,
    SYMBOL_OR_STATE,
    ANALYSIS_PHASE_NAME,
    CALL_OPERATION,
    SENSITIVE_OPERATIONS
)
from lian.semantic.semantic_structs import (
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
from lian.semantic.basic_analysis.entry_points import EntryPointGenerator
from lian.semantic.basic_analysis.control_flow import ControlFlowAnalysis
from lian.semantic.basic_analysis.stmt_def_use_analysis import StmtDefUseAnalysis
from lian.semantic.summary_analysis.stmt_state_analysis import StmtStateAnalysis
from lian.util.loader import Loader
from lian.semantic.resolver import Resolver

class GlobalAnalysis(SemanticSummaryGeneration):
    def __init__(self, lian, analyzed_method_list):
        """
        初始化全局分析上下文：
        1. 定义敏感操作类型集合（调用语句、数组读取等）
        2. 初始化分析方法列表、路径管理器
        3. 调用父类初始化方法设置符号状态基础结构
        """
        self.path_manager = PathManager()
        super().__init__(lian)
        self.analyzed_method_list = analyzed_method_list
        self.phase_name = ANALYSIS_PHASE_NAME.GlobalAnalysis

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

    def adjust_index_of_status_space(self, baseline_index, status, frame, space, symbol_to_define, symbol_bit_vector, state_bit_vector):

        for symbol_def_nodes in symbol_bit_vector.bit_pos_to_id.values():
            symbol_def_nodes.index += baseline_index
        for state_def_nodes in state_bit_vector.bit_pos_to_id.values():
            state_def_nodes.index += baseline_index
        for symbol_def_nodes in symbol_to_define.values():
            for node in symbol_def_nodes:
                node.index += baseline_index
        for stmtstatus in status.values():
            for each_id, value in enumerate(stmtstatus.used_symbols):
                stmtstatus.used_symbols[each_id] = value + baseline_index
            for each_id, value in enumerate(stmtstatus.implicitly_used_symbols):
                stmtstatus.implicitly_used_states[each_id] = value + baseline_index
            for each_id, value in enumerate(stmtstatus.implicitly_defined_symbols):
                stmtstatus.implicitly_defined_symbols[each_id] = value + baseline_index
            stmtstatus.defined_symbol += baseline_index
        for each_space in space:
            # each_space.index += baseline_index
            if isinstance(each_space, Symbol):
                new_set = set()
                for each_id in each_space.states:
                    new_set.add(each_id + baseline_index)
                each_space.states = new_set
            else:
                for each_id, stmtstatus in enumerate(each_space.array):
                    new_set = set()
                    for index in stmtstatus:
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

        _, parameter_decls, method_body = self.loader.load_method_gir(method_id)
        if util.is_available(parameter_decls):
            for row in parameter_decls:
                frame.stmt_id_to_stmt[row.stmt_id] = row
                frame.stmt_counters[row.stmt_id] = config.FIRST_ROUND
        if util.is_available(method_body):
            for row in method_body:
                frame.stmt_id_to_stmt[row.stmt_id] = row
                frame.stmt_counters[row.stmt_id] = config.FIRST_ROUND

        frame.stmt_state_analysis = GlobalStmtStateAnalysis(
            app_manager = self.app_manager,
            loader = self.loader,
            resolver = self.resolver,
            compute_frame = frame,
            path_manager = self.path_manager,
            analyzed_method_list = self.analyzed_method_list
        )

        # frame.symbol_to_define = self.loader.load_method_symbol_to_define_p2(method_id).copy()
        all_defs = set()
        for stmt_id in frame.symbol_to_define:
            symbol_def_set = frame.symbol_to_define[stmt_id]
            for symbol_def in symbol_def_set:
                all_defs.add(symbol_def)

        frame.all_defs = all_defs

        frame.state_to_define = self.loader.load_method_state_to_define_p2(method_id).copy()

        frame.cfg = self.loader.load_method_cfg(method_id)
        frame.stmt_worklist = SimpleWorkList(graph = frame.cfg)
        frame.stmt_worklist.add(frame.cfg.nodes())
        frame.symbol_changed_stmts.add(frame.cfg.nodes())

        if len(frame_stack) > 2:
            frame.path = frame_stack[-2].path + (frame.call_stmt_id, frame.method_id)

            frame_path = APath(frame.path)
            self.path_manager.add_path(frame_path)
        # avoid changing the content of the loader
        status = copy.deepcopy(self.loader.load_stmt_status_p2(method_id))
        symbol_state_space = self.loader.load_symbol_state_space_p2(method_id).copy()
        symbol_to_define = self.loader.load_method_symbol_to_define_p2(method_id).copy()
        symbol_bit_vector = copy.deepcopy(self.loader.load_symbol_bit_vector_p2(method_id))
        state_bit_vector = self.loader.load_state_bit_vector_p2(method_id).copy()
        self.adjust_index_of_status_space(len(global_space), status, frame, symbol_state_space, symbol_to_define, symbol_bit_vector, state_bit_vector)
        frame.stmt_id_to_status = status
        frame.symbol_to_define = symbol_to_define
        for item in symbol_state_space:
            global_space.add(item)

        frame.symbol_state_space = global_space

        frame.stmt_id_to_callee_info = self.get_stmt_id_to_callee_info(self.loader.load_method_internal_callees(method_id))

        frame.symbol_bit_vector_manager = symbol_bit_vector
        frame.state_bit_vector_manager = self.loader.load_state_bit_vector_p2(method_id).copy()
        frame.method_def_use_summary = self.loader.load_method_def_use_summary(method_id).copy()
        frame.method_summary_template = self.loader.load_method_summary_template(method_id).copy()
        frame.external_symbol_id_to_initial_state_index = frame.method_summary_template.external_symbol_to_state

        frame.space_summary = self.loader.load_symbol_state_space_summary_p2(method_id).copy()
        symbol_graph = self.loader.load_method_symbol_graph_p2(method_id).copy()
        frame.symbol_graph.graph = symbol_graph

        frame.method_summary_instance.copy_template_to_instance(frame.method_summary_template)
        self.adjust_symbol_to_define_and_init_bit_vector(frame, method_id)
        return frame

    def collect_external_symbol_states(self, frame: ComputeFrame, stmt_id, stmt, symbol_id, summary: MethodSummaryTemplate, old_key_state_indexes: set):
        """
        收集外部符号状态：
        1. 处理首次全局分析轮次的符号状态
        2. 解析动态调用相关状态（方法/类声明）
        3. 合并解析后的状态索引到当前作用域
        返回：更新后的状态索引集合
        """
        # key_dynamic_content = summary.key_dynamic_content
        # if config.DEBUG_FLAG:
        #     print(f"进入collect_external_symbol_states: symbol_id {symbol_id}, old_key_states {old_key_state_indexes}")
        if frame.stmt_counters[stmt_id] is not config.FIRST_ROUND:
            return old_key_state_indexes

        new_state_indexes = set()
        # if stmt.operation not in SENSITIVE_OPERATIONS:
        #     if symbol_id in summary.used_external_symbols:
        #         for index_pair in summary.used_external_symbols[symbol_id]:
        #             each_state_index = index_pair.raw_index
        #             new_state_indexes.add(each_state_index)
        #     if not new_state_indexes:
        #         return None
        #     return new_state_indexes

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

    def compute_states(self, stmt_id, stmt, frame: ComputeFrame):
        """
        执行符号状态计算：
        1. 收集输入符号状态位
        2. 生成输入符号列表
        3. 完成状态传播并检查持续分析条件
        4. 执行动态内容分析器计算具体状态
        5. 返回状态变化标志（符号/使用变化）
        """
        status = frame.stmt_id_to_status[stmt_id]
        in_states = {}
        symbol_graph = frame.symbol_graph.graph

        if not symbol_graph.has_node(stmt_id) or stmt.operation != "goto_stmt":
            return P2ResultFlag()

        # collect in state bits
        old_defined_symbol_states = set()
        if defined_symbol := frame.symbol_state_space[status.defined_symbol]:
            if isinstance(defined_symbol, Symbol):
                old_defined_symbol_states = defined_symbol.states
        old_status_defined_states = status.defined_states
        old_in_state_bits = status.in_state_bits
        old_index_ceiling = frame.symbol_state_space.get_length()
        old_implicitly_defined_symbols = status.implicitly_defined_symbols.copy()
        old_implicitly_used_symbols = status.implicitly_used_symbols.copy()
        status.in_state_bits = self.collect_in_state_bits(stmt_id, stmt, frame)
        self.unset_states_of_status(stmt_id, frame, status)

        # collect in state

        in_symbols = self.generate_in_symbols(stmt_id, frame, status, symbol_graph)
        # print(f"in_symbols: {in_symbols}")
        in_states = self.group_used_states(stmt_id, in_symbols, frame, status)
        # print(f"in_states@before complete_in_states: {in_states}")
        method_summary = frame.method_summary_template
        continue_flag = self.complete_in_states_and_check_continue_flag(stmt_id, frame, stmt, status, in_states, method_summary)
        if not continue_flag:
            if config.DEBUG_FLAG:
                print(f"  CONTINUE")
            if status.in_state_bits != old_in_state_bits:
                self.update_out_states(stmt_id, frame, status, old_index_ceiling, old_status_defined_states)
            self.restore_states_of_defined_symbol_and_status(stmt_id, frame, status, old_defined_symbol_states, old_implicitly_used_symbols, old_status_defined_states)
            return P2ResultFlag()
        self.unset_states_of_defined_symbol(stmt_id, frame, status)
        change_flag: P2ResultFlag = frame.stmt_state_analysis.compute_stmt_state(stmt_id, stmt, status, in_states)
        if change_flag is None:
            if config.DEBUG_FLAG:
                print(f"  NO CHANGE")
            change_flag = P2ResultFlag()

        self.adjust_computation_results(stmt_id, frame, status, old_index_ceiling)
        new_out_states = self.update_out_states(stmt_id, frame, status, old_index_ceiling, set(), 3)
        new_defined_symbol_states = set()
        if defined_symbol := frame.symbol_state_space[status.defined_symbol]:
            new_defined_symbol_states = defined_symbol.states

        if new_out_states or new_defined_symbol_states != old_defined_symbol_states:
            change_flag.states_changed = True

        if status.implicitly_defined_symbols != old_implicitly_defined_symbols:
            change_flag.def_changed = True

        if status.implicitly_used_symbols != old_implicitly_used_symbols:
            change_flag.use_changed = True

        if change_flag.states_changed:
            frame.symbol_changed_stmts.add(
                self.get_next_stmts_for_state_analysis(stmt_id, symbol_graph)
            )
        # print(f"out_symbol_bits: {frame.symbol_bit_vector_manager.explain(status.out_symbol_bits)}")


        return change_flag

    def generate_analysis_summary_and_s2space(self, frame: ComputeFrame):
        """
        生成分析摘要和压缩状态空间：
        创建包含方法摘要实例和压缩状态空间的汇总数据对象
        """
        summary_data = SummaryData()
        return summary_data

    def analyze_stmts(self, frame: ComputeFrame):
        """
        执行语句级分析循环：
        1. 管理工作列表中的待分析语句
        2. 处理控制流回边和循环分析
        3. 触发符号状态计算和中断处理
        4. 更新符号使用信息并推进分析轮次
        """
        while len(frame.stmt_worklist) != 0:
            stmt_id = frame.stmt_worklist.peek()
            if config.DEBUG_FLAG:
                util.debug(f"-----analyzing stmt <{stmt_id}> of method <{frame.method_id}>-----")
                # print("gir3: ",self.loader.load_stmt_gir(stmt_id))
            if stmt_id <= 0 or stmt_id not in frame.stmt_counters:
                frame.stmt_worklist.pop()
                continue
            # print(f"counter: {frame.stmt_counters[stmt_id]}")

            stmt = frame.stmt_id_to_stmt.get(stmt_id)
            if stmt_id in frame.loop_total_rounds:
                if frame.stmt_counters[stmt_id] <= frame.loop_total_rounds[stmt_id]:
                    frame.stmt_worklist.add(util.graph_successors(frame.cfg, stmt_id))
                    frame.symbol_changed_stmts.add(stmt_id)
            else:
                if frame.stmt_counters[stmt_id] < config.MAX_STMT_STATE_ANALYSIS_ROUND:
                    frame.stmt_worklist.add(util.graph_successors(frame.cfg, stmt_id))

            if frame.interruption_flag:
                # 关键指令？ 会中断
                frame.interruption_flag = False
            else:
                # compute in/out bitsz
                self.analyze_reaching_symbols(stmt_id, stmt, frame)

            # according to symbol_graph, compute the state flow of current statement
            result_flag = self.compute_states(stmt_id, stmt, frame)
            frame.symbol_changed_stmts.remove(stmt_id)

            # re-analyze def/use
            if result_flag.def_changed or result_flag.use_changed:
                # change out_bit to reflect implicitly_defined_symbols
                self.rerun_analyze_reaching_symbols(stmt_id, frame, result_flag)
                # update method def/use
                self.update_method_def_use_summary(stmt_id, frame)

            # check if interruption is enabled
            if result_flag.interruption_flag:
                frame.symbol_changed_stmts.add(stmt_id)
                return result_flag

            # move to the next statement
            frame.stmt_worklist.pop()
            frame.stmt_counters[stmt_id] += 1

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


            if config.DEBUG_FLAG:
                util.debug(f"\n\tPhase III Analysis is in progress <method {frame.method_id}> \n")

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
                summary_instance: MethodSummaryInstance = self.loader.load_method_summary_instance(frame.call_site)
                summary_compact_space: SymbolStateSpace = self.loader.load_symbol_state_space_summary_p3(frame.call_site)
                if summary_instance and summary_compact_space:
                    self.save_analysis_summary_and_space(frame, summary_instance.copy(), summary_compact_space.copy(), caller_frame)
                    frame_stack.pop()
                    continue

                # check if there is an available method summary
                p2_summary_template = self.loader.load_method_summary_template(frame.method_id)
                # 如果没有summary->函数体为空->跳过
                if util.is_empty(p2_summary_template):
                    frame_stack.pop()
                    continue

                summary_template: MethodSummaryTemplate = p2_summary_template.copy()
                summary_compact_space: SymbolStateSpace = self.loader.load_symbol_state_space_summary_p2(frame.method_id)

                # if not summary_template.dynamic_call_stmt:
                #     if config.DEBUG_FLAG:
                #         util.debug(f"\t<method {frame.method_id}> does not need to be processed")

                #     self.save_analysis_summary_and_space(frame, summary_template.copy(), summary_compact_space.copy(), caller_frame)
                #     frame_stack.pop()
                #     continue

                # Need to deal with dynamic callees
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

            summary_data = self.generate_analysis_summary_and_s2space(frame)
            self.save_result_to_last_frame_v3(frame_stack, frame, summary_data)
            summary, space = self.generate_and_save_analysis_summary(frame, frame.method_summary_instance)
            self.save_analysis_summary_and_space(frame, summary, space, caller_frame)
            self.loader.save_stmt_status_p3(frame.call_site, frame.stmt_id_to_status)
            self.loader.save_method_symbol_to_define_p3(frame.call_site, frame.symbol_to_define)
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


    def save_call_beauty_global(self, all_call_sites):
        self.call_beauty = []
        for edge in all_call_sites:
            caller_method_id = edge[0]
            callee_method_id= edge[1]
            stmt_id = edge[2]
            caller_class_id = self.loader.convert_method_id_to_class_id(caller_method_id)
            caller_class_name = self.loader.convert_class_id_to_class_name(caller_class_id)
            caller_method_name = self.loader.convert_method_id_to_method_name(caller_method_id)
            if util.is_empty(caller_class_name):
                caller_class_name = "None"
            if caller_method_id == -1 or not isinstance(caller_method_name,str):
                caller_method_name = "None"

            callee_class_id = self.loader.convert_method_id_to_class_id(callee_method_id)
            callee_class_name = self.loader.convert_class_id_to_class_name(callee_class_id)
            callee_method_name = self.loader.convert_method_id_to_method_name(callee_method_id)
            if util.is_empty(callee_class_name):
                callee_class_name = "None"
            if callee_method_id == -1 or not isinstance(callee_method_name,str):
                callee_method_name = "None"            
            one_call = [caller_method_id,caller_class_name,caller_method_name,callee_method_id,callee_class_name,callee_method_name,stmt_id]
            self.call_beauty.append(one_call)
        self.loader.save_call_beauty_global(self.call_beauty)
        self.loader._call_graph_stronger_loader2.export()

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
        for entry_point in self.loader.load_entry_points():
            # for path in self.call_graph.find_paths(entry_point):
            #     self.path_manager.add_path(path)
            # print(f"all paths in II: {self.path_manager.paths}")
            frame_stack = self.init_frame_stack(entry_point, global_space)
            result = self.analyze_frame_stack(frame_stack, global_space)
        self.loader.save_symbol_state_space_p3(0, global_space)

        self.loader.save_call_paths_p3(self.path_manager.paths)
        self.loader._call_path_p3_loader.export()
        all_APaths = self.loader.load_call_paths_p3()
        print("所有的APaths: ",all_APaths)
        all_call_sites = []
        for apath in all_APaths:
            call_site_list = apath.to_CallSite_list()
            for call_site in call_site_list:
                one_call_site = [call_site.caller_id,call_site.callee_id,call_site.call_stmt_id] 
                all_call_sites.append(one_call_site)
        self.save_call_beauty_global(all_call_sites)



