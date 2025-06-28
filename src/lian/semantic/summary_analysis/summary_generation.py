#!/usr/bin/env python3
import copy
import pprint, os
import sys
import traceback
import numpy

from lian.config import type_table
from lian.util import util
from lian.config import config
from lian.config.constants import (
    SymbolDependencyGraphEdgeKind,
    LianInternal,
    StateTypeKind,
    SymbolOrState,
    ControlFlowKind,
    EventKind,
    SymbolKind,
    AnalysisPhaseName,
    RETURN_STMT_OPERATION,
    SUMMARY_GENERAL_SYMBOL_ID
)
import lian.apps.event_return as er
from lian.apps.app_template import EventData
from lian.semantic.semantic_structs import (
    AccessPoint,
    SimpleWorkList,
    StateDefNode,
    Symbol,
    State,
    ComputeFrame,
    ComputeFrameStack,
    CallGraph,
    SimplyGroupedMethodTypes,
    InterruptionData,
    P2ResultFlag,
    StmtStatus,
    SymbolDefNode,
    MethodSummaryTemplate,
    IndexMapInSummary,
    SymbolStateSpace,
    LastSymbolDefNode,
    CountStmtDefStateNode
)
from lian.util.loader import Loader
from lian.semantic.resolver import Resolver
from lian.semantic.summary_analysis.stmt_state_analysis import StmtStateAnalysis

# from lian.config.type_table import get_lang_init_script_name

stmt_counts = 0

