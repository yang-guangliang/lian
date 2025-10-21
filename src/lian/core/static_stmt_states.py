#!/usr/bin/env python3
import ast
import pprint
import re
import copy

from lian.events.handler_template import EventData
from lian.util import util
from lian.config import config, type_table
from lian.util.loader import Loader
# from lian.events.handler_template import AppTemplate
from lian.config.constants import (
    CONDITION_STMT_PATH_FLAG,
    LIAN_SYMBOL_KIND,
    LIAN_INTERNAL,
    STATE_TYPE_KIND,
    LIAN_INTERNAL,
    CALLEE_TYPE,
    EVENT_KIND,
    SYMBOL_OR_STATE,
    ACCESS_POINT_KIND,
    ANALYSIS_PHASE_ID
)
import lian.events.event_return as er
from lian.common_structs import (
    MethodDeclParameters,
    Parameter,
    Argument,
    MethodCallArguments,
    StateDefNode,
    StmtStatus,
    Symbol,
    State,
    CallGraph,
    AccessPoint,
    MethodCall,
    ComputeFrameStack,
    ComputeFrame,
    MethodSummaryTemplate,
    MethodDefUseSummary,
    SymbolDefNode,
    SymbolStateSpace,
    SimpleWorkList,
    P2ResultFlag,
    MethodCallArguments,
    InterruptionData,
    ParameterMapping,
    PathManager,
    UnionFind,
    IndexMapInSummary
)
from lian.core.resolver import Resolver

