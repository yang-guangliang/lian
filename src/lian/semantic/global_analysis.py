#!/usr/bin/env python3

import os,sys
import pprint
import copy

from lian.semantic.dynamic_content_analysis import DynamicContentAnalysis
from lian.semantic.summary_generation import SemanticSummaryGeneration
from lian.util import util
from lian.config import config
import lian.util.data_model as dm
from lian.config.constants import (
    LianInternal,
    StateTypeKind,
    SymbolDependencyGraphEdgeKind,
    SymbolOrState,
    AnalysisPhaseName,
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
from lian.semantic.entry_points import EntryPointGenerator
from lian.semantic.control_flow import ControlFlowAnalysis
from lian.semantic.stmt_def_use_analysis import StmtDefUseAnalysis
from lian.semantic.stmt_state_analysis import StmtStateAnalysis
from lian.util.loader import Loader
from lian.semantic.resolver import Resolver

class GlobalAnalysis(SemanticSummaryGeneration):
    def __init__(self, lian):
        """
        初始化全局分析上下文：
        1. 定义敏感操作类型集合（调用语句、数组读取等）
        2. 初始化分析方法列表、路径管理器
        3. 调用父类初始化方法设置符号状态基础结构
        """
        self.analyzed_method_list = set()
        self.path_manager = PathManager()
        super().__init__(lian)
        self.phase_name = AnalysisPhaseName.GlobalAnalysis

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

    def init_compute_frame(self, frame: ComputeFrame, frame_stack: ComputeFrameStack):
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

        frame.stmt_state_analysis = DynamicContentAnalysis(
            app_manager = self.app_manager,
            loader = self.loader,
            resolver = self.resolver,
            compute_frame = frame,
            call_graph = self.call_graph,
            path_manager = self.path_manager,
            analyzed_method_list = self.analyzed_method_list
        )

        frame.symbol_to_define = self.loader.load_method_symbol_to_define_p2(method_id).copy()
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
        frame.stmt_id_to_status = copy.deepcopy(self.loader.load_stmt_status_p2(method_id))
        frame.symbol_state_space = self.loader.load_symbol_state_space_p2(method_id).copy()
        frame.stmt_id_to_callee_info = self.get_stmt_id_to_callee_info(self.loader.load_method_internal_callees(method_id))

        frame.symbol_bit_vector_manager = self.loader.load_symbol_bit_vector_p2(method_id).copy()
        frame.state_bit_vector_manager = self.loader.load_state_bit_vector_p2(method_id).copy()
        frame.method_def_use_summary = self.loader.load_method_def_use_summary(method_id).copy()
        frame.method_summary_template = self.loader.load_method_summary_template(method_id).copy()
        frame.external_symbol_id_to_initial_state_index = frame.method_summary_template.external_symbol_to_state

        frame.space_summary = self.loader.load_symbol_state_space_summary_p2(method_id).copy()
        symbol_graph = self.loader.load_method_symbol_graph_p2(method_id).copy()
        frame.symbol_graph.graph = symbol_graph

        frame.method_summary_instance.copy_template_to_instance(frame.method_summary_template)
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

            if old_key_state.data_type in (LianInternal.METHOD_DECL, LianInternal.CLASS_DECL):
                new_state_indexes.add(old_key_state_index)
                continue

            if old_key_state.symbol_or_state != SymbolOrState.EXTERNAL_KEY_STATE:
                continue

            # TODO JAVA CASE 处理java中 call this()的情况，应该去找它的构造函数
            if stmt.operation in CALL_OPERATION and old_key_state.data_type == LianInternal.THIS:
                continue

            if old_key_state.state_type != StateTypeKind.ANYTHING:
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

        if not symbol_graph.has_node(stmt_id):
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
        new_out_states = self.update_out_states(stmt_id, frame, status, old_index_ceiling)

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
                print("gir3: ",self.loader.load_stmt_gir(stmt_id))
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

    def analyze_frame_stack(self, frame_stack: ComputeFrameStack):
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
                    self.init_compute_frame(frame, frame_stack)

            result: P2ResultFlag = self.analyze_stmts(frame)
            if util.is_available(result) and result.interruption_flag:
                data: InterruptionData = result.interruption_data
                new_callee = False
                for callee_id in data.callee_ids:
                    key = (data.caller_id, data.call_stmt_id, callee_id)
                    # print(key)
                    if key not in frame.content_to_be_analyzed:
                        frame.content_to_be_analyzed[key] = False
                        new_callee = True

                if new_callee:
                    continue

            # summary_data = self.generate_analysis_summary_and_s2space(frame)
            # self.save_result_to_last_frame_v3(frame_stack, frame, summary_data)
            self.generate_and_save_analysis_summary(frame, frame.method_summary_instance)
            self.loader.save_symbol_state_space_p3(frame.call_site, frame.symbol_state_space)
            self.loader.save_stmt_status_p3(frame.call_site, frame.stmt_id_to_status)
            # self.loader.save_symbol_bit_vector_p3(frame.call_site, frame.symbol_bit_vector_manager)
            # self.loader.save_state_bit_vector_p3(frame.call_site, frame.state_bit_vector_manager)
            # self.loader.save_method_symbol_graph_p3(frame.call_site, frame.symbol_graph.graph)

            frame_stack.pop()
            if config.DEBUG_FLAG:
                util.debug(f"\n\t<method {frame.method_id}> is Done\n")

        meta_frame: MetaComputeFrame = frame_stack[0]
        return meta_frame.summary_collection

    def init_frame_stack(self, entry_method_id):
        """
        初始化调用栈框架：
        1. 创建元帧用于结果收集
        2. 初始化入口方法计算帧
        3. 配置初始调用路径信息
        返回：初始化完成的调用栈对象
        """
        frame_stack = ComputeFrameStack()
        frame_stack.add(MetaComputeFrame()) #  used for collecting the final results
        entry_frame = ComputeFrame(method_id = entry_method_id, loader = self.loader)
        # entry_frame.path = tuple([entry_method_id])
        entry_frame.path = (entry_method_id,)
        entry_frame_path = APath(entry_frame.path)
        self.path_manager.add_path(entry_frame_path)
        frame_stack.add(entry_frame)
        return frame_stack

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

        for entry_point in self.loader.load_entry_points():
            # for path in self.call_graph.find_paths(entry_point):
            #     self.path_manager.add_path(path)
            # print(f"all paths in II: {self.path_manager.paths}")
            frame_stack = self.init_frame_stack(entry_point)
            result = self.analyze_frame_stack(frame_stack)

        self.loader.save_call_paths_p3(self.path_manager.paths)
        self.loader._call_path_p3_loader.export()
        all_APaths = self.loader.load_call_paths_p3()
        print("所有的APaths: ",all_APaths)