class SemanticSummaryGeneration:
    def __init__(self, lian):
        """
        构建语句ID到被调用者信息的映射表。
        参数：callees - 包含被调用者信息的列表
        返回：stmt_id -> 被调用者对象的字典
        """
        self.analysis_phases = []
        self.count_stmt_def_states = {}
        self.count_stmt_op_def_states = {}
        self.options = lian.options
        self.app_manager = lian.app_manager
        self.loader:Loader = lian.loader
        self.resolver: Resolver = lian.resolver
        self.call_graph = CallGraph()
        self.analyzed_method_list = set()
        self.inited_unit_list = set()
        self.phase_name = AnalysisPhaseName.SemanticSummaryGeneration
        self.LOOP_OPERATIONS = set(["for_stmt", "forin_stmt", "for_value_stmt", "while_stmt", "dowhile_stmt"])

    def get_stmt_id_to_callee_info(self, callees):
        results = {}
        for each_callee in callees:
            results[each_callee.stmt_id] = each_callee
        return results

    def adjust_symbol_to_define_and_init_bit_vector(self, frame: ComputeFrame, method_id):
        """
        调整符号的定义位向量，初始化符号状态空间。
        处理旧符号定义，构建新的符号到定义节点的映射关系。
        """
        old_symbol_to_define = self.loader.load_method_symbol_to_define(method_id)
        if not old_symbol_to_define:
            return

        all_symbol_defs = set()
        result = {}
        for symbol_id, defined_set in old_symbol_to_define.items():
            for defined_stmt_id in defined_set:
                status = frame.stmt_id_to_status[defined_stmt_id]
                all_defined_indexes = [status.defined_symbol] + status.implicitly_defined_symbols
                for each_index in all_defined_indexes:
                    content = frame.symbol_state_space[each_index]
                    if isinstance(content, Symbol):
                        if content.symbol_id == symbol_id:
                            if symbol_id not in result:
                                result[symbol_id] = set()
                            symbol_node = SymbolDefNode(
                                index = each_index, symbol_id=symbol_id, stmt_id=defined_stmt_id
                            )
                            result[symbol_id].add(symbol_node)
                            all_symbol_defs.add(symbol_node)
                            break

        frame.symbol_to_define = result
        frame.symbol_bit_vector_manager.init(all_symbol_defs)
        frame.all_symbol_defs = all_symbol_defs

    def adjust_state_to_define_and_init_bit_vector(self, frame: ComputeFrame, method_id):
        """
        调整状态的定义位向量，初始化状态状态空间。
        处理旧状态定义，构建状态到定义节点的映射关系。
        """
        frame.state_to_define = self.loader.load_method_state_to_define_p1(method_id)
        all_state_defs = set()
        for state_id, defined_set in frame.state_to_define.items():
            for state_def_node in defined_set:
                all_state_defs.add(state_def_node)

        frame.state_bit_vector_manager.init(all_state_defs)
        frame.all_state_defs = all_state_defs

    def init_compute_frame(self, frame: ComputeFrame, frame_stack):
        """
        初始化计算帧，设置符号状态、控制流图、工作列表等基础数据。
        加载方法参数、方法体、符号初始状态等信息。
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

        frame.stmt_state_analysis = StmtStateAnalysis(
            app_manager = self.app_manager,
            loader = self.loader,
            resolver = self.resolver,
            compute_frame = frame,
            call_graph = self.call_graph,
            analyzed_method_list = self.analyzed_method_list
        )

        frame.cfg = self.loader.load_method_cfg(method_id)
        if util.is_empty(frame.cfg):
            return

        frame.stmt_worklist = SimpleWorkList(graph = frame.cfg)
        frame.stmt_worklist.add(util.find_cfg_first_nodes(frame.cfg))
        frame.symbol_changed_stmts.add(util.find_cfg_first_nodes(frame.cfg))

        # avoid changing the content of the loader
        frame.stmt_id_to_status = copy.deepcopy(self.loader.load_stmt_status_p1(method_id))
        frame.symbol_state_space = self.loader.load_symbol_state_space_p1(method_id).copy()
        if util.is_empty(frame.symbol_state_space):
            return

        frame.stmt_id_to_callee_info = self.get_stmt_id_to_callee_info(
            self.loader.load_method_internal_callees(method_id)
        )
        frame.method_def_use_summary = self.loader.load_method_def_use_summary(method_id).copy()
        frame.all_local_symbol_ids = frame.method_def_use_summary.local_symbol_ids
        #print(frame.method_def_use_summary)

        self.adjust_symbol_to_define_and_init_bit_vector(frame, method_id)
        self.adjust_state_to_define_and_init_bit_vector(frame, method_id)

        return frame

    def update_current_symbol_bit(self, bit_id: SymbolDefNode, frame: ComputeFrame, current_bits):
        """
        更新当前符号的位向量，处理新定义的符号节点。
        参数：bit_id - 符号定义节点，current_bits - 当前位向量
        返回：更新后的位向量
        """
        symbol_id = bit_id.symbol_id
        if bit_id not in frame.all_symbol_defs:
            frame.all_symbol_defs.add(bit_id)
            if symbol_id not in frame.symbol_to_define:
                frame.symbol_to_define[symbol_id] = set()
            frame.symbol_to_define[symbol_id].add(bit_id)
            frame.symbol_bit_vector_manager.add_bit_id(bit_id)
        all_def_stmts = frame.symbol_to_define[symbol_id]
        current_bits = frame.symbol_bit_vector_manager.kill_bit_ids(current_bits, all_def_stmts)
        current_bits = frame.symbol_bit_vector_manager.gen_bit_ids(current_bits, [bit_id])

        return current_bits

    def update_current_state_bit(self, bit_id: StateDefNode, frame: ComputeFrame, current_bits, new_defined_state_set: set):
        """
        更新当前状态的位向量，处理新定义的状态节点。
        参数：bit_id - 状态定义节点，current_bits - 当前位向量
        返回：更新后的位向量
        """
        state_id = bit_id.state_id
        if bit_id not in frame.all_state_defs:
            frame.all_state_defs.add(bit_id)
            util.add_to_dict_with_default_set(frame.state_to_define, state_id, bit_id)
            frame.state_bit_vector_manager.add_bit_id(bit_id)
        # 由于一条指令可能同时新定义多个state id相同的state，因此不能将同stmt id的state kill掉
        # 每一轮需要将同一语句前面几轮中相同state id的state都kill掉
        all_def_states = frame.state_to_define[state_id]
        all_def_stmt_except_current_stmt = set()
        for each_def_state in all_def_states:
            # 不是本轮产生的state
            if each_def_state.index not in new_defined_state_set:
                all_def_stmt_except_current_stmt.add(each_def_state)

        current_bits = frame.state_bit_vector_manager.kill_bit_ids(current_bits, all_def_stmt_except_current_stmt)
        current_bits = frame.state_bit_vector_manager.gen_bit_ids(current_bits, [bit_id])

        return current_bits

    def update_out_states(self, stmt_id, frame: ComputeFrame, status: StmtStatus, old_index_ceiling, old_status_defined_states = set()):
        """
        为每个defined_states创建一个StateDefNode，并更新out_state_bits，(kill/gen也在这个过程中进行)。
        如果该语句有defined_symbol且defined_symbol没有任何state，说明没解析出来，人为创建一个UNSOLVED的state给defined_symbol。
        输出这句语句产生的new_states的集合(超出原来state_space长度的states)。
        """
        # 这条语句新产生的状态
        new_defined_state_set = set()
        for index in status.defined_states:
            if index >= old_index_ceiling: # newly generated states
                new_defined_state_set.add(index)

        if old_status_defined_states:
            defined_states = old_status_defined_states
            if not new_defined_state_set:
                new_defined_state_set = old_status_defined_states
        else:
            defined_states = status.defined_states

        state_current_bits = status.in_state_bits

        # 为每个defined_state创建一个StateDefNode，并更新out_state_bits
        for defined_state_index in defined_states:
            defined_state: State = frame.symbol_state_space[defined_state_index]
            if not isinstance(defined_state, State):
                continue

            state_id = defined_state.state_id
            state_node = StateDefNode(index=defined_state_index, state_id=state_id, stmt_id=stmt_id, stmt_counter=frame.stmt_counters[stmt_id])
            state_current_bits = self.update_current_state_bit(state_node, frame, state_current_bits, new_defined_state_set)
        status.out_state_bits = state_current_bits

        # 若本句语句的defined_symbol没有被解析出任何状态，生成一个UNSOLVED状态给它。并不加入到out_state_bits
        if defined_symbol := frame.symbol_state_space[status.defined_symbol]:
            if isinstance(defined_symbol, Symbol) and len(defined_symbol.states) == 0:
                new_state = State(
                    stmt_id = stmt_id,
                    source_symbol_id = defined_symbol.symbol_id,
                    state_type = StateTypeKind.UNSOLVED
                )
                defined_symbol.states.add(frame.symbol_state_space.add(new_state))
                # print("本句语句的defined_symbol没有被解析出任何状态,生成一个UNSOLVED状态给它",defined_symbol.states)

        # print("@update_out_states new_defined_state_set", new_defined_state_set)
        return new_defined_state_set

    def update_symbols_if_changed(
        self, stmt_id, frame: ComputeFrame, status: StmtStatus, old_in_symbol_bits, old_out_symbol_bits, def_changed = False, use_changed = False
    ):
        """
        根据符号或使用情况的变化更新符号图。
        参数：def_changed - 符号定义变化标记，use_changed - 使用变化标记
        """
        if use_changed:
            self.update_used_symbols_to_symbol_graph(stmt_id, frame, only_implicitly_used_symbols = True)
        elif status.in_symbol_bits != old_in_symbol_bits:
            self.update_used_symbols_to_symbol_graph(stmt_id, frame)

        if status.out_symbol_bits != old_out_symbol_bits or def_changed:
            frame.symbol_changed_stmts.add(util.graph_successors(frame.cfg, stmt_id))

    def analyze_reaching_symbols(self, stmt_id, stmt, frame: ComputeFrame):
        """
        分析符号的可达性，计算输入符号位向量。
        处理循环控制流，更新符号状态传播。
        """
        status = frame.stmt_id_to_status[stmt_id]
        old_out_symbol_bits = status.out_symbol_bits
        old_in_symbol_bits = status.in_symbol_bits
        status.in_symbol_bits = 0

        # collect parent stmts
        parent_stmt_ids = util.graph_predecessors(frame.cfg, stmt_id)
        if stmt.operation in self.LOOP_OPERATIONS:
            new_parent_stmt_ids = []
            for each_parent_stmt_id in parent_stmt_ids:
                edge_weight = util.get_graph_edge_weight(frame.cfg, each_parent_stmt_id, stmt_id)
                if frame.stmt_counters[stmt_id] == config.FIRST_ROUND and edge_weight != ControlFlowKind.LOOP_BACK:
                    new_parent_stmt_ids.append(each_parent_stmt_id)
                elif frame.stmt_counters[stmt_id] > config.FIRST_ROUND and edge_weight == ControlFlowKind.LOOP_BACK:
                    new_parent_stmt_ids.append(each_parent_stmt_id)
            parent_stmt_ids = new_parent_stmt_ids

        # collect in symbol bits
        for each_parent_stmt_id in parent_stmt_ids:
            if each_parent_stmt_id in frame.stmt_id_to_status:
                status.in_symbol_bits |= frame.stmt_id_to_status[each_parent_stmt_id].out_symbol_bits

        if self.phase_name == AnalysisPhaseName.SemanticSummaryGeneration:
            if frame.stmt_counters[stmt_id] != config.FIRST_ROUND and status.in_symbol_bits == old_in_symbol_bits:
                return
        elif self.phase_name == AnalysisPhaseName.GlobalAnalysis:
            if status.in_symbol_bits == old_in_symbol_bits:
                return

        current_bits = status.in_symbol_bits
        all_defined_symbols = [status.defined_symbol] + status.implicitly_defined_symbols
        for tmp_counter, defined_symbol_index in enumerate(all_defined_symbols):
            defined_symbol = frame.symbol_state_space[defined_symbol_index]
            if not isinstance(defined_symbol, Symbol):
                continue
            # pprint.pprint(defined_symbol)
            symbol_id = defined_symbol.symbol_id
            key = SymbolDefNode(index = defined_symbol_index, symbol_id = symbol_id, stmt_id = stmt_id, stmt_counter = frame.stmt_counters[stmt_id])
            current_bits = self.update_current_symbol_bit(key, frame, current_bits)

            edge_type = SymbolDependencyGraphEdgeKind.EXPLICITLY_DEFINED
            if tmp_counter != 0:
                edge_type = SymbolDependencyGraphEdgeKind.IMPLICITLY_DEFINED

            frame.symbol_graph.add_edge(stmt_id, key, edge_type)
        status.out_symbol_bits = current_bits

        # check if the out bits are changed
        if self.phase_name == AnalysisPhaseName.SemanticSummaryGeneration:
            if frame.stmt_counters[stmt_id] == config.FIRST_ROUND:
                self.update_used_symbols_to_symbol_graph(stmt_id, frame)
                frame.symbol_changed_stmts.add(util.graph_successors(frame.cfg, stmt_id))
            else:
                self.update_symbols_if_changed(stmt_id, frame, status, old_in_symbol_bits, old_out_symbol_bits)

        elif self.phase_name == AnalysisPhaseName.GlobalAnalysis:
                self.update_symbols_if_changed(stmt_id, frame, status, old_in_symbol_bits, old_out_symbol_bits)

    def rerun_analyze_reaching_symbols(self, stmt_id, frame: ComputeFrame, result_flag: P2ResultFlag):
        """
        重新分析符号可达性（当结果发生变化时）。
        处理隐式使用符号的变化传播。
        """
        status = frame.stmt_id_to_status[stmt_id]
        old_out_symbol_bits = status.out_symbol_bits
        current_bits = status.out_symbol_bits
        all_defined_symbols = status.implicitly_defined_symbols
        for defined_symbol_index in all_defined_symbols:
            defined_symbol = frame.symbol_state_space[defined_symbol_index]
            if not isinstance(defined_symbol, Symbol):
                continue
            symbol_id = defined_symbol.symbol_id
            key = SymbolDefNode(index=defined_symbol_index, symbol_id=symbol_id, stmt_id=stmt_id, stmt_counter=frame.stmt_counters[stmt_id])
            current_bits = self.update_current_symbol_bit(key, frame, current_bits)
            frame.symbol_graph.add_edge(stmt_id, key, SymbolDependencyGraphEdgeKind.IMPLICITLY_DEFINED)
        status.out_symbol_bits = current_bits
        # print("rerun_new_out_bits")
        # print(frame.symbol_bit_vector_manager.explain(current_bits))

        # check if the out bits are changed
        self.update_symbols_if_changed(stmt_id, frame, status, status.in_symbol_bits, old_out_symbol_bits, result_flag.def_changed, result_flag.use_changed)

    def check_reachable_symbol_defs(self, stmt_id, frame: ComputeFrame, status, used_symbol: Symbol, available_symbol_defs):
        """
        检查可到达的符号定义，区分本地定义与外部引用。
        返回符号定义节点的集合。
        """
        used_symbol_id = used_symbol.symbol_id
        # print(f"stmt_id: {stmt_id}, used_symbol: {used_symbol.name}")
        reachable_symbol_defs = set()
        if used_symbol_id in frame.symbol_to_define:
            reachable_symbol_defs = available_symbol_defs & frame.symbol_to_define[used_symbol_id]
        else:
            if used_symbol_id not in frame.all_local_symbol_ids:
                if used_symbol_id not in frame.method_def_use_summary.used_external_symbol_ids:
                    frame.method_def_use_summary.used_external_symbol_ids.add(used_symbol_id)
                reachable_symbol_defs.add(
                    SymbolDefNode(symbol_id=used_symbol_id)
                )

        return reachable_symbol_defs

    def update_used_symbols_to_symbol_graph(self, stmt_id, frame: ComputeFrame, only_implicitly_used_symbols=False):
        """
        更新符号图中使用的符号边。
        参数：only_implicitly_used_symbols - 是否仅处理隐式使用
        """
        status = frame.stmt_id_to_status[stmt_id]
        available_defs = frame.symbol_bit_vector_manager.explain(status.in_symbol_bits)
        all_used_symbols = []
        if only_implicitly_used_symbols:
            all_used_symbols = status.implicitly_used_symbols
        else:
            all_used_symbols = status.used_symbols + status.implicitly_used_symbols

        for used_symbol_index in all_used_symbols:
            used_symbol = frame.symbol_state_space[used_symbol_index]
            if not isinstance(used_symbol, Symbol):
                continue

            reachable_defs = self.check_reachable_symbol_defs(stmt_id, frame, status, used_symbol, available_defs)
            edge_type = SymbolDependencyGraphEdgeKind.IMPLICITLY_USED
            if not only_implicitly_used_symbols:
                if used_symbol_index < len(status.used_symbols):
                    edge_type = SymbolDependencyGraphEdgeKind.EXPLICITLY_USED
            for tmp_key in reachable_defs:
                frame.symbol_graph.add_edge(tmp_key, stmt_id, edge_type)

    def collect_in_state_bits(self, stmt_id, stmt, frame: ComputeFrame):
        """
        收集语句的输入状态位，处理控制流合并。
        返回合并后的状态位向量。
        """
        in_state_bits = 0
        parent_stmt_ids = util.graph_predecessors(frame.cfg, stmt_id)
        if stmt.operation in self.LOOP_OPERATIONS:
            new_parent_stmt_ids = []
            for each_parent_stmt_id in parent_stmt_ids:
                edge_weight = util.get_graph_edge_weight(frame.cfg, each_parent_stmt_id, stmt_id)
                if frame.stmt_counters[stmt_id] == config.FIRST_ROUND and edge_weight != ControlFlowKind.LOOP_BACK:
                    new_parent_stmt_ids.append(each_parent_stmt_id)
                elif frame.stmt_counters[stmt_id] > config.FIRST_ROUND and edge_weight == ControlFlowKind.LOOP_BACK:
                    new_parent_stmt_ids.append(each_parent_stmt_id)
            parent_stmt_ids = new_parent_stmt_ids

        for each_parent_stmt_id in parent_stmt_ids:
            if each_parent_stmt_id in frame.stmt_id_to_status:
                in_state_bits |= frame.stmt_id_to_status[each_parent_stmt_id].out_state_bits

        return in_state_bits

    def generate_in_symbols(self, stmt_id, frame: ComputeFrame, status: StmtStatus, symbol_graph):
        """
        生成输入符号列表，基于使用符号和可用定义。
        返回符号对象列表。
        """
        in_symbols = []

        available_defs = frame.symbol_bit_vector_manager.explain(status.in_symbol_bits)
        all_used_symbols = status.used_symbols + status.implicitly_used_symbols
        all_reachable_defs = set()
        for used_symbol_index in all_used_symbols:
            used_symbol = frame.symbol_state_space[used_symbol_index]
            if not isinstance(used_symbol, Symbol):
                continue

            all_reachable_defs.update(self.check_reachable_symbol_defs(stmt_id, frame, status, used_symbol, available_defs))

        for node in all_reachable_defs:
            if not isinstance(node, SymbolDefNode):
                continue

            if node.stmt_id <= 0:
                continue

            symbol = frame.symbol_state_space[node.index]
            in_symbols.append(symbol)

        return in_symbols

    #def group_used_states_and_obtain_newest_states(self, stmt_id, in_symbols, frame: ComputeFrame):
    def group_used_states(self, stmt_id, in_symbols, frame: ComputeFrame, status):
        """
        准备in_states, 返回一个集合 {symbol_id: {newest_states} }
        """
        # all_in_states are all states of used symbols
        # all_in_states -> align -> status.used_symbols
        symbol_id_to_state_index = {}
        for each_in_symbol in in_symbols:
            if not isinstance(each_in_symbol, Symbol):
                continue

            symbol_id = each_in_symbol.symbol_id
            available_state_defs = frame.state_bit_vector_manager.explain(status.in_state_bits)
            # print("group_used_states@ available_state_defs",available_state_defs)
            # print(f"group_used_states@ in_symbol {symbol_id}.states", each_in_symbol.states)
            latest_state_index_set = self.resolver.collect_newest_states_by_state_indexes(
                frame, stmt_id, each_in_symbol.states, available_state_defs
            )
            # print("group_used_states@ latest_state_index_set",latest_state_index_set)
            if latest_state_index_set:
                util.add_to_dict_with_default_set(symbol_id_to_state_index, symbol_id, latest_state_index_set)

        # print("group_used_states@ symbol_id_to_state_index before fusion",symbol_id_to_state_index)
        for symbol_id, each_symbol_in_states in symbol_id_to_state_index.items():
            # 对每个symbol的in_states按state_id合并一次，并将fusion_state添加到status.defined_states中
            state_id_to_indexes = self.group_states_with_state_ids(frame, each_symbol_in_states)
            for state_id, states_with_same_id in state_id_to_indexes.items():
                fusion_state = frame.stmt_state_analysis.fuse_states_to_one_state(states_with_same_id, stmt_id, status)
                each_symbol_in_states -= states_with_same_id
                each_symbol_in_states |= fusion_state
        # print("group_used_states@ symbol_id_to_state_index after fusion",symbol_id_to_state_index)
        return symbol_id_to_state_index

    def generate_external_symbol_states(self, frame: ComputeFrame, stmt_id, symbol_id, used_symbol, method_summary):
        """
        生成外部符号的状态（如方法/类声明）。
        返回新生成的状态索引集合。
        """
        if self.loader.is_method_decl(symbol_id):
            new_state = State(
                stmt_id = stmt_id,
                source_symbol_id = symbol_id,
                data_type = LianInternal.METHOD_DECL,
                state_type = StateTypeKind.REGULAR,
                value = symbol_id,
            )
            new_state.access_path = [AccessPoint(key=used_symbol.name, state_id=new_state.state_id)]
        elif self.loader.is_class_decl(symbol_id):
            new_state = State(
                stmt_id = stmt_id,
                source_symbol_id = symbol_id,
                data_type = LianInternal.CLASS_DECL,
                state_type = StateTypeKind.REGULAR,
                value = symbol_id
            )
            new_state.access_path = [AccessPoint(key=used_symbol.name, state_id=new_state.state_id)]
        elif self.loader.is_unit_id(symbol_id):
            new_state = State(
                stmt_id = stmt_id,
                source_symbol_id = symbol_id,
                data_type = LianInternal.UNIT,
                state_type = StateTypeKind.REGULAR,
                value = symbol_id
            )
            new_state.access_path = [AccessPoint(key=used_symbol.name, state_id=new_state.state_id)]
        else:
            new_state = State(
                stmt_id = stmt_id,
                source_symbol_id = symbol_id,
                state_type = StateTypeKind.ANYTHING

            )
            new_state.access_path = [AccessPoint(key=used_symbol.name, state_id=new_state.state_id)]

        if used_symbol.name == LianInternal.THIS:
            new_state.data_type = LianInternal.THIS
            # new_state.symbol_or_state = SymbolOrState.EXTERNAL_KEY_STATE
            # method_summary.dynamic_call_stmt.add(stmt_id)

        # util.add_to_dict_with_default_set(frame.used_external_symbol_id_to_state_id_set, symbol_id, new_state.state_id)
        index = frame.symbol_state_space.add(new_state)
        frame.initial_state_to_external_symbol[new_state.state_id] = symbol_id
        frame.external_symbol_id_to_initial_state_index[symbol_id] = index
        event = EventData(
            frame.lang,
            EventKind.P2STATE_GENERATE_EXTERNAL_STATES,
            {
                "stmt_id": stmt_id,
                "frame": frame,
                "state_analysis": self,
                "symbol_id": symbol_id,
                "new_state": new_state,
                "external_state_index": index
            }
        )
        app_return = self.app_manager.notify(event)

        status = frame.stmt_id_to_status[stmt_id]
        util.add_to_dict_with_default_set(
            frame.state_to_define,
            new_state.state_id,
            StateDefNode(index=index, state_id=new_state.state_id, stmt_id=stmt_id)
        )
        status.defined_states.add(index)

        index_pair = IndexMapInSummary(raw_index = index, new_index = -1)
        return {index_pair}

    def collect_external_symbol_states(self, frame, stmt_id, stmt, symbol_id, summary_template: MethodSummaryTemplate, old_key_state_indexes: set):
        """
        收集外部符号的状态索引。
        返回状态索引集合。
        """
        return_indexes = set()
        if symbol_id in summary_template.key_dynamic_content:
            return old_key_state_indexes

        for index_pair in summary_template.used_external_symbols[symbol_id]:
            each_state_index = index_pair.raw_index
            return_indexes.add(each_state_index)
        return return_indexes

    def complete_in_states_and_check_continue_flag(self, stmt_id, frame: ComputeFrame, stmt, status, in_states, method_summary: MethodSummaryTemplate):
        """
        完成in_states的更新，并检查是否需要继续分析。
        返回是否继续分析的标记。
        """
        # print("@in_states before", in_states)
        if stmt.operation == "parameter_decl":
            return True
        if stmt_id not in frame.symbol_changed_stmts:
            return False

        if (
            frame.stmt_counters[stmt_id] >= config.MAX_STMT_STATE_ANALYSIS_ROUND or
            stmt_id in frame.loop_total_rounds and frame.stmt_counters[stmt_id] >= frame.loop_total_rounds[stmt_id]
        ):
            return False

        dynamic_call_stmt: set = method_summary.dynamic_call_stmt
        change_flag = False
        if (
            self.phase_name == AnalysisPhaseName.SemanticSummaryGeneration and
            frame.stmt_counters[stmt_id] == config.FIRST_ROUND
        ):
            change_flag = True

        if stmt_id in frame.loop_total_rounds and frame.stmt_counters[stmt_id] < frame.loop_total_rounds[stmt_id]:
            change_flag = True

        if stmt_id in dynamic_call_stmt and frame.stmt_counters[stmt_id] == config.FIRST_ROUND:
            change_flag = True

        for used_symbol_index in status.used_symbols + status.implicitly_used_symbols:
            from_external = True
            used_symbol = frame.symbol_state_space[used_symbol_index]
            if not isinstance(used_symbol, Symbol):
                continue

            symbol_id = used_symbol.symbol_id
            # locals
            if symbol_id in in_states:
                from_external = False
                if not change_flag:
                    if used_symbol.states != in_states[symbol_id]:
                        change_flag = True

                used_symbol.states = in_states[symbol_id]
                # from parameters/loacls & key_dynamic_content
                # only when symbol_id in in_states is key_dynamic and is in dynamic_call and is FIRST_ROUND
                if(
                    symbol_id not in method_summary.key_dynamic_content or
                    frame.stmt_counters[stmt_id] > config.FIRST_ROUND or
                    stmt_id not in dynamic_call_stmt
                ):
                    continue

            # holds symbol_id in frame.method_def_use_summary.used_external_symbol_ids:
            # externals
            # first encounter
            elif symbol_id not in method_summary.used_external_symbols:
                # print(f"{symbol_id} not in method_summary.used_external_symbols")
                if(
                    symbol_id in frame.method_def_use_summary.used_external_symbol_ids or
                    symbol_id in frame.method_def_use_summary.used_this_symbol_id or
                    stmt_id in dynamic_call_stmt
                ):
                    # print(f"{symbol_id} goes into generate_external_symbol_states")
                    new_state_indexes = self.generate_external_symbol_states(frame, stmt_id, symbol_id, used_symbol, method_summary)
                    method_summary.used_external_symbols[symbol_id] = new_state_indexes

                else:
                    continue

            # from externals & key_dynamic_content
            old_key_state_indexes = used_symbol.states
            # print(f"{symbol_id} symbol中的states:",used_symbol.states)
            # print("\n打印method_summary",method_summary.key_dynamic_content)
            current_states = set()
            if util.is_empty(old_key_state_indexes):
                # 如果第二阶段碰到一个来自外部的symbol，并且进行了一些关键操作，比如field_read a.f，其中a是external_symbol。那就会把a加入到key_dynamic_content中
                # method_summary.key_dynamic_content是在tag_key_state方法中添加的
                if symbol_id in method_summary.key_dynamic_content and from_external:
                    # print(f"symbol_id {symbol_id} in method_summary.key_dynamic_content and from_external")
                    for index_pair in method_summary.key_dynamic_content[symbol_id]:
                        old_key_state_indexes.add(index_pair.raw_index)

                # print("收集到的old_key_state_indexes是", old_key_state_indexes)
                current_states = self.collect_external_symbol_states(
                    frame, stmt_id, stmt, symbol_id, method_summary, old_key_state_indexes
                )
            else:
                # 如果能直接从in_symbol中获取，就直接用
                current_states = old_key_state_indexes

            # print("收集到的current_States是", current_states)
            if util.is_empty(current_states):
                continue

            if used_symbol.states != current_states:
                used_symbol.states = current_states
                change_flag = True
            in_states[symbol_id] = current_states

        # print("@in_states before", in_states)
        return change_flag

    def get_next_stmts_for_state_analysis(self, stmt_id, symbol_graph):
        """
        获取后续需要分析的状态相关语句。
        返回后继语句的集合。
        """
        if not symbol_graph.has_node(stmt_id):
            return set()

        results = set()
        for tmp_id in util.graph_successors(symbol_graph, stmt_id):
            for tmp_stmt in util.graph_successors(symbol_graph, tmp_id):
                results.add(tmp_stmt)

        return results

    def unset_states_of_status(self, stmt_id, frame: ComputeFrame, status: StmtStatus):
        """
        重置状态定义相关的状态集合。
        """
        status.defined_states = set()

    def unset_states_of_defined_symbol(self, stmt_id, frame: ComputeFrame, status: StmtStatus):
        """
        重置定义符号的状态集合。
        """
        defined_symbol = frame.symbol_state_space[status.defined_symbol]
        if defined_symbol:
            defined_symbol.states = set()
        status.implicitly_defined_symbols = []

    def restore_states_of_defined_symbol_and_status(
        self, stmt_id, frame: ComputeFrame, status: StmtStatus, old_defined_symbol_states, old_implicitly_defined_symbols, old_status_defined_states
    ):
        """
        恢复符号和状态定义的原始状态（用于回滚操作）。
        """
        defined_symbol = frame.symbol_state_space[status.defined_symbol]
        if defined_symbol:
            defined_symbol.states = old_defined_symbol_states
        status.implicitly_defined_symbols = old_implicitly_defined_symbols
        status.defined_states = old_status_defined_states

    def check_outdated_state_indexes(self, status, frame: ComputeFrame):
        """
        检查过时的状态索引集合。
        返回需要更新的状态索引。
        """
        outdated_state_indexes = set()
        for defined_symbol_index in [status.defined_symbol, *status.implicitly_defined_symbols]:
            defined_symbol = frame.symbol_state_space[defined_symbol_index]
            if defined_symbol:
                for each_state_index in defined_symbol.states:
                    if frame.state_bit_vector_manager.exist_state_index(each_state_index):
                        outdated_state_indexes.add(each_state_index)
        return outdated_state_indexes

    def adjust_computation_results(self, stmt_id, frame, status: StmtStatus, old_index_ceiling):
        """
        一条语句处理完后，将该语句的所有defined_symbol.states和status.defined_states更新到最新版本。
        """
        available_state_defs = frame.state_bit_vector_manager.explain(status.in_state_bits)
        for defined_symbol_index in [status.defined_symbol, *status.implicitly_defined_symbols]:
            defined_symbol = frame.symbol_state_space[defined_symbol_index]
            if not isinstance(defined_symbol, Symbol):
                continue
            adjusted_states = self.resolver.collect_newest_states_by_state_indexes(
                frame, stmt_id, defined_symbol.states, available_state_defs, old_index_ceiling
            )
            # if config.DEBUG_FLAG:
            #     print(f"\ndefined_symbol: {defined_symbol.name} {defined_symbol.symbol_id}")
            #     print(f"defined_symbol.states: {defined_symbol.states}")
            #     print(f"adjusted_states: {adjusted_states}")
            defined_symbol.states = adjusted_states

        adjusted_states = self.resolver.collect_newest_states_by_state_indexes(
            frame, stmt_id, status.defined_states, available_state_defs, old_index_ceiling
        )
        # if config.DEBUG_FLAG:
        #     print(f"status.defined_states: {status.defined_states}")
        #     print(f"adjusted_states: {adjusted_states}")
        status.defined_states = adjusted_states

    def compute_states(self, stmt_id, stmt, frame: ComputeFrame):
        """
        执行状态计算的核心逻辑：
        1. 收集输入状态
        2. 完成状态传播
        3. 执行具体语句的状态计算
        返回结果标志（状态变化/中断等）
        """
        status = frame.stmt_id_to_status[stmt_id]
        in_states = {}
        symbol_graph = frame.symbol_graph.graph

        if not symbol_graph.has_node(stmt_id):
            return P2ResultFlag()

        # 收集输入状态位
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
        # 收集输入状态
        # collect in state

        in_symbols = self.generate_in_symbols(stmt_id, frame, status, symbol_graph)
        # print(f"in_symbols: {in_symbols}")
        in_states = self.group_used_states(stmt_id, in_symbols, frame, status)
        # print(f"in_states@before complete_in_states: {in_states}")
        method_summary = frame.method_summary_template
        continue_flag = self.complete_in_states_and_check_continue_flag(stmt_id, frame, stmt, status, in_states, method_summary)
        # print(f"in_states@after complete_in_states: {in_states}")
        if not continue_flag:
            print("  DON'T CONTINUE")
            if status.in_state_bits != old_in_state_bits:
                status.out_state_bits = status.in_state_bits
            self.restore_states_of_defined_symbol_and_status(stmt_id, frame, status, old_defined_symbol_states, old_implicitly_defined_symbols, old_status_defined_states)
            return P2ResultFlag()

        self.unset_states_of_defined_symbol(stmt_id, frame, status)
        change_flag: P2ResultFlag = frame.stmt_state_analysis.compute_stmt_state(stmt_id, stmt, status, in_states)
        if change_flag is None:
            print(f"  NO CHANGE")
            change_flag = P2ResultFlag()

        self.adjust_computation_results(stmt_id, frame, status, old_index_ceiling)
        new_out_states = self.update_out_states(stmt_id, frame, status, old_index_ceiling)

        self.collect_def_states_amount_each_stmt(stmt_id, len(new_out_states),in_states)

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

    def group_states_with_state_ids(self, frame: ComputeFrame, state_indexes: set):
        """
        给定一组state_indexes集合，输出{state_id:states}的映射
        """
        state_id_to_indexes = {}
        space = frame.symbol_state_space
        for index in state_indexes:
            if not isinstance(state := space[index], State):
                continue
            state_id = state.state_id
            util.add_to_dict_with_default_set(state_id_to_indexes, state_id, index)
        # print("group_states_with_state_ids@ state_id_to_indexes",state_id_to_indexes)
        return state_id_to_indexes


    def update_method_def_use_summary(self, stmt_id, frame: ComputeFrame):
        """
        更新方法的def-use摘要信息。
        处理隐式定义/使用符号的记录。
        """
        summary = frame.method_def_use_summary
        status = frame.stmt_id_to_status[stmt_id]
        for implicitly_defined_symbols_index in status.implicitly_defined_symbols:
            implicitly_defined_symbol = frame.symbol_state_space[implicitly_defined_symbols_index]
            if not isinstance(implicitly_defined_symbol, Symbol):
                continue
            symbol_id = implicitly_defined_symbol.symbol_id
            if symbol_id in frame.all_local_symbol_ids:
                continue
            # only keyword global and nonlocal symbol can be added in defined_external_symbol_ids in python
            # summary.defined_external_symbol_ids.add(symbol_id)

        for symbol_id in status.implicitly_used_symbols:
            if symbol_id in frame.all_local_symbol_ids:
                continue
            summary.used_external_symbol_ids.add(symbol_id)

    def save_analysis_summary_and_space(self, frame: ComputeFrame, method_summary: MethodSummaryTemplate, compact_space: SymbolStateSpace):
        """
        保存方法的分析摘要和压缩后的状态空间。
        """
        self.loader.save_symbol_state_space_summary_p2(frame.method_id, compact_space)
        self.loader.save_method_summary_template(frame.method_id, method_summary)

    def generate_and_save_analysis_summary(self, frame: ComputeFrame, method_summary: MethodSummaryTemplate):
        """
        生成并保存完整的方法分析摘要：
        1. 处理返回值状态
        2. 更新符号到状态的映射
        3. 保存压缩后的状态空间
        """
        # print(f"生成方法{frame.method_id}的summary")
        def_use_summary = frame.method_def_use_summary
        if util.is_empty(def_use_summary):
            return

        symbol_state_space = frame.symbol_state_space

        basic_target_symbol_ids = set()
        for each_id_set in (
            {pair[0] for pair in def_use_summary.parameter_symbol_ids}, # 只取每个二元组的前一个元素
            def_use_summary.defined_this_symbol_id,
            # def_use_summary.used_external_symbol_ids,
            def_use_summary.defined_external_symbol_ids,
        ):
            basic_target_symbol_ids.update(each_id_set)

        all_indexes = set()

        for stmt_id in util.find_cfg_last_nodes(frame.cfg):
            # all_newest_states_indexes = set()
            stmt = frame.stmt_id_to_stmt[stmt_id]
            status = frame.stmt_id_to_status[stmt_id]
            current_symbol_bits = status.out_symbol_bits
            current_state_bits = status.out_state_bits

            # obtain target symbol_ids
            returned_states = set()
            current_symbol_ids = basic_target_symbol_ids.copy()
            if stmt.operation in RETURN_STMT_OPERATION and len(status.used_symbols) != 0: # 说明该语句有return_symbol
                returned_symbol_index = status.used_symbols[0]
                returned_symbol = symbol_state_space[returned_symbol_index]
                if isinstance(returned_symbol, Symbol):
                    returned_states.update(returned_symbol.states)
                else:
                    returned_states.add(returned_symbol_index)

            # get current out_bits from return_stmt_id
            available_defined_symbols = frame.symbol_bit_vector_manager.explain(current_symbol_bits) # 收集到当前last_stmt中所有可用last_symbol_def
            available_defined_states = frame.state_bit_vector_manager.explain(current_state_bits)
            # find symbol_ids' states
            old_states = set()
            symbol_id_to_old_state_indexes= {}
            for symbol_def_node in available_defined_symbols:
                symbol_id = symbol_def_node.symbol_id
                if symbol_id in current_symbol_ids: # 说明是我们需要放到summary中去的symbol
                     symbol = symbol_state_space[symbol_def_node.index]
                     # get old_states
                     util.add_to_dict_with_default_set(symbol_id_to_old_state_indexes, symbol_id, symbol.states)

            # 统一更新所有小弟
            state_index_old_to_new = {}
            symbol_id_to_latest_state_indexes = {}
            for symbol_id in symbol_id_to_old_state_indexes:
                old_states = symbol_id_to_old_state_indexes[symbol_id]
                latest_states = self.resolver.retrieve_latest_states(frame, stmt_id, symbol_state_space, old_states, available_defined_states, state_index_old_to_new)
                # 将latest_states中所有state_id相同的states进行合并成一个state,避免summary中保存的state过多。
                state_id_to_indexes = self.group_states_with_state_ids(frame, latest_states)
                fusion_states = set()
                for state_id, states_with_same_id in state_id_to_indexes.items():
                    if (len(states_with_same_id) > 1):
                        fusion_state = frame.stmt_state_analysis.fuse_states_to_one_state(states_with_same_id, stmt_id, status)
                        fusion_states.update(fusion_state)
                    else:
                        fusion_states.update(states_with_same_id)
                symbol_id_to_latest_state_indexes[symbol_id] = fusion_states

            # 补充defined_external_symbol_ids的情况，因为defined_external_symbol_ids在frame里没有symbol_def_node
            for symbol_id in def_use_summary.defined_external_symbol_ids:
                state_index = frame.external_symbol_id_to_initial_state_index.get(symbol_id, None)
                if state_index:
                    latest_states = self.resolver.retrieve_latest_states(frame, stmt_id, symbol_state_space, {state_index}, available_defined_states, state_index_old_to_new)
                    state_id_to_indexes = self.group_states_with_state_ids(frame, latest_states)
                    fusion_states = set()
                    for state_id, states_with_same_id in state_id_to_indexes.items():
                        if (len(states_with_same_id) > 1):
                            fusion_state = frame.stmt_state_analysis.fuse_states_to_one_state(states_with_same_id, stmt_id, status)
                            fusion_states.update(fusion_state)
                        else:
                           fusion_states.update(states_with_same_id)
                    symbol_id_to_latest_state_indexes[symbol_id] = fusion_states

            # print("generate_and_save_analysis_summary@ symbol_id_to_latest_state_indexes: ")
            # pprint.pprint(symbol_id_to_latest_state_indexes)
            # save results
            lines_to_be_updated = (
                (def_use_summary.parameter_symbol_ids,          method_summary.parameter_symbols),
                # (def_use_summary.used_external_symbol_ids,      method_summary.used_external_symbols),
                (def_use_summary.defined_external_symbol_ids,   method_summary.defined_external_symbols),
                # (def_use_summary.return_symbol_ids,             method_summary.return_symbols),
                # (returned_symbol_id,                            method_summary.return_symbols),
                (set(),                                         method_summary.key_dynamic_content),
                (def_use_summary.defined_this_symbol_id,        method_summary.this_symbols),
            )
            # 逐条语句添加
            for summary_ids, content_record in lines_to_be_updated:
                for symbol_id in content_record:
                    state_index_pair_set = content_record[symbol_id]
                    for state_index_pair in state_index_pair_set:
                        all_indexes.add(state_index_pair.raw_index)

                for symbol_id in summary_ids:
                    default_value_symbol_id = -1
                    if isinstance(symbol_id, (int, numpy.int64)):
                        default_value_symbol_id = -1
                    # only parameter_symbol_id may have a default_value_symbol_id
                    elif isinstance(symbol_id, tuple):
                        symbol_id = symbol_id[0]
                        #default_value_symbol_id = symbol_id[1]

                    if symbol_id in symbol_id_to_latest_state_indexes:
                        state_indexes = symbol_id_to_latest_state_indexes[symbol_id]
                        for each_state_index in state_indexes:
                            util.add_to_dict_with_default_set(
                                content_record,
                                symbol_id,
                                IndexMapInSummary(
                                    raw_index = each_state_index,
                                    new_index = -1,
                                    default_value_symbol_id = default_value_symbol_id
                                )
                            )
                            all_indexes.add(each_state_index)

            # 处理return
            new_return_states = self.resolver.retrieve_latest_states(frame, stmt_id, symbol_state_space, returned_states, available_defined_states, state_index_old_to_new)

            if new_return_states:
                for each_return_state in new_return_states:
                    util.add_to_dict_with_default_set(
                        method_summary.return_symbols,
                        SUMMARY_GENERAL_SYMBOL_ID.RETURN_SYMBOL_ID,
                        IndexMapInSummary(
                            raw_index = each_return_state,
                            new_index = -1,
                            default_value_symbol_id = -1
                        )
                    )
                    all_indexes.add(each_return_state)

        method_summary.external_symbol_to_state = frame.external_symbol_id_to_initial_state_index
        # save space
        compact_space = frame.symbol_state_space.extract_related_elements_to_new_space(all_indexes)
        # adjust ids and save summary template
        method_summary.adjust_ids(compact_space.old_index_to_new_index)
        # print(compact_space)
        self.save_analysis_summary_and_space(frame, method_summary, compact_space)
        # print(f"dynamic_call_stmt: {frame.method_summary_template.dynamic_call_stmt}")

    def analyze_stmts(self, frame: ComputeFrame):
        """
        执行语句级别的分析循环：
        1. 处理工作列表中的语句
        2. 触发中断处理（如调用未分析方法）
        3. 更新符号图和def-use信息
        """
        while len(frame.stmt_worklist) != 0:
            stmt_id = frame.stmt_worklist.peek()
            # print(f"当前语句id是{stmt_id}, stmt_worklist:",frame.stmt_worklist)
            if stmt_id <= 0 or stmt_id not in frame.stmt_counters:
                frame.stmt_worklist.pop()
                continue

            stmt = frame.stmt_id_to_stmt.get(stmt_id)
            if stmt_id in frame.loop_total_rounds:
                if frame.stmt_counters[stmt_id] <= frame.loop_total_rounds[stmt_id]:
                    frame.stmt_worklist.add(util.graph_successors(frame.cfg, stmt_id))
                    frame.symbol_changed_stmts.add(stmt_id)
            else:
                if frame.stmt_counters[stmt_id] < config.MAX_STMT_STATE_ANALYSIS_ROUND:
                    frame.stmt_worklist.add(util.graph_successors(frame.cfg, stmt_id))
                    # print("添加cfg后继",list(util.graph_successors(frame.cfg, stmt_id)))

            if config.DEBUG_FLAG:
                util.debug(f"-----analyzing stmt <{stmt_id}> of method <{frame.method_id}>-----")
                # print("gir2: ",self.loader.load_stmt_gir(stmt_id))

            if frame.interruption_flag:
                frame.interruption_flag = False
            else:
                # compute in/out bits
                self.analyze_reaching_symbols(stmt_id, stmt, frame)

            # according to symbol_graph, compute the state flow of current statement
            result_flag = self.compute_states(stmt_id, stmt, frame)
            frame.symbol_changed_stmts.remove(stmt_id)
            # check if interruption is enabled
            if result_flag.interruption_flag:
                return result_flag

            # re-analyze def/use
            if result_flag.def_changed or result_flag.use_changed:
                # change out_bit to reflect implicitly_defined_symbols
                self.rerun_analyze_reaching_symbols(stmt_id, frame, result_flag)
                # update method def/use
                self.update_method_def_use_summary(stmt_id, frame)

            # move to the next statement
            frame.stmt_counters[stmt_id] += 1

            # global stmt_counts
            # stmt_counts += 1
            # if stmt_counts % 2000 == 0:
                # print(f"第{stmt_counts/2000}轮打印stmt_states情况")
                # self.print_count_stmt_def_states()

            frame.stmt_worklist.pop()

    def analyze_method(self, method_id):
        """
        分析单个方法的完整流程：
        1. 初始化计算帧
        2. 执行状态分析循环
        3. 保存分析结果
        4. 处理方法调用中断
        """
        current_frame = ComputeFrame(method_id=method_id, loader = self.loader)
        frame_stack = ComputeFrameStack().add(current_frame)
        while len(frame_stack) != 0:
            frame = frame_stack.peek()
            if config.DEBUG_FLAG:
                util.debug(f"\n\tPhase II Analysis is in progress <method {frame.method_id}> \n")

            if not frame.has_been_inited:
                if self.init_compute_frame(frame, frame_stack) is None:
                    self.analyzed_method_list.add(frame.method_id)
                    frame_stack.pop()
                    continue
            result: P2ResultFlag = self.analyze_stmts(frame)
            if result is not None and result.interruption_flag and result.interruption_data:
                # here an interruption is faced
                # create a new frame and add it to the stack
                frame.interruption_flag = True
                data:InterruptionData = result.interruption_data
                if config.DEBUG_FLAG:
                    util.debug(f"Interruption unsolved_callee_ids: {data.callee_ids}")
                if len(data.callee_ids) != 0:
                    frame.symbol_changed_stmts.add(data.call_stmt_id)
                    for callee_id in data.callee_ids:
                        if callee_id not in self.analyzed_method_list:
                            new_frame = ComputeFrame(
                                method_id = callee_id,
                                caller_id = data.caller_id,
                                call_stmt_id = data.call_stmt_id,
                                loader = self.loader
                            )
                            frame_stack.add(new_frame)
                # new_frame = ComputeFrame(method_id = data.method_id, caller_id = data.caller_id, call_stmt_id = data.call_stmt_id, loader = self.loader)
                # frame_stack.add(new_frame)
                continue

            # Current frame is done, pop it
            # save the result
            self.analyzed_method_list.add(frame.method_id)
            self.generate_and_save_analysis_summary(frame, frame.method_summary_template)

            self.loader.save_stmt_status_p2(frame.method_id, frame.stmt_id_to_status)
            self.loader.save_symbol_bit_vector_p2(frame.method_id, frame.symbol_bit_vector_manager)
            self.loader.save_state_bit_vector_p2(frame.method_id, frame.state_bit_vector_manager)
            self.loader.save_symbol_state_space_p2(frame.method_id, frame.symbol_state_space)
            self.loader.save_method_symbol_graph_p2(frame.method_id, frame.symbol_graph.graph)
            self.loader.save_method_symbol_to_define_p2(frame.method_id, frame.symbol_to_define)
            self.loader.save_method_state_to_define_p2(frame.method_id, frame.state_to_define)
            self.loader.save_method_def_use_summary(frame.method_id, frame.method_def_use_summary)
            frame_stack.pop()

    def sort_methods_by_unit_id(self, methods):
        """
        按单元ID对方法进行排序。
        返回排序后的方法列表。
        """
        return sorted(list(methods), key=lambda method: self.loader.convert_method_id_to_unit_id(method))

    def reversed_methods_by_unit_id(self, methods):
        return reversed(self.sort_methods_by_unit_id(methods))

    def collect_def_states_amount_each_stmt(self, stmt_id, new_out_states_len, in_states):
        stmt = self.loader.load_stmt_gir(stmt_id)
        op = stmt.operation

        if stmt_id not in self.count_stmt_def_states:
            self.count_stmt_def_states[stmt_id] = CountStmtDefStateNode(stmt_id, op, in_states)
        self.count_stmt_def_states[stmt_id].add_new_states_count(new_out_states_len)

        if op not in self.count_stmt_op_def_states:
            self.count_stmt_op_def_states[op] = 0
        self.count_stmt_op_def_states[op] += new_out_states_len


    def print_count_stmt_def_states(self):
        """
        打印summary_generation阶段，每条语句产生的new_out_states数量，倒序排列
        """
        print("统计产生的new_out_states的数量——————￥￥￥￥￥￥￥￥￥￥￥￥")
        filtered_stmts_nodes = [node for node in self.count_stmt_def_states.values() if node.new_out_states_len >= 5]
        sorted_stmts_nodes = sorted(filtered_stmts_nodes, key=lambda x: x.new_out_states_len, reverse=True)
        counter = 0
        for node in sorted_stmts_nodes:
            # node.print_as_beautiful_dict()
            if counter >= 20:
                break
            counter+=1
            node.print_as_dict()

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

        sorted_ops = sorted(self.count_stmt_op_def_states.items(), key=lambda x: x[1], reverse=True)
        counter = 0
        for each_op in sorted_ops:
            if counter >= 20:
                break
            counter+=1
            print(each_op)

    def run(self):
        """
        执行语义摘要生成的主流程：
        1. 遍历所有方法分组
        2. 调用单个方法分析
        3. 保存全局调用图和最终结果
        """
        if config.DEBUG_FLAG:
            util.debug("\n\t------------------------------------------------\n"
                       "\t~~~~~~~~ Phase II analysis is ongoing ~~~~~~~~~\n"
                       "\t------------------------------------------------\n")

        # analyze all methods
        grouped_methods:SimplyGroupedMethodTypes = self.loader.load_grouped_methods()
        for method_id in grouped_methods.get_all_method_list():
            if method_id not in self.analyzed_method_list:
                self.analyze_method(method_id)

        # save all results here
        self.loader.save_call_graph_p2(self.call_graph)
        self.loader.export()
        # self.print_count_stmt_def_states()

        return self