class StaticStmtStates:
    def __init__(
            self, analysis_phase_id, event_manager, loader: Loader, resolver: Resolver,
            compute_frame: ComputeFrame, call_graph: CallGraph, analyzed_method_list = []
    ):
        """
        初始化语句状态分析上下文：
        1. 注册核心组件（加载器、解析器、计算帧等）
        2. 初始化状态处理器映射表
        3. 准备符号状态空间和定义集合
        """
        self.event_manager = event_manager
        self.loader = loader
        self.resolver: Resolver = resolver
        self.frame: ComputeFrame = compute_frame
        self.frame_stack: ComputeFrameStack = compute_frame.frame_stack
        self.call_graph = call_graph
        self.analyzed_method_list = analyzed_method_list
        self.unit_id = self.frame.unit_id
        self.lang = self.frame.lang
        self.analysis_phase_id = analysis_phase_id
        self.sfg = self.frame.state_flow_graph

        self.state_analysis_handlers = {
            "comment_stmt"                          : self.regular_stmt_state,
            "package_stmt"                          : self.regular_stmt_state,
            "echo_stmt"                             : self.regular_stmt_state,
            "exit_stmt"                             : self.regular_stmt_state,
            "return_stmt"                           : self.regular_stmt_state,
            "yield_stmt"                            : self.regular_stmt_state,
            "sync_stmt"                             : self.regular_stmt_state,
            "label_stmt"                            : self.regular_stmt_state,
            "throw_stmt"                            : self.regular_stmt_state,
            "try_stmt"                              : self.regular_stmt_state,
            "catch_stmt"                            : self.regular_stmt_state,
            "asm_stmt"                              : self.regular_stmt_state,
            "assert_stmt"                           : self.regular_stmt_state,
            "pass_stmt"                             : self.regular_stmt_state,
            "with_stmt"                             : self.regular_stmt_state,
            "await_stmt"                            : self.regular_stmt_state,
            "catch_clause"                          : self.regular_stmt_state,
            "unsafe_block"                          : self.regular_stmt_state,

            "if_stmt"                               : self.control_flow_stmt_state,
            "dowhile_stmt"                          : self.control_flow_stmt_state,
            "while_stmt"                            : self.control_flow_stmt_state,
            "for_stmt"                              : self.control_flow_stmt_state,
            "switch_stmt"                           : self.control_flow_stmt_state,
            "case_stmt"                             : self.control_flow_stmt_state,
            "default_stmt"                          : self.control_flow_stmt_state,
            "switch_type_stmt"                      : self.control_flow_stmt_state,
            "break_stmt"                            : self.control_flow_stmt_state,
            "continue_stmt"                         : self.control_flow_stmt_state,
            "goto_stmt"                             : self.control_flow_stmt_state,
            "block"                                 : self.control_flow_stmt_state,
            "block_start"                           : self.control_flow_stmt_state,

            "forin_stmt"                            : self.forin_stmt_state,
            "for_value_stmt"                        : self.for_value_stmt_state,

            "import_stmt"                           : self.import_stmt_state,
            "from_import_stmt"                      : self.from_import_stmt_state,
            "export_stmt"                           : self.export_stmt_state,
            "export_from_stmt"                      : self.export_from_stmt_state,
            "require_stmt"                          : self.require_stmt_state,

            "assign_stmt"                           : self.assign_stmt_state,
            "call_stmt"                             : self.call_stmt_state,
            "global_stmt"                           : self.global_stmt_state,
            "nonlocal_stmt"                         : self.nonlocal_stmt_state,
            "type_cast_stmt"                        : self.type_cast_stmt_state,
            "type_alias_decl"                       : self.type_alias_decl_state,
            "phi_stmt"                              : self.phi_stmt_state,

            "namespace_decl"                        : self.namespace_decl_stmt_state,
            "class_decl"                            : self.class_decl_stmt_state,
            "record_decl"                           : self.class_decl_stmt_state,
            "interface_decl"                        : self.class_decl_stmt_state,
            "enum_decl"                             : self.class_decl_stmt_state,
            "struct_decl"                           : self.class_decl_stmt_state,
            "enum_constants"                        : self.regular_stmt_state,
            "annotation_type_decl"                  : self.regular_stmt_state,
            "annotation_type_elements_decl"         : self.regular_stmt_state,

            "parameter_decl"                        : self.parameter_decl_stmt_state,
            "variable_decl"                         : self.variable_decl_stmt_state,
            "method_decl"                           : self.method_decl_stmt_state,

            "new_array"                             : self.new_array_stmt_state,
            "new_object"                            : self.new_object_stmt_state,
            "new_record"                            : self.new_record_stmt_state,
            "new_set"                               : self.new_set_stmt_state,
            "new_struct"                            : self.new_object_stmt_state,

            "addr_of"                               : self.addr_of_stmt_state,
            "mem_read"                              : self.mem_read_stmt_state,
            "mem_write"                             : self.mem_write_stmt_state,
            "array_write"                           : self.common_element_write_stmt_state,
            "array_read"                            : self.common_element_read_stmt_state,
            "array_insert"                          : self.array_insert_stmt_state,
            "array_append"                          : self.array_append_stmt_state,
            "array_extend"                          : self.array_extend_stmt_state,
            "record_extend"                         : self.record_extend_stmt_state,
            "record_write"                          : self.field_write_stmt_state,
            "field_write"                           : self.field_write_stmt_state,
            "field_read"                            : self.field_read_stmt_state,
            "field_addr"                            : self.field_addr_stmt_state,
            "slice_write"                           : self.slice_write_stmt_state,
            "slice_read"                            : self.slice_read_stmt_state,
            "del_stmt"                              : self.del_stmt_state,
            "unset_stmt"                            : self.unset_stmt_state,
        }

    def copy_and_extend_access_path(self, original_access_path, access_point):
        """
        扩展访问路径：
        1. 复制原始访问路径
        2. 追加新的访问点
        3. 返回扩展后的路径
        """
        new_path: list = original_access_path.copy()
        new_path.append(access_point)
        return new_path

    def make_state_tangping(self, new_state):
        """
        标记状态为tangping：
        1. 设置tangping标志
        2. 合并数组元素到tangping集合
        3. 清空原数组和字段集合
        """
        new_state.tangping_flag = True
        for each_array in new_state.array:
            new_state.tangping_elements.update(each_array)
        for each_field in new_state.fields.values():
            new_state.tangping_elements.update(each_field)
        new_state.array = []
        new_state.fields = {}

    def is_state_a_class_decl(self, state):
        """
        判断状态是否为类声明：
        1. 检查状态数据类型
        2. 验证符号是否为类声明
        """
        if state.data_type == LIAN_INTERNAL.CLASS_DECL:
            return True
        if self.loader.is_class_decl(state.value):
            return True
        return False

    def is_state_a_unit(self, state):
        if state.data_type == LIAN_INTERNAL.UNIT:
            return True

    def is_state_a_method_decl(self, state):
        """
        判断状态是否为方法声明：
        1. 检查状态数据类型
        2. 验证符号是否为方法声明
        """
        if state.data_type == LIAN_INTERNAL.METHOD_DECL:
            return True
        if self.loader.is_method_decl(state.value):
            return True
        return False

    def is_first_round(self, stmt_id):
        return self.frame.stmt_counters[stmt_id] == 0

    def create_state_and_add_space(
            self, status: StmtStatus, stmt_id, source_symbol_id = -1, source_state_id = -1, value = "", data_type = "",
            state_type = STATE_TYPE_KIND.REGULAR, access_path = [], overwritten_flag = False
    ):
        """
        创建新状态并加入符号空间：
        1. 构造State对象
        2. 添加至符号状态空间
        3. 更新状态定义集合
        4. 处理外部符号关联
        """
        item = State(
            stmt_id = stmt_id,
            value = value,
            source_symbol_id = source_symbol_id,
            source_state_id = source_state_id,
            data_type = str(data_type),
            state_type = state_type,
            access_path = access_path,
            fields = {},
            array = []
        )

        index = self.frame.symbol_state_space.add(item)
        state_def_node = StateDefNode(index=index, state_id=item.state_id, stmt_id=stmt_id)
        util.add_to_dict_with_default_set(
            self.frame.defined_states,
            item.state_id,
            state_def_node
        )

        # if state_def_node not in self.frame.all_state_defs:
        #     self.frame.state_bit_vector_manager.add_bit_id(state_def_node)
        #     self.frame.all_state_defs.add(state_def_node)
        # status.defined_states.add(index)

        # 如果新建的state是基于我们在generate_external_state里手动给的state，说明该symbol也被我们define了，需添加到define集合中
        if overwritten_flag and source_state_id in self.frame.initial_state_to_external_symbol:
            symbol_id = self.frame.initial_state_to_external_symbol[source_state_id]
            if symbol_id != self.frame.method_def_use_summary.this_symbol_id:
                self.frame.method_def_use_summary.defined_external_symbol_ids.add(symbol_id)
        return index

    def create_copy_of_state_and_add_space(self, status: StmtStatus, stmt_id, state_index, overwritten_flag = False):
        """复制已有状态并添加到状态空间，更新相关定义信息"""
        state = self.frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            return -1
        new_state = state.copy(stmt_id)
        index = self.frame.symbol_state_space.add(new_state)
        state_id = state.state_id
        if state_id != -1:
            state_def_node = StateDefNode(index=index, state_id=state_id, stmt_id=stmt_id)
            util.add_to_dict_with_default_set(
                self.frame.defined_states,
                state_id,
                state_def_node
            )
            if state_def_node not in self.frame.all_state_defs:
                self.frame.state_bit_vector_manager.add_bit_id(state_def_node)
                self.frame.all_state_defs.add(state_def_node)

        status.defined_states.discard(state_index)
        status.defined_states.add(index)

        if overwritten_flag and state.source_state_id in self.frame.initial_state_to_external_symbol:
            symbol_id = self.frame.initial_state_to_external_symbol[state.source_state_id]
            if symbol_id != self.frame.method_def_use_summary.this_symbol_id:
                self.frame.method_def_use_summary.defined_external_symbol_ids.add(symbol_id)
        return index

    def create_copy_of_symbol_and_add_space(self, status:StmtStatus, stmt_id, symbol: Symbol):
        """复制符号并添加到符号空间，更新相关定义信息"""
        new_symbol = symbol.copy(stmt_id)
        new_symbol_index = self.frame.symbol_state_space.add(new_symbol)

        util.add_to_dict_with_default_set(
            self.frame.defined_symbols,
            new_symbol.symbol_id,
            SymbolDefNode(
                index=new_symbol_index, symbol_id=new_symbol.symbol_id, stmt_id=stmt_id
            )
        )
        status.implicitly_defined_symbols.append(new_symbol_index)

        return new_symbol_index

    def create_unsolved_state_and_update_symbol(
        self, status, stmt_id, receiver_symbol, data_type = "", state_type = STATE_TYPE_KIND.UNSOLVED
    ):
        """创建未解决状态并更新关联符号的状态集合"""
        if isinstance(receiver_symbol, Symbol):
            index = self.create_state_and_add_space(
                status, stmt_id, receiver_symbol.symbol_id, data_type = data_type, state_type = state_type
            )
            receiver_symbol.states.add(index)
        else:
            index = self.create_state_and_add_space(
                status, stmt_id, stmt_id, data_type = data_type, state_type = state_type
            )

        return index

    def read_used_states(self, index, in_states):
        """读取给定索引对应的符号或状态在输入状态集合中的使用情况"""
        target = self.frame.symbol_state_space[index]
        if isinstance(target, Symbol):
            return in_states.get(target.symbol_id, set())

        return {index}

    def obtain_states(self, index):
        """获取给定索引对应的状态集合（符号的状态或单个状态）"""
        s = self.frame.symbol_state_space[index]
        if isinstance(s, State):
            return {index}
        elif isinstance(s, Symbol):
            return s.states
        return set()

    def run_stmt_state_analysis(self, stmt_id, stmt, status: StmtStatus, in_states):
        """根据语句类型分发到对应的状态处理函数进行分析"""
        # print("status.operation:", status.operation)
        handler = self.state_analysis_handlers.get(stmt.operation, None)
        if handler is None:
            return self.regular_stmt_state(stmt_id, stmt, status, in_states)
        return handler(stmt_id, stmt, status, in_states)

    def read_defined_symbol_states(self, status: StmtStatus):
        """读取已定义符号的状态集合"""
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return set()

        return defined_symbol.states

    def cancel_key_state(self, symbol_id, state_index, stmt_id = -1):
        """取消关键状态标记，并清理相关动态调用信息"""
        key_state = self.frame.symbol_state_space[state_index]
        if not(key_state and isinstance(key_state, State)):
            return

        if key_state.symbol_or_state == SYMBOL_OR_STATE.EXTERNAL_KEY_STATE:
            key_state.symbol_or_state = SYMBOL_OR_STATE.STATE
            key_dynamic_content = self.frame.method_summary_template.key_dynamic_content
            if symbol_id in key_dynamic_content:
                values = key_dynamic_content[symbol_id]
                values.discard(IndexMapInSummary(raw_index = state_index, new_index = -1))

        if stmt_id > 0:
            self.frame.method_summary_template.dynamic_call_stmts.discard(stmt_id)

    def tag_key_state(self, stmt_id, symbol_id, state_index):
        """将状态标记为关键状态，并记录相关动态调用信息"""
        key_state = self.frame.symbol_state_space[state_index]
        if not(key_state and isinstance(key_state, State)):
            return

        key_state.symbol_or_state = SYMBOL_OR_STATE.EXTERNAL_KEY_STATE
        key_dynamic_content = self.frame.method_summary_template.key_dynamic_content
        # print("tag_key_state@add_state_index",state_index)
        util.add_to_dict_with_default_set(
            key_dynamic_content, symbol_id, IndexMapInSummary(raw_index = state_index, new_index = -1)
        )
        self.frame.method_summary_template.dynamic_call_stmts.add(stmt_id)

    def regular_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        return P2ResultFlag()

    def control_flow_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """处理控制流语句，分析条件路径（真/假路径）"""
        condition_index = status.used_symbols[0]
        condition_states = self.read_used_states(condition_index, in_states)

        condition_flag = CONDITION_STMT_PATH_FLAG.NO_PATH
        for each_state_index in condition_states:
            each_state = self.frame.symbol_state_space[each_state_index]
            if not each_state:
                continue
            #print("each_state:", each_state)
            if len(each_state.fields) != 0 or len(each_state.array) != 0 or len(each_state.tangping_elements) != 0:
                condition_flag |= CONDITION_STMT_PATH_FLAG.TRUE_PATH
            else:
                if each_state.value == LIAN_INTERNAL.FALSE:
                    condition_flag |= CONDITION_STMT_PATH_FLAG.FALSE_PATH
                elif each_state.value == 0:
                    condition_flag |= CONDITION_STMT_PATH_FLAG.FALSE_PATH
                else:
                    condition_flag |= CONDITION_STMT_PATH_FLAG.TRUE_PATH

            if condition_flag == CONDITION_STMT_PATH_FLAG.ANY_PATH:
                break

        return P2ResultFlag(condition_path_flag = condition_flag)
        # return P2ResultFlag()

    def update_access_path_state_id(self, state_index):
        state = self.frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            return
        state.access_path[-1].state_id = state.state_id

    def forin_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        <forin_stmt defined_symbol: name, used_symbol: [receiver]>
        处理for-in循环语句状态：
        1. 获取接收器符号状态
        2. 分析数组/字典结构
        3. 生成循环轮次状态
        4. 更新定义符号集合
        """
        receiver_index = status.used_symbols[0]
        receiver_symbol = self.frame.symbol_state_space[receiver_index]
        receiver_states = self.read_used_states(receiver_index, in_states)

        new_receiver_symbol_index = None
        new_receiver_symbol = None

        defined_symbol_states = set()
        current_round = self.frame.stmt_counters[stmt_id]
        loop_total_rounds = 0

        for receiver_state_index in receiver_states:
            receiver_state = self.frame.symbol_state_space[receiver_state_index]
            if not isinstance(receiver_state, State):
                continue

            if receiver_state.tangping_elements:
                defined_symbol_states.update(receiver_state.tangping_elements)

            # 根据receiver类型进行分发. array / dict
            # 处理array
            elif receiver_state.array:
                # for cur_elem_states in receiver_state.array:
                #     for cur_elem_states_index in cur_elem_states:
                #         defined_symbol_states.add(cur_elem_states_index)

                receiver_array = receiver_state.array
                receiver_array_length = len(receiver_array)
                if current_round >= receiver_array_length:
                    continue
                defined_symbol_states.update(receiver_state.array[current_round])
                loop_total_rounds = min(receiver_array_length, config.MAX_STMT_STATE_ANALYSIS_ROUND)
                # current_key_index = self.create_state_and_add_space(
                #     status, stmt_id=stmt_id, value=current_round, data_type=LianInternal.INT,
                #     source_state_id = receiver_state.source_state_id,
                #     source_symbol_id = receiver_state.source_symbol_id,
                #     access_path= self.copy_and_extend_access_path(
                #         receiver_state.access_path,
                #         AccessPoint(
                #             kind = AccessPointKind.ARRAY_INDEX,
                #             key = current_round
                #         )
                #     )
                # )
                # self.update_access_path(current_key_index)
                # defined_symbol_states.add(current_key_index)

            # 处理dict
            elif receiver_state.fields:
                # print(f"current_round: {current_round}")
                all_sorted_keys = sorted(receiver_state.fields.keys())
                real_sorted_keys = []
                if receiver_state.data_type == LIAN_INTERNAL.ARRAY:
                    for key in all_sorted_keys:
                        if key.isdigit():
                            real_sorted_keys.append(key)
                else:
                    real_sorted_keys = all_sorted_keys

                keys_length = len(real_sorted_keys)
                if current_round >= keys_length:
                    continue
                loop_total_rounds = min(keys_length, config.MAX_STMT_STATE_ANALYSIS_ROUND)
                current_key = real_sorted_keys[current_round]
                # print(f"current_key: {current_key}")
                current_key_index = self.create_state_and_add_space(
                    status, stmt_id=stmt_id, value=f'{current_key}', data_type=LIAN_INTERNAL.STRING,
                    source_state_id= receiver_state.source_state_id,
                    source_symbol_id=receiver_state.source_symbol_id,
                    access_path=self.copy_and_extend_access_path(
                        receiver_state.access_path,
                        AccessPoint(
                            kind = ACCESS_POINT_KIND.FIELD_NAME,
                            key = current_key
                        )
                    )
                )
                self.update_access_path_state_id(current_key_index)

                defined_symbol_states.add(current_key_index)

            elif receiver_state.state_type == STATE_TYPE_KIND.ANYTHING:
                self.tag_key_state(stmt_id, receiver_symbol.symbol_id, receiver_state_index)

                if util.is_empty(new_receiver_symbol_index):
                    new_receiver_symbol_index = self.create_copy_of_symbol_and_add_space(status, stmt_id, receiver_symbol)
                    new_receiver_symbol: Symbol = self.frame.symbol_state_space[new_receiver_symbol_index]

                new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, receiver_state_index)
                new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]

                source_index = self.create_state_and_add_space(
                    status = status,
                    stmt_id = stmt_id,
                    source_symbol_id=receiver_state.source_symbol_id,
                    source_state_id=receiver_state.source_state_id,
                    state_type = STATE_TYPE_KIND.ANYTHING,
                    access_path = self.copy_and_extend_access_path(
                        new_receiver_state.access_path,
                        AccessPoint(
                            kind = ACCESS_POINT_KIND.FORIN_ELEMENT
                        )
                    )
                )
                self.update_access_path_state_id(source_index)

                self.make_state_tangping(new_receiver_state)
                new_receiver_state.tangping_elements.add(source_index)
                new_receiver_symbol.states.discard(receiver_state_index)
                new_receiver_symbol.states.add(new_receiver_state_index)

                # print("new_receiver_symbol", new_receiver_symbol.states)

                defined_symbol_states.add(source_index)

        if stmt_id not in self.frame.loop_total_rounds:
            self.frame.loop_total_rounds[stmt_id] = loop_total_rounds

        # print(f"loop_total_rounds: {self.frame.loop_total_rounds[stmt_id]}")
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol.states = defined_symbol_states
        # print(f"defined_symbol.states: {defined_symbol.states}")
        return P2ResultFlag()

    def for_value_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        处理for-value循环语句状态：
        1. 获取接收器符号状态
        2. 分析值类型结构
        3. 生成循环轮次状态
        4. 更新定义符号集合
        <for_value_stmt defined_symbol: name, used_symbol: [receiver]>
        """
        receiver_index = status.used_symbols[0]
        receiver_symbol = self.frame.symbol_state_space[receiver_index]
        receiver_states = self.read_used_states(receiver_index, in_states)

        new_receiver_symbol_index = None
        new_receiver_symbol = None

        defined_symbol_states = set()
        current_round = self.frame.stmt_counters[stmt_id]
        loop_total_rounds = 0

        for receiver_state_index in receiver_states:
            receiver_state = self.frame.symbol_state_space[receiver_state_index]
            if not (receiver_state and isinstance(receiver_state, State)):
                continue

            if receiver_state.tangping_elements:
                defined_symbol_states.update(receiver_state.tangping_elements)

            # 根据receiver类型进行分发. array / dict
            # 处理array
            elif receiver_state.array:
                # for cur_elem_states in receiver_state.array:
                #     for cur_elem_states_index in cur_elem_states:
                #         defined_symbol_states.add(cur_elem_states_index)

                receiver_array = receiver_state.array
                receiver_array_length = len(receiver_array)
                if current_round >= receiver_array_length:
                    continue
                loop_total_rounds = min(receiver_array_length, config.MAX_STMT_STATE_ANALYSIS_ROUND)
                defined_symbol_states.update(receiver_array[current_round])

            # 处理dict
            elif receiver_state.fields:
                all_sorted_keys = sorted(receiver_state.fields.keys())
                keys_length = len(all_sorted_keys)
                if current_round >= keys_length:
                    continue
                loop_total_rounds = min(keys_length, config.MAX_STMT_STATE_ANALYSIS_ROUND)
                current_key = all_sorted_keys[current_round]
                defined_symbol_states.update(receiver_state.fields[current_key])

            elif receiver_state.state_type == STATE_TYPE_KIND.ANYTHING:
                self.tag_key_state(stmt_id, receiver_symbol.symbol_id, receiver_state_index)

                if util.is_empty(new_receiver_symbol_index):
                    new_receiver_symbol_index = self.create_copy_of_symbol_and_add_space(status, stmt_id, receiver_symbol)
                    new_receiver_symbol: Symbol = self.frame.symbol_state_space[new_receiver_symbol_index]

                new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, receiver_state_index)
                new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]
                source_index = self.create_state_and_add_space(
                    status = status,
                    stmt_id = stmt_id,
                    source_symbol_id=receiver_state.source_symbol_id,
                    source_state_id=receiver_state.source_state_id,
                    state_type = STATE_TYPE_KIND.ANYTHING,
                    access_path = self.copy_and_extend_access_path(
                        receiver_state.access_path,
                        AccessPoint(
                            kind = ACCESS_POINT_KIND.FORIN_ELEMENT
                        )
                    )
                )
                self.update_access_path_state_id(source_index)

                self.make_state_tangping(new_receiver_state)
                new_receiver_state.tangping_elements.add(source_index)
                new_receiver_symbol.states.discard(receiver_state_index)
                new_receiver_symbol.states.add(new_receiver_state_index)

                # print("new_receiver_symbol", new_receiver_symbol.states)

                defined_symbol_states.add(source_index)

        self.frame.loop_total_rounds[stmt_id] = loop_total_rounds
        # print(f"self.frame.loop_total_rounds[stmt_id]: {self.frame.loop_total_rounds[stmt_id]}")
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol.states = defined_symbol_states
        return P2ResultFlag()

    def import_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        # The imported symbol should be anything and is provided by complete_in_states before calling this function
        return P2ResultFlag()

    def from_import_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        return self.import_stmt_state(stmt_id, stmt, status, in_states)

    def export_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        return P2ResultFlag()

    def export_from_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        return P2ResultFlag()

    def require_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        name_symbol_index = status.used_symbols[0]
        name_symbol = self.frame.symbol_state_space[name_symbol_index]
        name_state_indexes = self.read_used_states(name_symbol_index, in_states)

        defined_index = status.defined_symbol
        defined_symbol = self.frame.symbol_state_space[defined_index]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        result = set()
        for each_index in name_state_indexes:
            each_name_state = self.frame.symbol_state_space[each_index]
            if each_name_state.value:
                state_index = self.create_state_and_add_space(
                    status, stmt_id,
                    source_symbol_id = defined_symbol.symbol_id,
                    data_type = LIAN_INTERNAL.REQUIRED_MODULE,
                    value = each_name_state.value,
                    access_path = [AccessPoint(
                        kind = ACCESS_POINT_KIND.REQUIRED_MODULE,
                        key = util.read_stmt_field(each_name_state.value),
                    )]
                )
                self.update_access_path_state_id(state_index)
                result.add(state_index)

        defined_symbol.states = result

        return P2ResultFlag()

    def compute_two_states(self, stmt, state1, state2, defined_symbol: Symbol):
        """
        计算双状态运算结果：
        1. 处理常规类型运算
        2. 处理动态类型组合
        3. 生成新状态并关联操作符

        REGULAR op REGULAR = REGULAR
        REGULAR op UNSOLVED = UNSOLVED
        REGULAR op ANY = ANY
        """
        symbol_id = defined_symbol.symbol_id
        if util.is_empty(state1) or util.is_empty(state2):
            return set()

        status = self.frame.stmt_id_to_status[stmt.stmt_id]
        value1 = state1.value
        state_type1 = state1.state_type
        data_type1 = state1.data_type
        value2 = state2.value
        state_type2 = state2.state_type
        data_type2 = state2.data_type
        operator = stmt.operator

        if not (state_type1 == state_type2 == STATE_TYPE_KIND.REGULAR):
            return set()

        if not (value1 and type_table.is_builtin_type(data_type1) and value2 and type_table.is_builtin_type(data_type2)):
            return set()

        value = None
        data_type = state1.data_type

        tmp_value1 = value1
        tmp_value2 = value2

        is_bool = True if operator in ["and", "or"] else False
        is_string = False
        if data_type1 == LIAN_INTERNAL.STRING:
            value1 = str(value1)
            if not value1.isdigit():
                is_string = True
        if not is_string:
            if data_type2 == LIAN_INTERNAL.STRING:
                value2 = str(value2)
                if not value2.isdigit():
                    is_string = True

        if not is_bool and is_string:
            tmp_value1 = f'"{tmp_value1}"'
            tmp_value2 = f'"{tmp_value2}"'
            data_type = LIAN_INTERNAL.STRING
        else:
            is_float = False
            if data_type1 == LIAN_INTERNAL.FLOAT or data_type2 == LIAN_INTERNAL.FLOAT:
                is_float = True
                data_type = LIAN_INTERNAL.FLOAT
            else:
                data_type = LIAN_INTERNAL.INT

            tmp_value1 = f'{tmp_value1}'
            tmp_value2 = f'{tmp_value2}'

        try:
            #print(tmp_value1, tmp_value2, operator)
            value = util.strict_eval(f"{tmp_value1} {operator} {tmp_value2}")
        except:
            # value = ""
            value = str(value1) + str(operator) + str(value2)
            data_type = LIAN_INTERNAL.STRING

        # else:
        #     value = str(value1) + str(operator) + str(value2)
        #     data_type = LianInternal.STRING

        if value:
            result_state_index = self.create_state_and_add_space(
                status, stmt_id=stmt.stmt_id, source_symbol_id=symbol_id, value=value, data_type=data_type,
                access_path = [AccessPoint(
                    kind = ACCESS_POINT_KIND.BINARY_ASSIGN,
                    key = defined_symbol.name
                )]
            )
            self.update_access_path_state_id(result_state_index)

            return {result_state_index}

        # state_type = StateTypeKind.ANYTHING
        # if StateTypeKind.UNSOLVED in (state_type1, state_type2):
        #     state_type = StateTypeKind.UNSOLVED

        # state_index1 = self.create_state_and_add_space(
        #     status, stmt_id=stmt.stmt_id, source_symbol_id=symbol_id,
        #     data_type = f"{data_type1}/{data_type2}", state_type = state_type,
        #     access_path=self.copy_and_extend_access_path(
        #         state1.access_path,
        #         AccessPoint(
        #             kind = AccessPointKind.BINARY_ASSIGN,
        #             key=defined_symbol.name
        #         )
        #     )
        # )
        # self.update_access_path_state_id(state_index1)
        # # state_index2 = self.create_state_and_add_space(
        # #     status, stmt_id=stmt.stmt_id, source_symbol_id=symbol_id,
        # #     data_type = data_type2, state_type = state_type,
        # #     access_path=self.copy_and_extend_access_path(
        # #         state2.access_path,
        # #         AccessPoint(
        # #             kind = AccessPointKind.BINARY_ASSIGN,
        # #             key=defined_symbol.name
        # #         )
        # #     )
        # # )
        # # self.update_access_path_state_id(state_index2)
        # return {state_index1}
        return set()

    def assign_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        assign_stmt data_type   target  operand operator    operand2
        def: target
        use: operand operand2
        """
        operand_index = status.used_symbols[0]
        operand_symbol = self.frame.symbol_state_space[operand_index]
        operand_states = self.read_used_states(operand_index, in_states)
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        source_symbol_id = -1
        if isinstance(operand_symbol, Symbol):
            source_symbol_id = operand_symbol.symbol_id
        new_states = set()
        # only one operand
        if util.isna(stmt.operand2):
            # compute unary operation
            # 形如 a = b
            if util.isna(stmt.operator):
                # print(">>>>>", stmt_id, stmt)
                # print(operand_states)
                defined_symbol.states = operand_states
                return P2ResultFlag()

            # 形如 a = -b
            for operand_state_index in operand_states:
                operand_state = self.frame.symbol_state_space[operand_state_index]
                if not isinstance(operand_state, State):
                    continue

                if not util.is_empty(operand_state.value):
                    try:
                        value = util.strict_eval(f"{stmt.operator}{operand_state.value}")
                        data_type = operand_state.data_type
                    except:
                        # value = None
                        # data_type = ""
                        continue

                    # state_index = self.create_state_and_add_space(
                    #     status, stmt.stmt_id,
                    #     source_symbol_id=source_symbol_id,
                    #     source_state_id=operand_state.source_state_id,
                    #     value=value,
                    #     data_type = data_type,
                    #     access_path=self.copy_and_extend_access_path(
                    #         operand_state.access_path,
                    #         AccessPoint(
                    #             kind = AccessPointKind.BINARY_ASSIGN,
                    #             key=defined_symbol.name
                    #         )
                    #     )
                    # )
                    # self.update_access_path_state_id(state_index)
                    # new_states.add(state_index)

                    new_operand_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, operand_state_index)
                    new_operand_state = self.frame.symbol_state_space[new_operand_state_index]
                    new_operand_state.value = value
                    # new_operand_state.access_path.append(
                    #     AccessPoint(
                    #         kind = AccessPointKind.BINARY_ASSIGN,
                    #         key=defined_symbol.name
                    #     )
                    # )
                    #self.update_access_path_state_id(new_operand_state_index)
                    new_states.add(new_operand_state_index)
            # 保证defined_symbol.states中有东西

            if len(new_states) == 0:
                tmp_index = self.create_state_and_add_space(
                        status, stmt.stmt_id,
                        value = None,
                        data_type = "",
                        source_symbol_id = source_symbol_id,
                        state_type =  STATE_TYPE_KIND.ANYTHING
                    )
                new_states = {tmp_index}
            defined_symbol.states = new_states
            return P2ResultFlag()

        # two operands
        operand2_index = status.used_symbols[1]
        operand2_states = self.read_used_states(operand2_index, in_states)

        for operand_state_index in operand_states:
            operand_state = self.frame.symbol_state_space[operand_state_index]
            if not isinstance(operand_state, State):
                continue
            if operand_state.state_type != STATE_TYPE_KIND.REGULAR:
                continue
            for operand2_state_index in operand2_states:
                operand2_state = self.frame.symbol_state_space[operand2_state_index]
                if not isinstance(operand2_state, State):
                    continue
                if operand2_state.state_type != STATE_TYPE_KIND.REGULAR:
                    continue

                # if operand_state.state_type == StateTypeKind.ANYTHING or operand2_state.state_type == StateTypeKind.ANYTHING:
                #     new_operand_state_index = self.create_state_and_add_space(status, stmt_id)
                #     new_operand_state = self.frame.symbol_state_space[new_operand_state_index]
                #     new_operand_state.access_path.append(
                #         AccessPoint(
                #             kind = AccessPointKind.BINARY_ASSIGN,
                #             key=defined_symbol.name
                #         )
                #     )
                #     self.update_access_path_state_id(new_operand_state_index)
                #     defined_symbol.states = {new_operand_state_index}
                #     return P2ResultFlag()

                new_states.update(
                    self.compute_two_states(
                        stmt, operand_state, operand2_state, defined_symbol
                    )
                )
        # 保证defined_symbol.states不为空
        if not new_states:
            state_index = self.create_state_and_add_space(
                    status, stmt.stmt_id,
                    value = None,
                    data_type = "",
                    source_symbol_id = source_symbol_id,
                    state_type =  STATE_TYPE_KIND.ANYTHING
                )
            new_states = {state_index}
        defined_symbol.states = new_states
        return P2ResultFlag()

    def prepare_args(self, stmt_id, stmt, status: StmtStatus, in_states, args_state_set = dict()):
        # used_symbols: [name, packed_positional_args, packed_named_args]
        # used_symbols: [name, packed_positional_args, named_args]
        # used_symbols: [name, positional_args, packed_named_args]
        # used_symbols: [name, positional_args, named_args]
        # index#1 of packed_positional_args: 1
        # index#2 of packed_named_args: -1
        # index#3 of named_args: [sorted values, -1]
        # index#4 of positional_args: [1, index#2/index#3]
        """
        Sequentially parse the arguments by types:
            packed_named_args, named_args, packed_positional_args, positional_args
        """

        positional_args = []
        named_args = {}
        named_args_index = len(status.used_symbols)

        # deal with packed_positional_args
        if not util.isna(stmt.packed_named_args):
            packed_named_arg_index = status.used_symbols[-1]
            item_index_set = self.read_used_states(packed_named_arg_index, in_states)
            if util.is_available(item_index_set):
                for each_item_index in item_index_set:
                    each_item = self.frame.symbol_state_space[each_item_index]
                    if not (each_item and isinstance(each_item, State) and each_item.fields):
                        continue

                    named_args.update(each_item.fields)

                    for field_name, state_index_set in each_item.fields.items():
                        util.add_to_dict_with_default_set(named_args, field_name, state_index_set)

            named_args_index -= 1

        # deal with named_args
        if not util.isna(stmt.named_args):
            args_dict = ast.literal_eval(stmt.named_args)
            keys = sorted(args_dict.keys())
            keys_len = len(keys)
            len_of_used_symbols = len(status.used_symbols)

            if len_of_used_symbols > keys_len:
                indexes = status.used_symbols[-keys_len:]
                tmp_counter = 0
                while tmp_counter < keys_len:
                    each_key = keys[tmp_counter]
                    each_arg = self.frame.symbol_state_space[indexes[tmp_counter]]
                    if isinstance(each_arg, Symbol):
                        for each_state_index in each_arg.states:
                            each_state = self.frame.symbol_state_space[each_state_index]
                            if not(each_state and isinstance(each_state, State)):
                                continue
                            if each_state.state_type == STATE_TYPE_KIND.ANYTHING:
                                self.tag_key_state(stmt_id, each_arg.symbol_id, each_state_index)
                        named_args[each_key] = each_arg.states
                    elif isinstance(each_arg, State):
                        named_args[each_key] = {indexes[tmp_counter]}
                    tmp_counter += 1

                named_args_index -= len(named_args)

        # deal with positional_args
        positional_args: list[set] = []
        if not util.isna(stmt.packed_positional_args):
            item_index_set = self.read_used_states(status.used_symbols[1], in_states)
            if util.is_available(item_index_set):
                for each_item_index in item_index_set:
                    each_item = self.frame.symbol_state_space[each_item_index]
                    if not (each_item and isinstance(each_item, State) and each_item.array):
                        continue

                    for array_index in range(len(each_item.array)):
                        array_length = len(positional_args)
                        if array_length <= array_index:
                            positional_args.extend(
                                [set() for _ in range(array_index + 1 - array_length)]
                            )

                        positional_args[array_index].update(each_item.array[array_index])

        elif not util.isna(stmt.positional_args):
            for index in range(1, named_args_index):
                each_arg = self.frame.symbol_state_space[status.used_symbols[index]]
                if isinstance(each_arg, Symbol):
                    for each_state_index in each_arg.states:
                        each_state = self.frame.symbol_state_space[each_state_index]
                        if not(each_state and isinstance(each_state, State)):
                            continue
                        if each_state.state_type == STATE_TYPE_KIND.ANYTHING:
                            self.tag_key_state(stmt_id, each_arg.symbol_id, each_state_index)
                    positional_args.append(each_arg.states)
                elif isinstance(each_arg, State):
                    positional_args.append({status.used_symbols[index]})
            # for index in range(1, named_args_index):
            #     positional_args.append({status.used_symbols[index]})

        # adjust named_args
        for each_key, index_set in named_args.items():
            arg_set = set()
            for each_index in index_set:
                content = self.frame.symbol_state_space[each_index]
                if isinstance(content, State):
                    arg_set.add(
                        Argument(
                            state_id = content.state_id,
                            call_stmt_id = stmt_id,
                            name = each_key,
                            source_symbol_id = content.source_symbol_id,
                            access_path = content.access_path,
                            index_in_space = each_index
                        )
                    )

            named_args[each_key] = arg_set

        # adjust positional_args
        counter = 0
        while counter < len(positional_args):
            index_set = positional_args[counter]
            arg_set = set()
            for each_index in index_set:
                content = self.frame.symbol_state_space[each_index]
                if isinstance(content, State):
                    arg_set.add(
                        Argument(
                            state_id = content.state_id,
                            call_stmt_id = stmt_id,
                            position = counter,
                            source_symbol_id = content.source_symbol_id,
                            access_path = content.access_path,
                            index_in_space = each_index
                        )
                    )

            positional_args[counter] = arg_set

            counter += 1

        return MethodCallArguments(positional_args, named_args)

    def prepare_parameters(self, callee_id):
        result = MethodDeclParameters()
        _, parameters_block = self.loader.get_method_header(callee_id)
        if not parameters_block:
            return result

        counter = 0
        for row in parameters_block:
            if row.operation != "parameter_decl":
                continue

            p = Parameter(
                method_id = callee_id, position = counter, name = row.name, symbol_id = row.stmt_id
            )
            is_attr = not util.isna(row.attrs)
            result.all_parameters.add(p)
            if is_attr and LIAN_INTERNAL.PACKED_NAMED_PARAMETER in row.attrs:
                result.packed_named_parameter = p
            elif is_attr and LIAN_INTERNAL.PACKED_POSITIONAL_PARAMETER in row.attrs:
                result.packed_positional_parameter = p
            else:
                result.positional_parameters.append(p)

            counter += 1

        return result

    def map_arguments(
        self, args: MethodCallArguments, parameters: MethodDeclParameters,
        parameter_mapping_list: list[ParameterMapping], call_site, phase
    ):
        """
        Mapping arguments and parameters in terms of symbol_ids
        This is done sequnetially by their types:
            - positional_args
            - named_args
            - packed_positional_args
            - packed_named_args
        """
        #### < key:symbol_id of parameter, value: parameter's states >

        # link args and parameters in terms of symbol_ids
        positional_arg_len = len(args.positional_args)
        positional_parameter_len = len(parameters.positional_parameters)
        common_len = min(positional_arg_len, positional_parameter_len)
        named_args_matched = set()
        rest_parameters = parameters.all_parameters.copy()

        pos = 0
        while pos < common_len:
            arg_set: set[Argument] = args.positional_args[pos]
            parameter: Parameter = parameters.positional_parameters[pos]
            if arg_set:
                rest_parameters.discard(parameter)
            for arg in arg_set:
                parameter_mapping_list.append(
                    ParameterMapping(
                        arg_index_in_space = arg.index_in_space,
                        arg_state_id = arg.state_id,
                        arg_access_path = arg.access_path,
                        arg_source_symbol_id = arg.source_symbol_id,
                        parameter_symbol_id = parameter.symbol_id
                    )
                )
            pos += 1

        name_to_parameter = {}
        if common_len < positional_parameter_len:
            # has default_parameter || has named_args
            # 下面处理named_args
            tmp_pos = common_len
            while tmp_pos < positional_parameter_len:
                each_parameter: Parameter = parameters.positional_parameters[tmp_pos]
                name_to_parameter[each_parameter.name] = each_parameter
                tmp_pos += 1

            if len(args.named_args) > 0 and len(name_to_parameter) > 0:
                for each_arg_name in args.named_args:
                    each_arg_set: set[Argument] = args.named_args[each_arg_name]
                    for each_arg in each_arg_set:
                        if each_arg_name in name_to_parameter:
                            each_parameter = name_to_parameter[each_arg_name]
                            rest_parameters.discard(each_parameter)
                            named_args_matched.add(each_arg_name)
                            parameter_mapping_list.append(
                                ParameterMapping(
                                    arg_index_in_space = each_arg.index_in_space,
                                    arg_state_id = each_arg.state_id,
                                    arg_source_symbol_id = each_arg.source_symbol_id,
                                    arg_access_path = each_arg.access_path,
                                    parameter_symbol_id = each_parameter.symbol_id
                                )
                            )

        elif common_len < positional_arg_len:
            if util.is_available(parameters.packed_positional_parameter):
                id = parameters.packed_positional_parameter.symbol_id
                parameter_index = 0
                for arg_set in args.positional_args[pos:]:
                    if arg_set:
                        rest_parameters.discard(parameters.packed_positional_parameter)
                    for arg in arg_set:
                        parameter_mapping_list.append(
                            ParameterMapping(
                                arg_index_in_space = arg.index_in_space,
                                arg_state_id = arg.state_id,
                                arg_source_symbol_id = arg.source_symbol_id,
                                arg_access_path = arg.access_path,
                                parameter_symbol_id = id,
                                parameter_type = LIAN_INTERNAL.PACKED_POSITIONAL_PARAMETER,
                                parameter_access_path = AccessPoint(
                                    kind = ACCESS_POINT_KIND.ARRAY_ELEMENT,
                                    key = parameter_index,
                                    state_id = arg.state_id
                                )
                            )
                        )
                    parameter_index += 1

        if util.is_available(parameters.packed_named_parameter):
            id = parameters.packed_named_parameter.symbol_id
            if len(args.named_args) > 0:
                for each_arg_name in args.named_args:
                    if each_arg_name in named_args_matched:
                        continue

                    each_arg_set: set[Argument] = args.named_args[each_arg_name]
                    if each_arg_set:
                        rest_parameters.discard(parameters.packed_named_parameter)
                    for each_arg in each_arg_set:
                        parameter_mapping_list.append(
                            ParameterMapping(
                                arg_index_in_space = each_arg.index_in_space,
                                arg_state_id = each_arg.state_id,
                                arg_source_symbol_id = each_arg.source_symbol_id,
                                arg_access_path = each_arg.access_path,
                                parameter_symbol_id = id,
                                parameter_type = LIAN_INTERNAL.PACKED_NAMED_PARAMETER,
                                parameter_access_path = AccessPoint(
                                    kind = ACCESS_POINT_KIND.FIELD_ELEMENT,
                                    key = str(each_arg_name),
                                    state_id = each_arg.state_id
                                )
                            )
                        )

                    named_args_matched.add(each_arg_name)

        if rest_parameters:
            for each_parameter in rest_parameters:
                parameter_symbol_id = each_parameter.symbol_id
                default_value_symbol_id = None
                callee_method_def_use_summary = self.loader.get_method_def_use_summary(call_site[2]).copy()
                for symbol_default_pair in callee_method_def_use_summary.parameter_symbol_ids:
                    if parameter_symbol_id == symbol_default_pair[0]:
                        default_value_symbol_id = symbol_default_pair[1]
                        break

                # if default_value_symbol_id and default_value_symbol_id in callee_def_use_summary.used_external_symbol_ids:
                if default_value_symbol_id:
                    parameter_mapping_list.append(
                        ParameterMapping(
                            arg_state_id = default_value_symbol_id,
                            parameter_symbol_id = parameter_symbol_id,
                            is_default_value = True
                        )
                    )
        if self.analysis_phase_id == ANALYSIS_PHASE_ID.STATIC_SEMANTICS:
            self.loader.save_parameter_mapping_p2(call_site, parameter_mapping_list)
        elif self.analysis_phase_id == ANALYSIS_PHASE_ID.DYNAMIC_SEMANTICS:
            self.loader.save_parameter_mapping_p3(call_site, parameter_mapping_list)

    def fuse_states_to_one_state(self, state_indexes:set, stmt_id, status: StmtStatus):
        """
        给定一组state_indexes的集合，将这些states进行合并,只产生一个新state，合并了所有children_states
        """
        if util.is_empty(state_indexes) or len(state_indexes) == 1:
            return state_indexes
        # 以集合中的任一个元素作为模板，创建一个fusion_state。create_copy过程中会自动将fusion_state加入status.defined_states中。
        new_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, list(state_indexes)[0])
        new_state:State = self.frame.symbol_state_space[new_state_index]
        state_array: list[set] = []
        tangping_flag = False
        tangping_elements = set()
        state_fields = {}
        for each_state_index in state_indexes:
            each_state = self.frame.symbol_state_space[each_state_index]
            if not (each_state and isinstance(each_state, State)):
                continue
            for index in range(len(each_state.array)):
                util.add_to_list_with_default_set(state_array, index, each_state.array[index])
            for field_name in each_state.fields:
                util.add_to_dict_with_default_set(state_fields, field_name, each_state.fields[field_name])
            tangping_flag |= each_state.tangping_flag
            tangping_elements.update(each_state.tangping_elements)
        new_state.array = state_array
        new_state.fields = state_fields
        new_state.tangping_elements = tangping_elements
        new_state.tangping_flag = tangping_flag
        if tangping_flag:
            self.make_state_tangping(new_state)
        return {new_state_index}


    def recursively_collect_children_fields(self, stmt_id, status: StmtStatus, state_set_in_summary_field: set, state_set_in_arg_field: set, source_symbol_id, access_path):
        """
        合并两个“状态集合”———— 【一个来自 summary field（state_set_in_summary_field），一个来自 arg field（state_set_in_arg_field）】所对应的所有 State 对象中的 fields（字段）信息，
        最终创建一个或多个新的 State，并返回这些新 State 在符号空间（symbol_state_space）中的索引集合。
        """
        # 闭包缓存，避免field环形依赖
        cache = {}

        def _recursively_collect_children_fields(stmt_id, status: StmtStatus, state_set_in_summary_field: set, state_set_in_arg_field: set, source_symbol_id, access_path):
            cache_key = (
                stmt_id,
                frozenset(state_set_in_summary_field),
                frozenset(state_set_in_arg_field),
                source_symbol_id,
            )
            # 检查缓存
            if cache_key in cache:
                return cache[cache_key]

            # state_type默认为REGULAR，如果任意一个输入状态的 state_type 是 ANYTHING，则结果也标记为 ANYTHING。
            state_type = STATE_TYPE_KIND.REGULAR
            # summary_states_fields / arg_state_fields：分别用来收集summary和arg两组状态的字段映射（字段名 → 值集合）。
            summary_states_fields = {}
            arg_state_fields = {}
            tangping_flag = False
            tangping_elements = set()
            return_set = set()

            # 填充summary_states_fields
            for each_state_index in state_set_in_summary_field:
                each_state = self.frame.symbol_state_space[each_state_index]
                # print("打印summary_field中的",each_state_index)
                # pprint.pprint(each_state)
                if not (each_state and isinstance(each_state, State)):
                    continue
                if each_state.state_type == STATE_TYPE_KIND.ANYTHING:
                    state_type = STATE_TYPE_KIND.ANYTHING
                if each_state.tangping_flag:
                    tangping_flag = True
                    tangping_elements.update(each_state.tangping_elements)
                    continue
                # 将该State的fields中每个字段名和对应值集，合并到summary_states_fields，同名字段时将值集并集。
                each_state_fields = each_state.fields.copy()
                for field_name in each_state_fields:
                    util.add_to_dict_with_default_set(summary_states_fields, field_name, each_state_fields[field_name])

            # 填充arg_state_fields
            for each_state_index in state_set_in_arg_field:
                each_state = self.frame.symbol_state_space[each_state_index]
                if not (each_state and isinstance(each_state, State)):
                    continue
                # print("打印arg_field中的",each_state_index)
                # pprint.pprint(each_state)
                if each_state.tangping_flag:
                    tangping_flag = True
                    tangping_elements.update(each_state.tangping_elements)
                    continue
                each_state_fields = each_state.fields.copy()
                for field_name in each_state_fields:
                    util.add_to_dict_with_default_set(arg_state_fields, field_name, each_state_fields[field_name])

            if tangping_flag:
                new_state_index = self.create_state_and_add_space(status, stmt_id)
                new_state: State = self.frame.symbol_state_space[new_state_index]
                new_state.tangping_flag = True
                new_state.tangping_elements = tangping_elements
                return_set.add(new_state_index)

            # print(f"\n======\naccess_path {access_path}")
            # print(f"arg_fields: {arg_state_fields}\nsummary_fields: {summary_states_fields}" )

            # 只有单侧有字段时的处理
            if not arg_state_fields or not summary_states_fields:
                if summary_states_fields:
                    new_state_index = self.create_state_and_add_space(status, stmt_id)
                    new_state: State = self.frame.symbol_state_space[new_state_index]
                    new_state.fields = summary_states_fields
                    return_set.add(new_state_index)
                elif arg_state_fields:
                    new_state_index = self.create_state_and_add_space(status, stmt_id)
                    new_state: State = self.frame.symbol_state_space[new_state_index]
                    new_state.fields = arg_state_fields
                    return_set.add(new_state_index)
                else:
                    new_state = None
                    if not return_set:
                        return_set.update(state_set_in_summary_field)
                if new_state:
                    new_state.state_type = state_type
                    new_state.source_symbol_id = source_symbol_id
                    new_state.access_path = access_path
                return return_set

            # 两侧都有字段
            new_state_index = self.create_state_and_add_space(status, stmt_id)
            return_set = {new_state_index}
            cache[cache_key] = return_set

            for field_name in summary_states_fields:
                if field_name not in arg_state_fields:
                    arg_state_fields[field_name] = summary_states_fields[field_name]
                # 如果已经存在，则 深入递归合并
                else:
                    # print(f"原本access_path是{access_path}")
                    # print(f"要递归处理的field_name是<{field_name}>,准备递归更新children_fields")
                    # 生成更深一层的access_path
                    new_access_path = self.copy_and_extend_access_path(
                        original_access_path = access_path,
                        access_point = AccessPoint(
                            kind = ACCESS_POINT_KIND.FIELD_ELEMENT,
                            key = field_name
                        )
                    )
                    arg_state_fields[field_name] = _recursively_collect_children_fields(stmt_id, status, summary_states_fields[field_name], arg_state_fields[field_name], source_symbol_id, new_access_path)

            new_state: State = self.frame.symbol_state_space[new_state_index]
            new_state.fields = arg_state_fields
            new_state.state_type = state_type
            new_state.source_symbol_id = source_symbol_id
            new_state.access_path = access_path
            return return_set
        return _recursively_collect_children_fields(stmt_id, status, state_set_in_summary_field, state_set_in_arg_field, source_symbol_id, access_path)

    # 用形参的last_states去更新传入的实参
    def apply_parameter_summary_to_args_states(
        self, stmt_id, status: StmtStatus, last_states, old_arg_state_index, old_to_new_arg_state,
        parameter_symbol_id = -1, callee_id = -1, deferred_index_updates = None, old_to_latest_old_arg_state = None
    ):
        if util.is_empty(old_to_latest_old_arg_state):
            old_to_latest_old_arg_state = {}

        if old_arg_state_index not in old_to_new_arg_state:
            latest_old_arg_index = self.resolver.retrieve_latest_states(
                self.frame, stmt_id, self.frame.symbol_state_space,{old_arg_state_index},
                self.frame.state_bit_vector_manager.explain(status.in_state_bits), old_to_latest_old_arg_state
            ).pop()
            new_arg_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, latest_old_arg_index)
            old_to_new_arg_state[old_arg_state_index] = new_arg_state_index
            status.defined_states.add(new_arg_state_index)
        else:
            new_arg_state_index = old_to_new_arg_state[old_arg_state_index]
        new_arg_state: State = self.frame.symbol_state_space[new_arg_state_index]
        # print(f"old_arg_state_index: {old_arg_state_index}")
        # print(f"new_arg_state_index: {new_arg_state_index}")
        state_array: list[set] = []
        tangping_flag = False
        tangping_elements = set()
        callee_state_fields = {}
        for each_state_index in last_states:
            each_last_state = self.frame.symbol_state_space[each_state_index]
            if not (each_last_state and isinstance(each_last_state, State)):
                continue

            if each_last_state.tangping_flag:
                tangping_flag = True
                tangping_elements.update(each_last_state.tangping_elements)

            # collect all array of all states in summary
            each_last_state_array = each_last_state.array
            for index in range(len(each_last_state_array)):
                util.add_to_list_with_default_set(state_array, index, each_last_state_array[index])
            # 如果callee的array_state有anything(来自于callee外部)，则需要去caller中找到对应的concrete_state
            state_array_copy = copy.deepcopy(state_array)
            for index in range(len(state_array_copy)):
                array_states = state_array_copy[index]
                for each_array_state_index in array_states:
                    each_array_state = self.frame.symbol_state_space[each_array_state_index]
                    if each_array_state.state_type == STATE_TYPE_KIND.ANYTHING:
                        self.resolver.resolve_anything_in_summary_generation(each_array_state_index, self.frame, stmt_id, callee_id, set_to_update=state_array[index])

            # collect all fields of all states in summary
            each_state_fields = each_last_state.fields.copy()
            for field_name in each_state_fields:
                util.add_to_dict_with_default_set(callee_state_fields, field_name, each_state_fields[field_name])

            new_array = new_arg_state.array.copy()
            for index in range(len(state_array)):
                util.add_to_list_with_default_set(new_array, index, state_array[index])
            new_arg_state.array = new_array

            new_arg_state.tangping_flag |= tangping_flag
            # [未测]
            for each_tangping_element_index in tangping_elements.copy():
                each_tangping_element = self.frame.symbol_state_space[each_tangping_element_index]
                if each_tangping_element.state_type == STATE_TYPE_KIND.ANYTHING:
                    self.resolver.resolve_anything_in_summary_generation(each_tangping_element_index, self.frame, stmt_id, callee_id, set_to_update=tangping_elements)
            new_arg_state.tangping_elements.update(tangping_elements)
            # print(f"new_arg_state: {new_arg_state}")
            # print(f"new_arg_state_index: {new_arg_state_index}")
        # print(f"new_arg_state: {new_arg_state}")

        new_arg_state_fields = new_arg_state.fields
        arg_base_access_path = new_arg_state.access_path
        # print(f"\napply_parameter_fields开始\ncallee_state_field: {callee_state_fields}")
        # print(f"new_arg_state_fields1: {new_arg_state_fields}")
        for field_name in callee_state_fields:
            if field_name not in new_arg_state_fields:
                new_arg_state_fields[field_name] = callee_state_fields[field_name]
            else:
                # TODO：填充a.f的data_type可能有哪些。这需要遍历callee_state_fields.f和arg_state_fields.f
                access_path = self.copy_and_extend_access_path(
                    original_access_path = arg_base_access_path,
                    access_point = AccessPoint(
                        kind = ACCESS_POINT_KIND.FIELD_ELEMENT,
                        key = field_name
                    )
                )
                new_arg_state_fields[field_name] = self.recursively_collect_children_fields(
                    stmt_id, status, callee_state_fields[field_name], new_arg_state_fields[field_name],
                    parameter_symbol_id, access_path
                    )
        # print(f"new_arg_state_fields2: {new_arg_state_fields}")
        # print(f"new_arg_state_index {new_arg_state_index}")

        # [rn]如果callee的field_state有anything，则需要去caller中找到对应的concrete_state
        # TODO：暂时只考虑了field
        for field_name, field_states in copy.deepcopy(new_arg_state_fields).items():
            for each_field_state_index in field_states:
                each_field_state = self.frame.symbol_state_space[each_field_state_index]
                if each_field_state.state_type == STATE_TYPE_KIND.ANYTHING:
                    # if config.DEBUG_FLAG:
                    #     print(f"\n\napply_parameter时, each_field_state {each_field_state_index} 是anything, field_name是{field_name}")
                    #     pprint.pprint(each_field_state)
                    #     print()
                    self.resolver.resolve_anything_in_summary_generation(
                        each_field_state_index, self.frame, stmt_id, callee_id, deferred_index_updates,
                        set_to_update = new_arg_state_fields[field_name], parameter_symbol_id = parameter_symbol_id
                    )

    def apply_this_symbol_semantic_summary(
        self, stmt_id, callee_summary: MethodSummaryTemplate,
        callee_space: SymbolStateSpace, instance_state_indexes:set[int],
        new_object_flag: bool
    ):
        # print("apply_this_symbol_semantic_summary@instance_state_indexes",instance_state_indexes)
        if util.is_empty(instance_state_indexes):
            return
        status = self.frame.stmt_id_to_status[stmt_id]
        old_to_new_arg_state = {}
        this_symbols = callee_summary.this_symbols
        # 收集callee_summary中this_symbols的last_states，并应用到实际传入的instance_state中。
        for this_symbol_id in this_symbols:
            this_symbol_last_states = this_symbols.get(this_symbol_id, [])
            last_states:set[State] = set()
            last_state_indexes = set()

            for index_pair in this_symbol_last_states:
                new_index = index_pair.new_index
                index_in_appended_space = callee_space.old_index_to_new_index[new_index]
                each_this_symbol_last_state = self.frame.symbol_state_space[index_in_appended_space]
                last_states.add(each_this_symbol_last_state)
                last_state_indexes.add(index_in_appended_space)
            # print("apply_this_symbol_semantic_summary@this_last_state_indexes",last_state_indexes)

            for instance_state_index_in_space in instance_state_indexes.copy():
                # 将summary中的this_symbol_last_state应用到实际的instance_state上
                self.apply_parameter_summary_to_args_states(stmt_id, status, last_state_indexes, instance_state_index_in_space, old_to_new_arg_state)

        # 如果caller是通过new_object_stmt调用到callee的，就不应该将以上对this的修改添加到caller的summary中
        if new_object_flag:
            return

        new_this_states = set()
        for old_state in old_to_new_arg_state:
            new_this_states.add(old_to_new_arg_state[old_state])
        if not new_this_states:
            return
        # print("apply_this_symbol_semantic_summary@new_this_states",new_this_states)

        this_symbol_id = self.frame.method_def_use_summary.this_symbol_id
        index_to_add = self.frame.symbol_state_space.add(
            Symbol(
                stmt_id = stmt_id,
                name = LIAN_INTERNAL.THIS,
                symbol_id = this_symbol_id,
                states = new_this_states
            )
        )
        index_pair_set = set()
        for index in new_this_states:
            index_pair_set.add(IndexMapInSummary(index, -1))
        util.add_to_dict_with_default_set(self.frame.method_summary_template.this_symbols, this_symbol_id, index_pair_set)
        util.add_to_dict_with_default_set(self.frame.method_summary_instance.this_symbols, this_symbol_id, index_pair_set)
        status.implicitly_defined_symbols.append(index_to_add)

    def apply_parameter_semantic_summary(
        self, stmt_id, callee_id, callee_summary: MethodSummaryTemplate,
        callee_space: SymbolStateSpace, parameter_mapping_list: list[ParameterMapping]
    ):
        status = self.frame.stmt_id_to_status[stmt_id]
        old_to_new_arg_state = {}
        old_to_latest_old_arg_state = {}
        deferred_index_updates = set()
        for each_mapping in parameter_mapping_list:
            # state_array: list[set] = []
            # state_fields: dict[str, set] = {}
            last_states: set[State] = set()
            last_state_indexes = set()
            if each_mapping.is_default_value:
                default_value_state_type = STATE_TYPE_KIND.REGULAR
                parameter_symbol_id = each_mapping.parameter_symbol_id # 直接取parameter_symbol的last_states
                default_value_symbol_id = each_mapping.arg_state_id
                for index_pair in callee_summary.parameter_symbols.get(parameter_symbol_id, []):
                    new_index = index_pair.new_index
                    index_in_appended_space = callee_space.old_index_to_new_index[new_index]
                    each_default_value_last_state = self.frame.symbol_state_space[index_in_appended_space]
                    if not (each_default_value_last_state and isinstance(each_default_value_last_state, State)):
                        continue

                    if default_value_state_type != STATE_TYPE_KIND.ANYTHING:
                        if each_default_value_last_state.state_type == STATE_TYPE_KIND.ANYTHING:
                            default_value_state_type = STATE_TYPE_KIND.ANYTHING

                    last_states.add(each_default_value_last_state)
                    last_state_indexes.add(index_in_appended_space)

                tmp_default_value_state_index = self.create_state_and_add_space(status, stmt_id, state_type = default_value_state_type)
                self.apply_parameter_summary_to_args_states(stmt_id, status, last_state_indexes, tmp_default_value_state_index, old_to_new_arg_state)
                new_default_value_state_index = old_to_new_arg_state[tmp_default_value_state_index]
                if default_value_symbol_id not in self.frame.all_local_symbol_ids:
                    util.add_to_dict_with_default_set(
                        self.frame.method_summary_template.defined_external_symbols,
                        default_value_symbol_id,
                        IndexMapInSummary(raw_index=new_default_value_state_index, new_index=-1)
                    )
                index_to_add = self.frame.symbol_state_space.add(
                    Symbol(
                        stmt_id = stmt_id,
                        symbol_id = default_value_symbol_id,
                        states = {new_default_value_state_index}
                    )
                )
                status.defined_states.discard(tmp_default_value_state_index)
                status.implicitly_defined_symbols.append(index_to_add)
                continue

            if each_mapping.arg_source_symbol_id == -1:
                continue

            parameter_symbol_id = each_mapping.parameter_symbol_id
            parameter_symbols = callee_summary.parameter_symbols
            parameter_last_states = parameter_symbols.get(parameter_symbol_id, [])
            # print(f"parameter_last_states: {parameter_last_states}")

            for index_pair in parameter_last_states:
                new_index = index_pair.new_index
                index_in_appended_space = callee_space.old_index_to_new_index[new_index]
                each_parameter_last_state = self.frame.symbol_state_space[index_in_appended_space]
                if not (each_parameter_last_state and isinstance(each_parameter_last_state, State)):
                    continue

                if each_mapping.parameter_type == LIAN_INTERNAL.PARAMETER_DECL:
                    last_states.add(each_parameter_last_state)
                    last_state_indexes.add(index_in_appended_space)

                elif each_mapping.parameter_type == LIAN_INTERNAL.PACKED_POSITIONAL_PARAMETER:
                    parameter_access_path = each_mapping.parameter_access_path
                    parameter_index_in_array = parameter_access_path.key
                    if len(each_parameter_last_state.array) > parameter_index_in_array:
                        last_state_index_set = each_parameter_last_state.array[parameter_index_in_array]
                        for last_state_index in last_state_index_set:
                            last_states.add(self.frame.symbol_state_space[last_state_index])
                            last_state_indexes.add(last_state_index)

                elif each_mapping.parameter_type == LIAN_INTERNAL.PACKED_NAMED_PARAMETER:
                    parameter_access_path = each_mapping.parameter_access_path
                    parameter_field_name = parameter_access_path.key
                    last_state_index_set = each_parameter_last_state.fields.get(parameter_field_name, set())
                    for last_state_index in last_state_index_set:
                        last_states.add(self.frame.symbol_state_space[last_state_index])
                        last_state_indexes.add(last_state_index)

            self.apply_parameter_summary_to_args_states(
                stmt_id, status, last_state_indexes, each_mapping.arg_index_in_space, old_to_new_arg_state,
                parameter_symbol_id, callee_id, deferred_index_updates, old_to_latest_old_arg_state
            )
        # print(f"\n\n\n\n\n\\\\\\\\\\\\\\apply_parameter延迟更新 \ndeferred_index_updates")
        # pprint.pprint(deferred_index_updates)
        # print(f"old_to_new_arg_state {old_to_new_arg_state}")
        self.resolver.update_deferred_index(old_to_new_arg_state, deferred_index_updates, self.frame.symbol_state_space)

    def apply_other_semantic_summary(
        self, stmt_id, callee_id, status: StmtStatus, callee_summary: MethodSummaryTemplate,
        callee_compact_space: SymbolStateSpace, parameter_mapping_list: list[ParameterMapping], this_state_set: set = set()
    ):
        target_index = status.defined_symbol
        target_symbol = self.frame.symbol_state_space[target_index]
        if not isinstance(target_symbol, Symbol):
            return P2ResultFlag()

        return_state_index_set = set()
        for _, return_states in callee_summary.return_symbols.items():
            for index_pair in return_states:
                each_return_state_index = index_pair.new_index
                if each_return_state_index == -1:
                    continue

                return_state_index_set.add(
                    callee_compact_space.old_index_to_new_index[each_return_state_index]
                )

        target_symbol.states.update(return_state_index_set)
        status.defined_states.update(return_state_index_set)

        for callee_defined_external_symbol_id, defined_external_states in callee_summary.defined_external_symbols.items():
            new_defined_external_states = set()
            for index_pair in defined_external_states:
                defined_external_state = index_pair.new_index
                if defined_external_state == -1:
                    continue

                new_state_index = callee_compact_space.old_index_to_new_index[defined_external_state]
                new_defined_external_states.add(new_state_index)

                if callee_defined_external_symbol_id not in self.frame.all_local_symbol_ids:
                    util.add_to_dict_with_default_set(
                        self.frame.method_summary_template.defined_external_symbols,
                        callee_defined_external_symbol_id,
                        IndexMapInSummary(raw_index=new_state_index, new_index=-1)
                    )

            index_to_add = self.frame.symbol_state_space.add(
                Symbol(
                    stmt_id = stmt_id,
                    symbol_id = callee_defined_external_symbol_id,
                    states = new_defined_external_states
                )
            )

            status.implicitly_defined_symbols.append(index_to_add)

    def apply_callee_semantic_summary(
        self, stmt_id, callee_id, args: MethodCallArguments,
        callee_summary, callee_compact_space: SymbolStateSpace,
        this_state_set: set = set(), new_object_flag = False
        ):
        # print("---开始apply_callee_semantic_summary---")
        # print("callee_id", callee_id, self.loader.convert_method_id_to_method_name(callee_id))
        # print("callee_summary")
        # pprint.pprint(callee_summary)
        # print("callee_compact_space")
        # print(len(callee_compact_space))
        # pprint.pprint(callee_compact_space)

        status = self.frame.stmt_id_to_status[stmt_id]
        # append callee space to caller space
        self.frame.symbol_state_space.append_space_copy(callee_compact_space)

        # add necessary state in defined_states
        top_state_index_set = set()
        for each_summary in [callee_summary.parameter_symbols, callee_summary.defined_external_symbols, callee_summary.return_symbols]:
            if util.is_empty(each_summary):
                continue
            for symbol_id in each_summary:
                index_pair_set = each_summary[symbol_id]
                top_state_index_set.update(
                    {callee_compact_space.old_index_to_new_index[each_index_pair.new_index] for each_index_pair in index_pair_set}
                )

        work_list = SimpleWorkList(top_state_index_set)
        state_visited = set()
        defined_states = set()
        defined_state_id_set = set()
        # 将summary中涉及到的所有states(包括children states)加入到defined_states中
        while len(work_list) != 0:
            current_state_index = work_list.pop()
            if current_state_index in state_visited:
                continue
            state_visited.add(current_state_index)

            defined_states.add(current_state_index)
            current_state: State = self.frame.symbol_state_space[current_state_index]
            defined_state_id_set.add(current_state.state_id)
            for each_array_item in current_state.array:
                work_list.add(each_array_item)
            for each_field_item in current_state.fields.values():
                work_list.add(each_field_item)
            if current_state.tangping_flag:
                work_list.add(current_state.tangping_elements)
        old_defined_states = status.defined_states.copy()
        # 移除旧status.defined_states中和新defined_states同state_id的states
        for each_state_index in old_defined_states:
            if self.frame.symbol_state_space.convert_state_index_to_state_id(each_state_index) in defined_state_id_set:
                status.defined_states.discard(each_state_index)
        status.defined_states.update(defined_states)
        # print("apply_callee_semantic_summary中, 添加的status.defined_states:",status.defined_states)

        # mapping parameter and argument
        caller_id = self.frame.method_id
        call_stmt_id = stmt_id
        # print(f"load_parameter_mapping: {callee_id, caller_id, call_stmt_id}")
        if self.analysis_phase_id == 2:
            parameter_mapping_list = self.loader.get_parameter_mapping_p2((caller_id, call_stmt_id, callee_id))
        else:
            parameter_mapping_list = self.loader.get_parameter_mapping_p3((caller_id, call_stmt_id, callee_id))
        # apply parameter's state in callee_summary to args
        self.apply_parameter_semantic_summary(
            stmt_id, callee_id, callee_summary, callee_compact_space, parameter_mapping_list
        )

        # apply this_symbol's state in callee_summary to this_state_set
        self.apply_this_symbol_semantic_summary(
            stmt_id, callee_summary, callee_compact_space, this_state_set, new_object_flag
        )

        # apply other callee_summary to args
        self.apply_other_semantic_summary(
            stmt_id, callee_id, status, callee_summary, callee_compact_space, this_state_set
        )

        if callee_summary.dynamic_call_stmts:
            self.frame.method_summary_template.dynamic_call_stmts.add(stmt_id)

    def trigger_extern_callee(
        self, stmt_id, stmt, status: StmtStatus, in_states, unsolved_callee_states, name_symbol, defined_symbol, args
    ):
        p2result_flag = P2ResultFlag()
        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_EXTERN_CALLEE,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "frame": self.frame,
                "in_states": in_states,
                "state_analysis": self,
                "callee_symbol": name_symbol,
                "unsolved_callee_states": unsolved_callee_states,
                "defined_symbol": defined_symbol,
                "args": args,
                "p2result_flag": p2result_flag,
                "loader": self.loader,
            }
        )
        app_return = self.event_manager.notify(event)
        if hasattr(event.out_data, "interruption_flag") and event.out_data.interruption_flag:
            return event.out_data

        if er.is_event_unprocessed(app_return):
            unsolved_state_index = self.create_state_and_add_space(
                    status, stmt_id,
                    source_symbol_id=defined_symbol.symbol_id,
                    state_type = STATE_TYPE_KIND.UNSOLVED,
                    data_type = util.read_stmt_field(stmt.data_type), # LianInternal.RETURN_VALUE,
                    access_path=[AccessPoint(
                        kind=ACCESS_POINT_KIND.CALL_RETURN,
                        key=util.read_stmt_field(defined_symbol.name)
                    )]
                )
            self.update_access_path_state_id(unsolved_state_index)
            defined_symbol.states = {unsolved_state_index}

        return None



    def call_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        call_stmt   target  name    return_type prototype   args
        target = name(args)

        call_stmt: target = name(positional_args, named_args)

        =============================

        1. generate summary
        2. parse args
        3. parse parameters
        4. apply the summary to args and parameters
        """
        defined_symbol_index = status.defined_symbol
        defined_symbol = self.frame.symbol_state_space[defined_symbol_index]

        name_index = status.used_symbols[0]
        name_symbol = self.frame.symbol_state_space[name_index]
        if not isinstance(name_symbol, Symbol):
            return P2ResultFlag()

        name_states = self.read_used_states(name_index, in_states)

        unsolved_callee_states = set()

        args = self.prepare_args(stmt_id, stmt, status, in_states)
        callee_info = self.frame.stmt_id_to_callee_info.get(stmt_id)

        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_CALL_STMT_BEFORE,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "frame": self.frame,
                "in_states": in_states,
                "defined_symbol": defined_symbol,
                "state_analysis": self,
                "args": args,
                "name_states": name_states,
                "space": self.frame.symbol_state_space,
            }
        )
        # 方便debug
        callee_name = self.resolver.recover_callee_name(stmt_id, self.frame)
        app_return = self.event_manager.notify(event)
        if er.should_block_event_requester(app_return):
            return P2ResultFlag()
        if util.is_empty(callee_info):
            result = self.trigger_extern_callee(
                stmt_id, stmt, status, in_states, unsolved_callee_states, name_symbol, defined_symbol, args
            )
            if util.is_available(result):
                return result
            return P2ResultFlag()

        callee_type = callee_info.callee_type
        callee_method_ids = set()
        callee_class_ids = set()
        this_state_set = set()
        for each_state_index in name_states:
            each_state = self.frame.symbol_state_space[each_state_index]
            if not isinstance(each_state, State):
                continue

            if each_state.state_type == STATE_TYPE_KIND.ANYTHING:
                self.tag_key_state(stmt_id, name_symbol.symbol_id, each_state_index)

            if self.is_state_a_method_decl(each_state):
                if each_state.value:
                    source_state_id = each_state.source_state_id
                    # 如果是state1.func()的形式，要去找state1
                    if source_state_id != each_state.state_id:
                        this_state_set.update(
                            self.resolver.obtain_parent_states(stmt_id, self.frame, status, each_state_index)
                        )
                    if callee_id := util.str_to_int(each_state.value):
                        callee_method_ids.add(callee_id)

            #  what if it calls class_constructor.  e.g., o = A()
            elif self.is_state_a_class_decl(each_state) or each_state.data_type == LIAN_INTERNAL.THIS:
                return self.new_object_stmt_state(stmt_id, stmt, status, in_states)

            else:
                unsolved_callee_states.add(each_state_index)

        # call plugin to deal with undefined_callee_error
        # if len(unsolved_callee_states) != 0:
        if len(callee_method_ids) == 0 or self.is_abstract_method(callee_method_ids):
            out_data = self.trigger_extern_callee(
                stmt_id, stmt, status, in_states, unsolved_callee_states, name_symbol, defined_symbol, args
            )
            if util.is_available(out_data):
                if hasattr(out_data, "callee_method_ids"):
                    callee_method_ids.update(out_data.callee_method_ids)
                else:
                    return out_data
        return self.compute_target_method_states(
            stmt_id, stmt, status, in_states, callee_method_ids, defined_symbol, args, this_state_set
        )

    def is_abstract_method(self, callee_method_ids):
        for stmt_id in callee_method_ids:
            stmt = self.loader.get_stmt_gir(stmt_id)
            # why stmt.attrs is nan
            if isinstance(stmt.attrs, str) and 'abstractmethod' in stmt.attrs:
                return True
        return False

    def compute_target_method_states(
        self, stmt_id, stmt, status, in_states,
        callee_method_ids, defined_symbol, args,
        this_state_set = set(), new_object_flag = False
    ):
        # Compute callees' summaries
        # TODO 如果method_id空，退出
        # print(f"第二阶段 compute_target_method_states callee_ids {callee_method_ids}")
        callee_ids_to_be_analyzed = []
        caller_id = self.frame.method_id
        call_stmt_id = stmt_id
        if config.DEBUG_FLAG:
            util.debug(f"positional_args of stmt <{stmt_id}>: {args.positional_args}")
            util.debug(f"named_args of stmt <{stmt_id}>: {args.named_args}")

        for each_callee_id in callee_method_ids:
            if not (each_callee_id in self.analyzed_method_list or self.frame_stack.has_method_id(each_callee_id)):
                callee_ids_to_be_analyzed.append(each_callee_id)
            # prepare callee parameters
            parameters = self.prepare_parameters(each_callee_id)
            if config.DEBUG_FLAG:
                util.debug(f"parameters of callee <{each_callee_id}>: {parameters}\n")
            new_call_site = (caller_id, stmt_id, each_callee_id)
            callee_method_def_use_summary:MethodDefUseSummary = self.loader.get_method_def_use_summary(each_callee_id)
            parameter_mapping_list = self.loader.get_parameter_mapping_p2(new_call_site)
            if util.is_empty(parameter_mapping_list):
                parameter_mapping_list = []
                self.map_arguments(args, parameters, parameter_mapping_list, new_call_site, 2)

        if len(callee_ids_to_be_analyzed) != 0:
            self.frame.stmts_with_symbol_update.add(stmt_id)
            if config.DEBUG_FLAG:
                util.debug(f"callee need to be analyzed: {callee_ids_to_be_analyzed}")

            return P2ResultFlag(
                interruption_flag = True,
                interruption_data = InterruptionData(
                    caller_id = self.frame.method_id,
                    call_stmt_id = stmt_id,
                    callee_ids = callee_ids_to_be_analyzed
                )
            )

        # Here we link args and parameters
        # argument : <position, name, symbol_id#1, states#1>
        #               ^        ^            ^             ^
        #               |        |            |             |
        #               v        v            v             v
        # parameter: <position, name, symbol_id#2, states#2>
        #            \__________________________________________/
        #                             |
        #                             v
        # Summary  :      state-level semantic summary

        if len(callee_method_ids) == 0:
            name_index = status.used_symbols[0]
            name_symbol = self.frame.symbol_state_space[name_index]
            return_access_path = []
            for index in name_symbol.states:
                name_state = self.frame.symbol_state_space[index]
                if len(name_state.access_path) == 0:
                    continue
                return_access_path = copy.deepcopy(name_state.access_path)
            return_access_path.append(AccessPoint(
                    kind=ACCESS_POINT_KIND.CALL_RETURN,
                    key=name_symbol.name
                ))
            unsolved_state_index = self.create_state_and_add_space(
                status, stmt_id,
                source_symbol_id=defined_symbol.symbol_id,
                state_type = STATE_TYPE_KIND.UNSOLVED,
                data_type = util.read_stmt_field(stmt.data_type), # LianInternal.RETURN_VALUE,
                access_path=return_access_path
            )
            self.update_access_path_state_id(unsolved_state_index)
            defined_symbol.states = {unsolved_state_index}

            return P2ResultFlag()

        # args = self.prepare_args(stmt_id, stmt, status, in_states, args_state_set)
        # if config.DEBUG_FLAG:
        #     util.debug(f"positional_args of stmt <{stmt_id}>: {args.positional_args}")
        #     util.debug(f"named_args of stmt <{stmt_id}>: {args.named_args}")

        for each_callee_id in callee_method_ids:
            if self.call_graph:
                if not self.call_graph.has_specific_weight(self.frame.method_id, each_callee_id, stmt_id):
                    # print(f"add edge: {self.frame.method_id} -> {each_callee_id} @ {stmt_id}")
                    self.call_graph.add_edge(int(self.frame.method_id), int(each_callee_id), int(stmt_id))

            # prepare callee summary template and compact space
            callee_summary = self.loader.get_method_summary_template(each_callee_id)
            if util.is_empty(callee_summary):
                # print(f"\neach_callee_id: {each_callee_id}")
                continue
            callee_summary = callee_summary.copy()

            callee_compact_space: SymbolStateSpace = self.loader.get_symbol_state_space_summary_p2(each_callee_id)
            if util.is_empty(callee_compact_space):
                continue
            callee_compact_space = callee_compact_space.copy()

            # apply callee semantic summary
            self.apply_callee_semantic_summary(
                stmt_id, each_callee_id, args, callee_summary,
                callee_compact_space, this_state_set, new_object_flag
            )

        return P2ResultFlag()

    def global_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        global_stmt name
        def: name
        """
        global_symbol_index = status.defined_symbol
        # self.frame_stack.global_bit_vector_manager.add_bit_id()
        global_symbol = self.frame.symbol_state_space[global_symbol_index]
        if not isinstance(global_symbol, Symbol):
            return P2ResultFlag()

        state_index = self.create_state_and_add_space(
                status, stmt_id, source_symbol_id=global_symbol.symbol_id,
            data_type = util.read_stmt_field(stmt.data_type),
            state_type = STATE_TYPE_KIND.ANYTHING,
            access_path=[AccessPoint(
                kind=ACCESS_POINT_KIND.EXTERNAL,
                key=util.read_stmt_field(stmt.name),
            )]
        )
        self.update_access_path_state_id(state_index)
        global_symbol.states = {state_index}

        return P2ResultFlag()

    def nonlocal_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        nonlocal_stmt   name
        def: name
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        state_index = self.create_state_and_add_space(
            status, stmt_id,
            source_symbol_id=defined_symbol.symbol_id,
            data_type = util.read_stmt_field(stmt.data_type),
            state_type = STATE_TYPE_KIND.ANYTHING,
            access_path=[AccessPoint(
                kind=ACCESS_POINT_KIND.EXTERNAL,
                key=util.read_stmt_field(stmt.name),
            )]
        )
        self.update_access_path_state_id(state_index)
        defined_symbol.states = {state_index}

        return P2ResultFlag()

    # TODO:
    def type_cast_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        type_cast_stmt  target  data_type   source  error   cast_action
        def: target data_type
        use: source
        target = (data_type)source
        """
        source_symbol_index = status.used_symbols[0]
        source_states = self.read_used_states(source_symbol_index, in_states)

        defined_index = status.defined_symbol
        defined_symbol = self.frame.symbol_state_space[defined_index]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        data_type = util.read_stmt_field(stmt.data_type)

        defined_states = set()
        for source_state_index in source_states:
            source_state = self.frame.symbol_state_space[source_state_index]
            if not isinstance(source_state, State):
                continue

            new_source_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, source_state_index)
            new_source_state: State = self.frame.symbol_state_space[new_source_state_index]
            new_source_state.data_type = str(data_type)
            defined_states.add(new_source_state_index)

        defined_symbol.states = defined_states
        return P2ResultFlag()

    # TODO:
    def type_alias_decl_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        type_alias_decl target source
        typedef source target
        """
        source_symbol_index = status.used_symbols[0]
        source_symbol = self.frame.symbol_state_space[source_symbol_index]
        if not isinstance(source_symbol, Symbol):
            return P2ResultFlag()

        defined_index = status.defined_symbol
        defined_symbol = self.frame.symbol_state_space[defined_index]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        data_type = util.read_stmt_field(stmt.data_type)
        defined_symbol.states = {
            self.create_state_and_add_space(
                status, stmt_id, source_symbol_id=source_symbol.symbol_id,
                data_type = str(data_type)
            )
        }
        return P2ResultFlag()

    def phi_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        phi_stmt    target  phi_values  phi_labels
        def: target
        use: phi_values
        target = [phi_value, phi_label]
        """
        used_symbol_indexes = status.used_symbols
        defined_index = status.defined_symbol
        defined_symbol = self.frame.symbol_state_space[defined_index]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        for each_index in used_symbol_indexes:
            states = self.read_used_states(each_index, in_states)
            defined_symbol.states.update(states)

        return P2ResultFlag()

    def namespace_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        namespace_decl  name    body
        def: name
        use:
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        index = self.create_state_and_add_space(
            status, stmt_id,
            source_symbol_id=defined_symbol.symbol_id,
            data_type = LIAN_INTERNAL.NAMESPACE_DECL,
            value = stmt_id,
            access_path=[AccessPoint(
                key = util.read_stmt_field(stmt.name),
            )]
        )
        self.update_access_path_state_id(index)
        defined_symbol.states = {index}
        return P2ResultFlag()

    def class_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        class_decl  attrs    name    supers  static_init init    fields  methods nested
        def: name
        use:
        for x in []:
            int i = 10
            A a = new A()
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        index = self.create_state_and_add_space(
            status, stmt_id,
            source_symbol_id=defined_symbol.symbol_id,
            data_type = LIAN_INTERNAL.CLASS_DECL,
            value = stmt_id,
            access_path=[AccessPoint(
                key = util.read_stmt_field(stmt.name),
            )]
        )
        self.update_access_path_state_id(index)
        defined_symbol.states = {index}

        return P2ResultFlag()

    def parameter_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        parameter_decl  attrs    data_type   name    default_value
        def: name
        use: default_value
        """
        parameter_name_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if isinstance(parameter_name_symbol, Symbol):
            parameter_state_index = self.create_state_and_add_space(
                status, stmt_id,
                source_symbol_id = parameter_name_symbol.symbol_id,
                data_type = util.read_stmt_field(stmt.data_type),
                state_type = STATE_TYPE_KIND.ANYTHING,
                access_path=[AccessPoint(
                    key = util.read_stmt_field(stmt.name),
                )]
            )
            self.update_access_path_state_id(parameter_state_index)
            parameter_name_symbol.states = {parameter_state_index}

            if len(status.used_symbols) > 0:
                default_value_index = status.used_symbols[0]
                default_value = self.frame.symbol_state_space[default_value_index]
                if isinstance(default_value, Symbol):
                    value_state_indexes = self.read_used_states(default_value_index, in_states)
                    for default_value_state_index in value_state_indexes:
                        # self.tag_key_state(stmt_id, default_value.symbol_id, default_value_state_index)
                        util.add_to_dict_with_default_set(
                            self.frame.method_summary_template.used_external_symbols,
                            default_value.symbol_id,
                            IndexMapInSummary(default_value_state_index, -1)
                        )

                else:
                    parameter_name_symbol.states.add(default_value_index)
        return P2ResultFlag()

    def variable_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        variable_decl   attrs    data_type   name
        def: name
        use:
        """
        # variable_name_symbol: Symbol = self.frame.symbol_state_space[status.defined_symbol]
        # variable_state_index = self.create_state_and_add_space(
        #     status, stmt_id,
        #     source_symbol_id=variable_name_symbol.symbol_id,
        #     data_type = util.read_stmt_field(stmt.data_type),
        #     state_type = StateTypeKind.UNINIT,
        #     access_path=[AccessPoint(
        #         key = util.read_stmt_field(stmt.name),
        #     )]
        # )
        # self.update_access_path(variable_state_index)
        # variable_name_symbol.states = {variable_state_index}

        return P2ResultFlag()

    def method_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        method_decl attrs    data_type   name    parameters  body
        def: name
        use:
        """
        method_name_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if isinstance(method_name_symbol, Symbol):
            method_state_index = self.create_state_and_add_space(
                status,
                stmt_id,
                source_symbol_id=method_name_symbol.symbol_id,
                value = stmt_id,
                data_type = LIAN_INTERNAL.METHOD_DECL,
                access_path=[AccessPoint(
                    key = util.read_stmt_field(stmt.name),
                )]
            )
            self.update_access_path_state_id(method_state_index)
            method_name_symbol.states = {method_state_index}

        return P2ResultFlag()

    def new_object_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        new_object  type  attrs  name  args
        def: type
        use:
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()
        type_index = status.used_symbols[0]
        type_states = self.read_used_states(type_index, in_states)
        args = self.prepare_args(stmt_id, stmt, status, in_states)
        p2result_flag = P2ResultFlag()
        type_state_to_new_index = {}
        type_state_to_callee_methods = {}

        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_NEW_OBJECT_BEFORE,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "frame": self.frame,
                "in_states": in_states,
                "state_analysis": self,
                "defined_symbol": defined_symbol,
                "defined_states": defined_symbol.states,
                "type_states": type_states,
                "type_state_to_new_index":type_state_to_new_index,
                "type_state_to_callee_methods":type_state_to_callee_methods,
                "p2result_flag" : p2result_flag,
                "args":args
            }
        )
        app_return = self.event_manager.notify(event)

        # 如果需要先去分析callee，先中断
        if p2result_flag.interruption_flag:
            return p2result_flag

        if er.is_event_unprocessed(app_return):
            for each_state_index in type_states:
                each_state = self.frame.symbol_state_space[each_state_index]
                init_state_index = self.create_state_and_add_space(
                    status, stmt_id, source_symbol_id = defined_symbol.symbol_id,
                    data_type = LIAN_INTERNAL.CLASS_DECL, value=each_state.value,
                    access_path=[AccessPoint(
                        key = each_state.value,
                    )]
                )
                self.update_access_path_state_id(init_state_index)
                defined_symbol.states.add(init_state_index)

            # print("new_object_stmt_state@ create a default_state for new object", defined_symbol.states)

        p2result_flag = P2ResultFlag()
        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_NEW_OBJECT_AFTER,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "frame": self.frame,
                "in_states": in_states,
                "state_analysis": self,
                "defined_symbol": defined_symbol,
                "defined_states": defined_symbol.states,
                "type_states": type_states,
                "type_state_to_new_index":type_state_to_new_index,
                "type_state_to_callee_methods":type_state_to_callee_methods,
                "p2result_flag" : p2result_flag,
                "args":args
            }
        )
        self.event_manager.notify(event)
        return p2result_flag

    def new_array_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        new_array   target  attrs    data_type
        def: target
        use:
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()
        init_state_index = self.create_state_and_add_space(
            status, stmt_id, source_symbol_id=defined_symbol.symbol_id, data_type = LIAN_INTERNAL.ARRAY,
            access_path=[AccessPoint(
                key = util.read_stmt_field(stmt.data_type),
            )]
        )
        self.update_access_path_state_id(init_state_index)
        defined_symbol.states = {init_state_index}

        return P2ResultFlag()

    def new_record_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        new_record  target  attrs    data_type
        def: target
        use:
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        init_state_index = self.create_state_and_add_space(
            status, stmt_id, source_symbol_id=defined_symbol.symbol_id, data_type = LIAN_INTERNAL.RECORD,
            access_path=[AccessPoint(
                key = util.read_stmt_field(stmt.data_type),
            )]
        )
        self.update_access_path_state_id(init_state_index)
        defined_symbol.states = {init_state_index}
        return P2ResultFlag()

    def new_set_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        new_set target  attrs    data_type
        def: target
        use:
        """
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        init_state_index = self.create_state_and_add_space(
            status, stmt_id, source_symbol_id=defined_symbol.symbol_id, data_type = LIAN_INTERNAL.SET,
            access_path=[AccessPoint(
                key = util.read_stmt_field(stmt.data_type),
            )]
        )
        self.update_access_path_state_id(init_state_index)
        defined_symbol.states = {init_state_index}

        return P2ResultFlag()

    def addr_of_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        addr_of target  source
        def: target
        use: source
        target = &source  (source.id => target.state)
        if condition:
           a = 3  -> Symbol1: [0, a, state2(3)]
           p = &a -> p -> [0]
        else:
           a = 4  -> Symbol3: [4, a, state5(4)]
           p = &a -> p -> [4]
        c = *p    -> Symbol5: [c, [state2(3), state5(4)]]
        a = 5     -> Symbol5: [0, a, state4(4)]
        d = *p    -> Symbol5: [c, state4(4)]

        a = 3  -> Symbol1: [0, a, state2(3)]
        p = &a -> p -> [0]
        if.true a =
        a = 4  -> Symbol3: [0, a, state4(4)]
        c = *p -> Symbol5: [c, state4(4)]   <= Symbol1.states live at this moment bit_vector.in_bits
        a = 5  -> Symbol6: [0, a, state7(5)]
        """
        source_symbol_index = status.used_symbols[0]
        source_symbol: Symbol = self.frame.symbol_state_space[source_symbol_index]
        defined_symbol: Symbol = self.frame.symbol_state_space[status.defined_symbol]
        state_index = self.create_state_and_add_space(
            status, stmt_id, source_symbol_id=stmt_id, value=source_symbol.symbol_id,
            access_path = self.copy_and_extend_access_path(
                source_symbol.access_path,
                AccessPoint(kind = ACCESS_POINT_KIND.ADDR_OF)
            )
        )
        self.update_access_path_state_id(state_index)
        defined_symbol.states = {state_index}
        return P2ResultFlag()

    def mem_read_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        mem_read    target  address
        def: target
        use: address
        target = *address (find_symbol_by_id(address.state.value).state => target.state)
        """
        """
        int x;
        int *p;
        int **q;
        x = 20;
        p = &x;     <p, [ID(x)]>
        q = &p;     <q, [ID(p)]>
        y = **q;
        """
        address_index = status.used_symbols[0]
        address_symbol: Symbol = self.frame.symbol_state_space[address_index]
        old_id_list = self.obtain_states(address_index)
        address_id_list = self.read_used_states(address_index, in_states)

        print("address_id_list:", address_id_list)

        target_states = set()
        reachable_symbol_defs = self.frame.symbol_bit_vector_manager.explain(status.in_symbol_bits)
        for symbol_id_index in address_id_list:
            symbol_id_state = self.frame.symbol_state_space[symbol_id_index]
            if not isinstance(symbol_id_state, State):
                continue

            if symbol_id_state.value in self.frame.defined_symbols:
                index = self.create_state_and_add_space(
                    status, stmt_id, source_symbol_id=stmt_id, state_type = STATE_TYPE_KIND.UNSOLVED
                )
                target_states.add(index)
                continue

            if symbol_id_state.state_type == STATE_TYPE_KIND.ANYTHING:
                index = self.create_state_and_add_space(
                    status, stmt_id, source_symbol_id=symbol_id_state.symbol_id,
                    access_path = self.copy_and_extend_access_path(
                        symbol_id_state.access_path,
                        AccessPoint(
                            kind = ACCESS_POINT_KIND.MEM_READ
                        )
                    )
                )
                self.update_access_path_state_id(index)
                target_states.add(index)
                continue

            symbol_id = symbol_id_state.value
            all_defs = self.frame.defined_symbols[symbol_id]
            all_defs &= reachable_symbol_defs
            for def_stmt_id, def_source in all_defs:
                reachable_status = self.frame.stmt_id_to_status[def_stmt_id]
                defined_symbol = self.frame.symbol_state_space[reachable_status.defined_symbol]
                flag = True
                if util.is_available(defined_symbol) and defined_symbol.symbol_id == def_source:
                    target_states.update(defined_symbol.states)
                    flag = False
                if flag:
                    if def_source in reachable_status.implicitly_defined_symbols:
                        index = reachable_status.implicitly_defined_symbols[def_source]
                        defined_symbol = self.frame.symbol_state_space[index]
                        if util.is_available(defined_symbol):
                            target_states.update(defined_symbol.states)

        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        defined_symbol.states = target_states

        return P2ResultFlag()

    def mem_write_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        mem_write   address source
        def:
        use: address source
        *address = source (source.states => find_symbol_by_id(address.state).state)
        """
        address_symbol_index = status.used_symbols[0]
        source_symbol_index = status.used_symbols[1]
        # address_symbol = self.frame.symbol_state_space[address_symbol_index]
        # old_source_states = self.obtain_states(source_symbol_index)
        source_states = self.read_used_states(source_symbol_index, in_states)
        address_states = self.read_used_states(address_symbol_index, in_states)

        implicitly_defined_symbols = []

        reachable_defs = self.frame.symbol_bit_vector_manager.explain(status.in_symbol_bits)
        for state_index in address_states:
            state = self.frame.symbol_state_space[state_index]
            if util.is_empty(state):
                continue
            symbol_id = state.value
            if symbol_id not in self.frame.defined_symbols:
                #TODO: need to deal with such a case
                continue
            all_defs = self.frame.defined_symbols[symbol_id]
            all_defs &= reachable_defs

            for def_stmt_id, def_source in all_defs:
                target_status = self.frame.stmt_id_to_status[def_stmt_id]
                defined_symbol = self.frame.symbol_state_space[target_status.defined_symbol]
                if util.is_available(defined_symbol):
                    if defined_symbol.symbol_id == def_source:
                        new_symbol = defined_symbol.copy(stmt_id)
                        new_symbol.states = source_states
                        implicitly_defined_symbols[def_source] = self.frame.symbol_state_space.add(new_symbol)
                        continue

                if def_source in target_status.implicitly_defined_symbols:
                    index = target_status.implicitly_defined_symbols[def_source]
                    defined_symbol = self.frame.symbol_state_space[index]
                    if util.is_available(defined_symbol):
                        new_symbol = defined_symbol.copy(stmt_id)
                        new_symbol.states = source_states
                        implicitly_defined_symbols[def_source] = self.frame.symbol_state_space.add(new_symbol)

        status.implicitly_defined_symbols = implicitly_defined_symbols

        return P2ResultFlag()

    def common_element_read_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        分发array / record / object 的read操作
        <array_read: target, array, index>
            def: target
            use: array, index
        <field_read: target, receiver_object, field>
            def: target
            use: receiver_object, field
        <record_read: 不存在>
        """
        # 统一建模为 receiver field
        # [例] target = receiver[field], target = receiver.field
        field_index = status.used_symbols[1]
        field_states = self.read_used_states(field_index, in_states)
        is_array_operation = False

        for field_state_id in field_states:
            field_state = self.frame.symbol_state_space[field_state_id]
            if not isinstance(field_state, State):
                continue

            if field_state.data_type == LIAN_INTERNAL.INT or isinstance(field_state.value, int):
                is_array_operation = True
                break

        if is_array_operation:
            return self.array_read_stmt_state(stmt_id, stmt, status, in_states)
        return self.field_read_stmt_state(stmt_id, stmt, status, in_states)

    def common_element_write_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        分发array / record / object 的write操作
        <array_write: array, index, source>
            def: array
            use: array, index, source
        <field_write: receiver_object, field, source>
            def: receiver_object
            use: receiver_object, field, source
        <record_write: receiver_symbol, key, value>
            def: receiver_record
            use: receiver_record, key, value
        """
        # 统一建模为 receiver field source
        # [例] receiver[field] = source, receiver.field = source
        field_index = status.used_symbols[1]
        field_states = self.read_used_states(field_index, in_states)
        is_array_operation = False
        for field_state_index in field_states:
            field_state = self.frame.symbol_state_space[field_state_index]
            if not isinstance(field_state, State):
                continue
            if re.match(r'^-?\d+$', (str(field_state.value))): # 判断field是不是一个数字
                is_array_operation = True
                break

        if is_array_operation:
            return self.array_write_stmt_state(stmt_id, stmt, status, in_states)
        return self.field_write_stmt_state(stmt_id, stmt, status, in_states)

    def array_read_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        array_read  target  array   index
        def: target
        use: array index
        target = array[index]
        """
        defined_states = set()
        new_array_symbol = None
        new_array_symbol_index = None

        array_symbol_index = status.used_symbols[0]
        index_symbol_index = status.used_symbols[1]
        used_array_symbol: Symbol = self.frame.symbol_state_space[array_symbol_index]
        if not isinstance(used_array_symbol, Symbol):
            return P2ResultFlag()

        array_state_indexes = self.read_used_states(array_symbol_index, in_states)
        index_state_indexes = self.read_used_states(index_symbol_index, in_states)
        for each_array_state_index in array_state_indexes:
            array_state = self.frame.symbol_state_space[each_array_state_index]
            if not isinstance(array_state, State):
                continue
            if isinstance(used_array_symbol, Symbol):
                self.tag_key_state(stmt_id, used_array_symbol.symbol_id, each_array_state_index)
            # 躺平，返回整个数组
            if array_state.tangping_flag:
                defined_states.update(array_state.tangping_elements)
                continue

            is_reading_success = True
            # for index_value in index_set:
            for index_state_id in index_state_indexes:
                index_state = self.frame.symbol_state_space[index_state_id]
                if not isinstance(index_state, State):
                    continue

                index_value = index_state.value
                if str(index_value).isdigit():
                    index_value = int(index_value)
                    array_length = len(array_state.array)

                    # 处理下标是负数时的情况
                    if index_value >= 0:
                        real_index_value = index_value
                    else:
                        real_index_value = array_length + index_value

                    if (
                        real_index_value >=0 and
                        real_index_value < array_length and
                        array_state.array[real_index_value]
                    ):
                        array_index_set: set = array_state.array[real_index_value]
                        for array_symbol_index in array_index_set:
                            defined_states.add(array_symbol_index)
                    else:
                        is_reading_success = False
                        break

            if is_reading_success:
                continue

            if util.is_empty(new_array_symbol_index):
                new_array_symbol_index = self.create_copy_of_symbol_and_add_space(status, stmt_id, used_array_symbol)
                new_array_symbol: Symbol = self.frame.symbol_state_space[new_array_symbol_index]

            new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_array_state_index)
            new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
            new_path: list = array_state.access_path.copy()
            new_path.append(AccessPoint(
                kind = ACCESS_POINT_KIND.ARRAY_ELEMENT,
                key = real_index_value
            ))
            source_index = self.create_state_and_add_space(
                status, stmt_id,
                source_symbol_id=array_state.source_symbol_id,
                source_state_id=array_state.source_state_id,
                state_type = STATE_TYPE_KIND.ANYTHING,
                access_path = new_path
            )
            self.update_access_path_state_id(source_index)

            self.make_state_tangping(new_array_state)
            new_array_state.tangping_elements.add(source_index)
            defined_states.update(new_array_state.tangping_elements)

            new_array_symbol.states.discard(each_array_state_index)
            new_array_symbol.states.add(new_array_state_index)

        target_symbol: Symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(target_symbol, Symbol):
            return P2ResultFlag()

        if target_symbol:
            target_symbol.states = defined_states

        return P2ResultFlag()

    def array_write_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        array_write array   index   source
        def: array
        use: array index source
        array[index] = source
        """
        array_index = status.used_symbols[0]
        index_index = status.used_symbols[1]
        source_index = status.used_symbols[2]

        array_states = self.read_used_states(array_index, in_states)
        index_states = self.read_used_states(index_index, in_states)
        source_states = self.read_used_states(source_index, in_states)

        defined_array_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_array_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol_states = set()

        for array_state_id in array_states:
            array_state = self.frame.symbol_state_space[array_state_id]
            if not (array_state and isinstance(array_state, State)):
                continue

            tangping_flag = array_state.tangping_flag
            if not tangping_flag:
                tmp_array = array_state.array.copy()
                for index_state_id in index_states:
                    index_state = self.frame.symbol_state_space[index_state_id]
                    if not isinstance(index_state, State):
                        continue

                    index_value = index_state.value
                    if isinstance(index_value, str):
                        # if not index_value.isdigit():
                        if not re.match(r'^-?\d+$', (str(index_value))):
                            tangping_flag = True
                            break
                        else:
                            index_value = int(index_value)

                    array_length = len(tmp_array)
                    # 处理下标是负数时的情况
                    if index_value >= 0:
                        real_index_value = index_value
                    else:
                        real_index_value = array_length + index_value

                    # 数组下标越界，将数组扩展
                    if not util.add_to_list_with_default_set(tmp_array, real_index_value, source_states):
                        tangping_flag = True

            if tangping_flag:
                new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, array_state_id, overwritten_flag = True)
                new_array_state: State = self.frame.symbol_state_space[new_array_state_index]

                self.make_state_tangping(new_array_state)
                new_array_state.tangping_elements.update(source_states)
                defined_symbol_states.add(new_array_state_index)

            elif tmp_array != array_state.array:
                new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, array_state_id, overwritten_flag = True)
                new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
                new_array_state.array = tmp_array
                defined_symbol_states.add(new_array_state_index)

        defined_array_symbol.states = defined_symbol_states

        return P2ResultFlag()


    def array_insert_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        array_insert    array   source  index
        def: array
        use: array source index
        """
        array_index = status.used_symbols[0]
        source_index = status.used_symbols[1]
        index_index = status.used_symbols[2]

        array_states = self.read_used_states(array_index, in_states)
        source_states = self.read_used_states(source_index, in_states)
        index_states = self.read_used_states(index_index, in_states)

        defined_array_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_array_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol_states = set()

        for array_state_id in array_states:
            array_state = self.frame.symbol_state_space[array_state_id]
            if not (array_state and isinstance(array_state, State)):
                continue

            tmp_array = None

            tangping_flag = array_state.tangping_flag
            if not tangping_flag:
                tmp_array = array_state.array.copy()
                for index_state_id in index_states:
                    index_state = self.frame.symbol_state_space[index_state_id]
                    if not (index_state and isinstance(index_state, State)):
                        continue
                    index_value = index_state.value

                    if index_value.isdigit():
                        index_value = int(index_value)
                        array_length = len(tmp_array)

                        # 处理下标是负数时的情况
                        if index_value >= 0:
                            real_index_value = index_value
                        else:
                            real_index_value = array_length + index_value

                        # 数组下标越界，将数组扩展
                        if real_index_value >= array_length:
                            tmp_array.extend([set() for _ in range(real_index_value + 1 - array_length)])

                        tmp_array.insert(real_index_value, source_states)

                    # 下标值非法，将数组变成崩溃状态
                    else:
                        tangping_flag = True
                        break

            if tangping_flag:
                new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, array_state_id, overwritten_flag = True)
                new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
                self.make_state_tangping(new_array_state)
                new_array_state.tangping_elements.update(source_states)
                defined_symbol_states.add(new_array_state_index)

            elif tmp_array != array_state.array:
                new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, array_state_id, overwritten_flag = True)
                new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
                new_array_state.array = tmp_array
                defined_symbol_states.add(new_array_state_index)

        defined_array_symbol.states = defined_symbol_states
        return P2ResultFlag()

    def array_append_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        array_append: array source
        def: array
        use: array source
        array.append(source)
        """
        used_array_index = status.used_symbols[0]
        used_array_states: set = self.read_used_states(used_array_index, in_states)

        source_index = status.used_symbols[1]
        source_states: set = self.read_used_states(source_index, in_states)

        defined_array_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_array_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol_states = set()

        for array_state_index in used_array_states:
            array_state = self.frame.symbol_state_space[array_state_index]
            if not (array_state and isinstance(array_state, State)):
                continue

            new_target_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, array_state_index, overwritten_flag = True)
            new_target_state: State = self.frame.symbol_state_space[new_target_state_index]
            if array_state.tangping_flag:
                new_target_state.tangping_elements.update(source_states)
            else:
                new_target_state.array.append(source_states)
            defined_symbol_states.add(new_target_state_index)

        defined_array_symbol.states = defined_symbol_states

        return P2ResultFlag()

    def array_extend_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        array_extend: array, source
        def: array
        use: array source
        array.extend(source)
        """
        used_array_index = status.used_symbols[0]
        used_array = self.frame.symbol_state_space[used_array_index]
        used_array_states: set  = self.read_used_states(used_array_index, in_states)

        source_index = status.used_symbols[1]
        source_array = self.frame.symbol_state_space[used_array_index]
        source_states: set = self.read_used_states(source_index, in_states)

        defined_array_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_array_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol_states = set()

        array_state_to_extend: list[set] = []
        for target_state_index in used_array_states:
            target_state = self.frame.symbol_state_space[target_state_index]
            if not (target_state and isinstance(target_state, State)):
                continue

            for source_state_index in source_states:
                source_state = self.frame.symbol_state_space[source_state_index]
                if not(source_state and isinstance(source_state, State)):
                    continue

                tmp_array = source_state.array
                for index in range(len(tmp_array)):
                    array_length = len(array_state_to_extend)
                    util.add_to_list_with_default_set(array_state_to_extend, index, tmp_array[index])

            if array_state_to_extend:
                new_target_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, target_state_index, overwritten_flag = True)
                new_target_state: State = self.frame.symbol_state_space[new_target_state_index]
                if new_target_state.tangping_flag:
                    new_target_state.tangping_elements.update(array_state_to_extend)
                else:
                    new_target_state.array.extend(array_state_to_extend)
                defined_symbol_states.add(new_target_state_index)

        defined_array_symbol.states = defined_symbol_states
        return P2ResultFlag()

    def record_extend_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        record_extend: record, source
        def: record
        use: record source
        """
        receiver_state_index = status.used_symbols[0]
        receiver_symbol = self.frame.symbol_state_space[receiver_state_index]
        receiver_states = self.read_used_states(receiver_state_index, in_states)

        source_index = status.used_symbols[1]
        source = self.frame.symbol_state_space[source_index]
        source_states = self.read_used_states(source_index, in_states)

        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]# copy on write

        for each_receiver_state_index in receiver_states:
            each_receiver_state = self.frame.symbol_state_space[each_receiver_state_index]
            if not isinstance(each_receiver_state, State):
                continue

            for source_state_index in source_states:
                each_source_state = self.frame.symbol_state_space[source_state_index]
                if not isinstance(each_source_state, State):
                    continue
                if each_source_state.tangping_flag:
                    new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_receiver_state_index, overwritten_flag = True)
                    new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]
                    if each_receiver_state.tangping_flag:
                        self.make_state_tangping(new_receiver_state)
                    new_receiver_state.tangping_elements.update(each_source_state.tangping_elements)
                    defined_symbol.states.add(new_receiver_state_index)
                    continue

                if each_receiver_state.tangping_flag:
                    new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_receiver_state_index, overwritten_flag = True)
                    new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]
                    for each_field_set in each_source_state.fields.values():
                        new_receiver_state.tangping_elements.update(each_field_set)
                    defined_symbol.states.add(new_receiver_state_index)
                    continue

                new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_receiver_state_index, overwritten_flag = True)
                new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]
                for each_field in each_source_state.fields:
                    util.add_to_dict_with_default_set(new_receiver_state.fields, each_field, each_source_state.fields[each_field])
                defined_symbol.states.add(new_receiver_state_index)

        return P2ResultFlag()

    def assert_field_read_new_receiver_symbol(self, new_receiver_symbol_index, status, stmt_id, receiver_symbol):
        if util.is_empty(new_receiver_symbol_index):
            new_receiver_symbol_index = self.create_copy_of_symbol_and_add_space(status, stmt_id, receiver_symbol)
        return new_receiver_symbol_index

    def change_field_read_receiver_state(
        self, stmt_id, status, new_receiver_symbol_index, receiver_state_index, receiver_state,
        field_name, defined_states, is_tangping = False
    ):
        if receiver_state.tangping_elements:
            defined_states.update(receiver_state.tangping_elements)
            return

        new_receiver_symbol = self.frame.symbol_state_space[new_receiver_symbol_index]
        new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, receiver_state_index)
        new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]

        if (not field_name) or is_tangping:
            self.make_state_tangping(new_receiver_state)

        if new_receiver_state.tangping_elements:
            defined_states.update(new_receiver_state.tangping_elements)

        elif defined_states:
            if receiver_state.tangping_flag:
                new_receiver_state.tangping_elements.update(defined_states)
            else:
                new_receiver_state.fields[field_name] = defined_states

        else:
            # [ah]
            if new_receiver_symbol.name.startswith("%vv"):
                source_index = self.create_state_and_add_space(
                    status, stmt_id = stmt_id,
                    source_symbol_id=receiver_state.source_symbol_id,
                    source_state_id=receiver_state.source_state_id,
                    state_type = STATE_TYPE_KIND.ANYTHING,
                    access_path = self.copy_and_extend_access_path(
                        original_access_path = receiver_state.access_path,
                        access_point = AccessPoint(
                            kind = ACCESS_POINT_KIND.FIELD_ELEMENT,
                            key = field_name
                        )
                    )
                )
            else:
                source_index = self.create_state_and_add_space(
                    status, stmt_id=stmt_id,
                    source_symbol_id=receiver_state.source_symbol_id,
                    source_state_id=receiver_state.source_state_id,
                    state_type=STATE_TYPE_KIND.ANYTHING,
                    access_path=[AccessPoint(
                            kind=ACCESS_POINT_KIND.TOP_LEVEL,
                            key=new_receiver_symbol.name
                        ),
                        AccessPoint(
                            kind=ACCESS_POINT_KIND.FIELD_ELEMENT,
                            key=field_name
                        )]

                )
            self.update_access_path_state_id(source_index)

            if new_receiver_state.tangping_flag:
                new_receiver_state.tangping_elements.add(source_index)
            else:
                new_receiver_state.fields[field_name] = {source_index}

            defined_states.add(source_index)

        new_receiver_symbol.states.discard(receiver_state_index)
        new_receiver_symbol.states.add(new_receiver_state_index)
        # if receiver_state.tangping_elements:
        #     defined_states.update(receiver_state.tangping_elements)
        #     return

        # if not field_name:
        #     is_tangping = True

        # new_receiver_symbol = self.frame.symbol_state_space[new_receiver_symbol_index]
        # new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, receiver_state_index)
        # new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]

        # if is_tangping:
        #     self.make_state_tangping(new_receiver_state)

        # source_index = -1
        # if len(defined_states) == 0:
        #     source_index = self.create_state_and_add_space(
        #         status, stmt_id = stmt_id,
        #         source_symbol_id=receiver_state.source_symbol_id,
        #         source_state_id=receiver_state.source_state_id,
        #         state_type = StateTypeKind.ANYTHING,
        #         access_path = self.copy_and_extend_access_path(
        #             original_access_path = receiver_state.access_path,
        #             access_point = AccessPoint(
        #                 kind = AccessPointKind.FIELD_ELEMENT,
        #                 key = field_name
        #             )
        #         )
        #     )
        #     self.update_access_path_state_id(source_index)

        # if source_index != -1:
        #     if new_receiver_state.tangping_flag:
        #         new_receiver_state.tangping_elements.add(source_index)
        #     else:
        #         new_receiver_state.fields[field_name] = {source_index}
        # else:
        #     if new_receiver_state.tangping_flag:
        #         new_receiver_state.tangping_elements.update(defined_states)
        #     else:
        #         new_receiver_state.fields[field_name] = defined_states

        # new_receiver_symbol.states.discard(receiver_state_index)
        # new_receiver_symbol.states.add(new_receiver_state_index)

        # if source_index != -1:
        #     if new_receiver_state.tangping_flag:
        #         defined_states.update(new_receiver_state.tangping_elements)
        #     else:
        #         defined_states.add(source_index)

        # print("source_index",source_index)
        # print("new_receiver_symbol.states",new_receiver_symbol.states)

    def field_read_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        <field_read: target, receiver_object, field>
        target = receiver_symbol.field

        通过state_bit_vector_manager拿到receiver_states的state id对应的最新的state
        """
        receiver_index = status.used_symbols[0]
        field_index = status.used_symbols[1]
        receiver_symbol: Symbol = self.frame.symbol_state_space[receiver_index]
        field_symbol: Symbol = self.frame.symbol_state_space[field_index]
        if not isinstance(receiver_symbol, Symbol): # TODO: 暂时未处理<string>.format的形式
            return
        receiver_states = self.read_used_states(receiver_index, in_states)
        # print("field_read经过插件之前的receiver_states",receiver_states)
        field_states = self.read_used_states(field_index, in_states)
        defined_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        new_receiver_symbol_index = None
        defined_states = set()

        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_FIELD_READ_BEFORE,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "receiver_states": receiver_states,
                "receiver_symbol": receiver_symbol,
                "frame": self.frame,
                "field_states": field_states,
                "in_states": in_states,
                "defined_symbol": defined_symbol,
                "state_analysis": self,
                "defined_states": defined_states
            }
        )
        app_return = self.event_manager.notify(event)
        if er.should_block_event_requester(app_return):
            defined_symbol.states = event.out_data.defined_states
            return P2ResultFlag()
        # else:
        # receiver_states = event.out_data.receiver_states
        # print("field_read经过插件后的receiver_states是：",receiver_states)

        for receiver_state_index in receiver_states:
            each_defined_states = set()
            each_receiver_state = self.frame.symbol_state_space[receiver_state_index]
            if not isinstance(each_receiver_state, State):
                continue
            if isinstance(receiver_symbol, Symbol):
                self.tag_key_state(stmt_id, receiver_symbol.symbol_id, receiver_state_index)
            for each_field_state_index in field_states:
                each_field_state = self.frame.symbol_state_space[each_field_state_index]
                if not isinstance(each_field_state, State):
                    continue

                field_name = str(each_field_state.value)
                if each_receiver_state.tangping_elements:
                    each_defined_states.update(each_receiver_state.tangping_elements)
                    continue

                elif len(field_name) == 0 or each_field_state.state_type == STATE_TYPE_KIND.ANYTHING:
                    if isinstance(field_symbol, Symbol):
                        self.tag_key_state(stmt_id, field_symbol.symbol_id, each_field_state_index)
                        # 不准躺平
                    else:
                        new_receiver_symbol_index = self.assert_field_read_new_receiver_symbol(
                            new_receiver_symbol_index, status, stmt_id, receiver_symbol
                        )
                        self.change_field_read_receiver_state(
                            stmt_id, status, new_receiver_symbol_index, receiver_state_index, each_receiver_state,
                            field_name, each_defined_states, is_tangping = True
                        )
                    continue

                elif field_name in each_receiver_state.fields:
                    index_set = each_receiver_state.fields.get(field_name, set())
                    each_defined_states.update(index_set)
                    continue

                # if field_name not in receiver_state.fields:
                elif self.is_state_a_unit(each_receiver_state):

                    import_graph = self.loader.get_import_graph()
                    import_symbols = self.loader.get_unit_export_symbols(each_receiver_state.value)
                    # [ah]
                    found_in_import_graph = False
                    # 解决file.symbol的情况，从import graph里找symbol
                    for u, v, wt in import_graph.edges(data=True):
                        real_name = wt.get("realName", None)
                        if real_name == field_name:
                            symbol_type = wt.get("symbol_type", None)
                            if symbol_type == LIAN_SYMBOL_KIND.METHOD_KIND:
                                data_type = LIAN_INTERNAL.METHOD_DECL
                            elif symbol_type == LIAN_SYMBOL_KIND.CLASS_KIND:
                                data_type = LIAN_INTERNAL.CLASS_DECL
                            else:
                                data_type = LIAN_INTERNAL.UNIT

                            state_index = self.create_state_and_add_space(
                                status, stmt_id=stmt_id,
                                source_symbol_id=v,
                                source_state_id=each_receiver_state.source_state_id,
                                data_type=data_type,
                                value=v,
                                access_path=self.copy_and_extend_access_path(
                                    each_receiver_state.access_path,
                                    AccessPoint(
                                        key=real_name,
                                    )
                                )
                            )
                            found_in_import_graph = True
                            self.update_access_path_state_id(state_index)
                            each_defined_states.add(state_index)


                    if import_symbols and not found_in_import_graph:
                        for import_symbol in import_symbols:
                            if import_symbol.symbol_name == field_name:
                                if import_symbol.symbol_type == LIAN_SYMBOL_KIND.METHOD_KIND:
                                    data_type = LIAN_INTERNAL.METHOD_DECL
                                elif import_symbol.symbol_type == LIAN_SYMBOL_KIND.CLASS_KIND:
                                    data_type = LIAN_INTERNAL.CLASS_DECL
                                else:
                                    data_type = LIAN_INTERNAL.UNIT

                                state_index = self.create_state_and_add_space(
                                    status, stmt_id = stmt_id,
                                    source_symbol_id =import_symbol.symbol_id,
                                    source_state_id = each_receiver_state.source_state_id,
                                    data_type = data_type,
                                    value = import_symbol.import_stmt,
                                    access_path = self.copy_and_extend_access_path(
                                        each_receiver_state.access_path,
                                        AccessPoint(
                                            key=import_symbol.symbol_name,
                                        )
                                    )
                                )
                                self.update_access_path_state_id(state_index)
                                each_defined_states.add(state_index)

                elif self.is_state_a_class_decl(each_receiver_state):
                    first_found_class_id = -1 # 记录从下往上找到该方法的第一个class_id。最后只返回该class中所有的同名方法，不继续向上找。
                    class_methods = self.loader.get_methods_in_class(each_receiver_state.value)
                    if class_methods:
                        for method in class_methods:
                            if method.name == field_name:
                                method_class_id = self.loader.convert_method_id_to_class_id(method.stmt_id)
                                if first_found_class_id == -1:
                                    first_found_class_id = method_class_id

                                if method_class_id != first_found_class_id:
                                    continue
                                data_type = LIAN_INTERNAL.METHOD_DECL
                                if self.loader.is_class_decl(method.stmt_id):
                                    data_type = LIAN_INTERNAL.CLASS_DECL
                                state_index = self.create_state_and_add_space(
                                    status, stmt_id = stmt_id,
                                    source_symbol_id = method.stmt_id,
                                    source_state_id = each_receiver_state.source_state_id,
                                    data_type = data_type,
                                    value = method.stmt_id,
                                    access_path = self.copy_and_extend_access_path(
                                        each_receiver_state.access_path,
                                        AccessPoint(
                                            key=method.name,
                                        )
                                    )
                                )
                                self.update_access_path_state_id(state_index)
                                each_defined_states.add(state_index)

                # 创建一个新的receiver_symbol，只创建一次。并将更新后的receiver_states赋给它
                new_receiver_symbol_index = self.assert_field_read_new_receiver_symbol(
                    new_receiver_symbol_index, status, stmt_id, receiver_symbol
                )
                self.change_field_read_receiver_state(
                    stmt_id, status, new_receiver_symbol_index, receiver_state_index, each_receiver_state,
                    field_name, each_defined_states, is_tangping = False
                )
            defined_states |= each_defined_states

        defined_symbol.states = defined_states

        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_FIELD_READ_AFTER,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "receiver_states": receiver_states,
                "receiver_symbol": receiver_symbol,
                "frame": self.frame,
                "field_states": field_states,
                "in_states": in_states,
                "defined_symbol": defined_symbol,
                "state_analysis": self,
                "defined_states": defined_states
            }
        )
        app_return = self.event_manager.notify(event)
        return P2ResultFlag()


    def field_write_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        field_write: receiver_object, field, source
        def: receiver_object
        use: receiver_object field source
        receiver_symbol[field] = source
        """
        def tangping():
            new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, receiver_state_index, overwritten_flag = True)
            new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]
            self.make_state_tangping(new_receiver_state)
            new_receiver_state.tangping_elements.update(source_states)
            status.defined_states.discard(receiver_state_index)
            defined_symbol_states.discard(receiver_state_index)
            defined_symbol_states.add(new_receiver_state_index)
            return new_receiver_state

        receiver_index = status.used_symbols[0]
        field_index = status.used_symbols[1]
        source_index = status.used_symbols[2]
        is_anonymous = False
        source_symbol = self.frame.symbol_state_space[source_index]
        if source_symbol and isinstance(source_symbol, Symbol):
            if source_symbol.name.startswith(LIAN_INTERNAL.METHOD_DECL_PREF):
                is_anonymous = True

        receiver_states = self.read_used_states(receiver_index, in_states)
        field_states = self.read_used_states(field_index, in_states)
        source_states = self.read_used_states(source_index, in_states)
        receiver_symbol: Symbol = self.frame.symbol_state_space[receiver_index]

        if len(receiver_states) == 0 or len(source_states) == 0:
            return P2ResultFlag()

        defined_symbol_index = status.defined_symbol
        defined_symbol = self.frame.symbol_state_space[defined_symbol_index]
        if not isinstance(defined_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol_states = set()

        for receiver_state_index in receiver_states:
            receiver_state = self.frame.symbol_state_space[receiver_state_index]
            if not (receiver_state and isinstance(receiver_state, State)):
                continue

            if receiver_state.tangping_flag:
                tangping()
                continue

            # TODO: Here we need to leverage type system to filter out false positives
            for each_field_index in field_states:
                each_field_state = self.frame.symbol_state_space[each_field_index]
                if not (each_field_state and isinstance(each_field_state, State)):
                    continue

                if receiver_state.tangping_flag:
                    tangping()
                    continue

                if len(str(each_field_state.value)) == 0 or each_field_state.state_type == STATE_TYPE_KIND.ANYTHING:
                    tangping()
                    continue

                new_receiver_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, receiver_state_index, overwritten_flag = True)
                new_receiver_state: State = self.frame.symbol_state_space[new_receiver_state_index]
                # print("@field_state write", new_receiver_state)

                # if is_anonymous:
                # [ah]a.b = c.d access_path 变成a.b
                for each_source_state_index in source_states:
                    each_source_state = self.frame.symbol_state_space[each_source_state_index]
                    if not (each_source_state and isinstance(each_source_state, State)):
                        continue
                    #
                    # if each_source_state.state_type == STATE_TYPE_KIND.ANYTHING:
                    #     continue

                    access_path = self.copy_and_extend_access_path(
                        original_access_path = receiver_state.access_path,
                        access_point = AccessPoint(
                            kind = ACCESS_POINT_KIND.FIELD_ELEMENT,
                            key = each_field_state.value
                        )
                    )
                    each_source_state.access_path = access_path
                    self.update_access_path_state_id(each_source_state_index)

                new_receiver_state.fields[each_field_state.value] = source_states
                defined_symbol_states.add(new_receiver_state_index)

        defined_symbol.states = defined_symbol_states
        # print(f"defined_symbol_states: {defined_symbol_states}")
        event = EventData(
            self.lang,
            EVENT_KIND.P2STATE_FIELD_WRITE_AFTER,
            {
                "resolver": self.resolver,
                "stmt_id": stmt_id,
                "stmt": stmt,
                "status": status,
                "receiver_states": receiver_states,
                "receiver_symbol": receiver_symbol,
                "frame": self.frame,
                "field_states": field_states,
                "source_states":source_states,
                "in_states": in_states,
                "defined_symbol": defined_symbol,
                "state_analysis": self,
                "defined_states": defined_symbol_states
            }
        )
        self.event_manager.notify(event)

        return P2ResultFlag()

    # TODO:
    def field_addr_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        field_addr  target  data_type   name
        def: target
        use: data_type name
        target = data_type  name
        """
        # data_type_index = status.used_symbols[0]
        # name_index = status.used_symbols[1]
        # data_type = self.frame.symbol_state_space[data_type_index]
        # name = self.frame.symbol_state_space[name_index]
        # data_type_states = self.read_used_states(data_type_index, in_states)
        # name_states = self.read_used_states(name_index, in_states)

        # defined_symbol_index = status.defined_symbol
        # defined_symbol: Symbol = self.frame.symbol_state_space[defined_symbol_index]
        # defined_symbol.states = {
        #     self.create_state_and_add_space(
        #         status, stmt_id,
        #         source_symbol_id=defined_symbol.symbol_id,
        #         data_type=LianInternal.U32
        #     )
        # }
        return P2ResultFlag()

    # TODO:
    def slice_write_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        slice_write array source start end step
        def: array
        use: array source start end step
        array[start:end:step] = source

        slice write: 不指定step时，以[start, end)这个区间为界(注: start作为第一个元素，end作为最后一个元素的后一个)将source直接塞进去(长短可以不匹配)
                     指定step时，必须要保证source长度不大于[start, end)，否则会报错
        """
        start_set = set()
        end_set = set()
        step_set = set()
        source_states_set = set()

        array_symbol_index = status.used_symbols[0]
        source_symbol_index = status.used_symbols[1]
        start_symbol_index = status.used_symbols[2]
        end_symbol_index = status.used_symbols[3]
        step_symbol_index = status.used_symbols[4]

        used_array_symbol = self.frame.symbol_state_space[array_symbol_index]
        used_source_symbol = self.frame.symbol_state_space[source_symbol_index]
        used_start_symbol = self.frame.symbol_state_space[start_symbol_index]
        used_end_symbol = self.frame.symbol_state_space[end_symbol_index]
        used_step_symbol = self.frame.symbol_state_space[step_symbol_index]

        array_state_indexes = self.read_used_states(array_symbol_index, in_states)
        source_state_indexes = self.read_used_states(source_symbol_index, in_states)
        start_state_indexes = self.read_used_states(start_symbol_index, in_states)
        end_state_indexes = self.read_used_states(end_symbol_index, in_states)
        step_state_indexes = self.read_used_states(step_symbol_index, in_states)

        defined_array_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(defined_array_symbol, Symbol):
            return P2ResultFlag()

        defined_symbol_states = set()

        for source_state_index in source_state_indexes:
            source_state = self.frame.symbol_state_space[source_state_index]
            if not isinstance(source_state, State):
                continue
            if source_state.value:
                source_states_set.add(source_state_index)
            elif source_state.array:
                for array_content in source_state.array:
                    source_states_set.update(array_content)

        if not source_states_set:
            return

        for each_array_state_index in array_state_indexes:
            array_state = self.frame.symbol_state_space[each_array_state_index]
            if not isinstance(array_state, State):
                continue

            tangping_flag = array_state.tangping_flag
            if not tangping_flag:
                tmp_array = array_state.array.copy()
                for start_state_id in start_state_indexes:
                    start_state = self.frame.symbol_state_space[start_state_id]
                    if not isinstance(start_state, State) or start_state.state_type == STATE_TYPE_KIND.ANYTHING:
                        tangping_flag = True
                        break

                    for end_state_id in end_state_indexes:
                        end_state = self.frame.symbol_state_space[end_state_id]
                        if not isinstance(end_state, State) or end_state.state_type == STATE_TYPE_KIND.ANYTHING:
                            tangping_flag = True
                            break

                        for step_state_id in step_state_indexes:
                            step_state = self.frame.symbol_state_space[step_state_id]
                            if not isinstance(step_state, State) or step_state.state_type == STATE_TYPE_KIND.ANYTHING:
                                tangping_flag = True
                                break

                            array_length = len(array_state.array)
                            if not used_start_symbol:
                                start_value = str(0)
                            else:
                                start_value = start_state.value

                            if not used_end_symbol:
                                end_value = str(array_length)
                            else:
                                end_value = end_state.value

                            if not used_step_symbol:
                                step_value = str(1)
                            else:
                                step_value = step_state.value

                            if start_value.isdigit() and end_value.isdigit() and step_value.isdigit():
                                start_value = int(start_value)
                                end_value = int(end_value)
                                step_value = int(step_value)

                                tmp_array[start_value:end_value:step_value] = source_states_set
                            else:
                                tangping_flag = True
                                break
                            if tangping_flag:
                                break
                        if tangping_flag:
                            break
                    if tangping_flag:
                        break

            if tangping_flag:
                new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_array_state_index, overwritten_flag = True)
                new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
                self.make_state_tangping(new_array_state)
                new_array_state.tangping_elements.update(source_state_indexes)
                defined_symbol_states.add(new_array_state_index)

            elif tmp_array != array_state.array:
                new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_array_state_index, overwritten_flag = True)
                new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
                new_array_state.array = tmp_array
                defined_symbol_states.add(new_array_state_index)

        defined_array_symbol.states = defined_symbol_states
        return P2ResultFlag()

    def slice_read_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        slice_read  target  array   start   end step
        def: array start end step
        use: target
        target = array[start:end:step]
        """
        defined_states = set()
        start_set = set()
        end_set = set()
        step_set = set()
        new_array_symbol = None
        new_array_symbol_index = None

        array_symbol_index = status.used_symbols[0]
        start_symbol_index = status.used_symbols[1]
        end_symbol_index = status.used_symbols[2]
        step_symbol_index = status.used_symbols[3]

        used_array_symbol = self.frame.symbol_state_space[array_symbol_index]
        if not isinstance(used_array_symbol, Symbol): # TODO 暂时不处理<string>[1:3]
            return P2ResultFlag()
        used_start_symbol = self.frame.symbol_state_space[start_symbol_index]
        used_end_symbol = self.frame.symbol_state_space[end_symbol_index]
        used_step_symbol = self.frame.symbol_state_space[step_symbol_index]

        array_state_indexes = self.read_used_states(array_symbol_index, in_states)
        start_state_indexes = self.read_used_states(start_symbol_index, in_states)
        end_state_indexes = self.read_used_states(end_symbol_index, in_states)
        step_state_indexes = self.read_used_states(step_symbol_index, in_states)

        target_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(target_symbol, Symbol):
            return P2ResultFlag()

        for each_array_state_index in array_state_indexes:
            array_state = self.frame.symbol_state_space[each_array_state_index]
            if not isinstance(array_state, State):
                continue

            if array_state.tangping_flag:
                defined_states.update(array_state.tangping_elements)
                continue

            tmp_array: list = []

            tangping_flag = True
            for start_state_id in start_state_indexes:
                start_state = self.frame.symbol_state_space[start_state_id]
                if not isinstance(start_state, State) or start_state.state_type == STATE_TYPE_KIND.ANYTHING:
                    break

                for end_state_id in end_state_indexes:
                    end_state = self.frame.symbol_state_space[end_state_id]
                    if not isinstance(end_state, State) or end_state.state_type == STATE_TYPE_KIND.ANYTHING:
                        break

                    for step_state_id in step_state_indexes:
                        step_state = self.frame.symbol_state_space[step_state_id]
                        if not isinstance(step_state, State) or step_state.state_type == STATE_TYPE_KIND.ANYTHING:
                            break

                        array_length = len(array_state.array)
                        if not used_start_symbol:
                            start_value = str(0)
                        else:
                            start_value = start_state.value

                        if not used_end_symbol:
                            end_value = str(array_length)
                        else:
                            end_value = end_state.value

                        if not used_step_symbol:
                            step_value = str(1)
                        else:
                            step_value = step_state.value

                        if start_value.isdigit() and end_value.isdigit() and step_value.isdigit():
                            start_value = int(start_value)
                            end_value = int(end_value)
                            step_value = int(step_value)

                            if (
                                start_value < end_value < array_length and
                                array_state.array[start_value:end_value:step_value]
                            ):
                                tmp_array = array_state.array[start_value:end_value:step_value]
                                defined_state_index = self.create_state_and_add_space(
                                    status = status,
                                    stmt_id = stmt_id,
                                    source_symbol_id = target_symbol.symbol_id,
                                    data_type = LIAN_INTERNAL.ARRAY,
                                    access_path=[AccessPoint()]
                                )
                                self.update_access_path_state_id(defined_state_index)
                                defined_state: State = self.frame.symbol_state_space[defined_state_index]
                                defined_state.array = tmp_array

                                defined_states.add(defined_state_index)
                                tangping_flag = False
                            else:
                                break

                        if tangping_flag:
                            break
                    if tangping_flag:
                        break
                if tangping_flag:
                    break

            if not tangping_flag:
                continue

            # tangping
            if util.is_empty(new_array_symbol_index):
                new_array_symbol_index = self.create_copy_of_symbol_and_add_space(status, stmt_id, used_array_symbol)
                new_array_symbol: Symbol = self.frame.symbol_state_space[new_array_symbol_index]

            new_array_state_index = self.create_copy_of_state_and_add_space(status, stmt_id, each_array_state_index)
            new_array_state: State = self.frame.symbol_state_space[new_array_state_index]
            new_path: list = array_state.access_path.copy()
            new_path.append(AccessPoint(
                kind = ACCESS_POINT_KIND.FIELD_ELEMENT,
                key=util.read_stmt_field(target_symbol.name)
            ))
            source_index = self.create_state_and_add_space(
                status,
                stmt_id,
                source_symbol_id = array_state.source_symbol_id,
                source_state_id = array_state.source_state_id,
                state_type = STATE_TYPE_KIND.ANYTHING,
                access_path = new_path
            )
            self.update_access_path_state_id(source_index)

            self.make_state_tangping(new_array_state)
            new_array_state.tangping_elements.add(source_index)
            defined_states.update(new_array_state.tangping_elements)
            new_array_symbol.states.discard(each_array_state_index)
            new_array_symbol.states.add(new_array_state_index)

        target_symbol.states = defined_states

        return P2ResultFlag()

    def del_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        del_stmt    name
        def:
        use: name
        """
        return P2ResultFlag()

    def unset_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        unset_stmt  name
        def:
        use: name
        """
        target_symbol = self.frame.symbol_state_space[status.defined_symbol]
        if not isinstance(target_symbol, Symbol):
            return P2ResultFlag()

        target_symbol.states = []
        return P2ResultFlag()

