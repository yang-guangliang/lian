#!/usr/bin/env python3

import ast
from inspect import Parameter
import pprint

from pandas.core import frame

from lian.semantic.resolver import Resolver
from lian.semantic.summary_analysis.stmt_state_analysis import StmtStateAnalysis
from lian.util import util
from lian.config import config
from lian.util.loader import Loader
# from lian.apps.app_template import AppTemplate
from lian.config.constants import (
    LIAN_SYMBOL_KIND,
    LIAN_INTERNAL,
    STATE_TYPE_KIND,
    LIAN_INTERNAL,
    CALLEE_TYPE,
    EVENT_KIND
)
from lian.semantic.semantic_structs import (
    CallGraph,
    MethodDeclParameters,
    Parameter,
    Argument,
    MethodCallArguments,
    PathManager,
    StateDefNode,
    StmtStatus,
    Symbol,
    State,
    MethodCall,
    ComputeFrameStack,
    ComputeFrame,
    MethodSummaryTemplate,
    MethodSummaryInstance,
    SymbolStateSpace,
    SimpleWorkList,
    P2ResultFlag,
    MethodCallArguments,
    InterruptionData,
    APath,
    MethodDefUseSummary
)

class GlobalStmtStateAnalysis(StmtStateAnalysis):
    def __init__(
        self, app_manager, loader: Loader, resolver: Resolver, compute_frame: ComputeFrame,
        path_manager: PathManager, analyzed_method_list: list
    ):
        super().__init__(app_manager, loader, resolver, compute_frame, None, analyzed_method_list)
        self.path_manager = path_manager
        self.analyzed_method_list = analyzed_method_list
        self.phase = 3

    def get_method_summary(self, method_id):
        pass

    def has_been_analyzed(self, method_id):
        pass

    def print_path(self, path: tuple):
        if not path:
            return

        path_len = len(path)
        if path_len < 1:
            return

        path_str = f"{path[0]}"
        for i in range(3, len(path)+1, 2):
            path_str += f"-@-{path[i-2]}->-{path[i-1]}"

        print(f"current path: {path_str}")
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
            array = [],
            call_site = self.frame.path[-3:]
        )

        index = self.frame.symbol_state_space.add(item)
        state_def_node = StateDefNode(index=index, state_id=item.state_id, stmt_id=stmt_id)
        util.add_to_dict_with_default_set(
            self.frame.state_to_define,
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
            if symbol_id in self.frame.method_def_use_summary.used_this_symbol_id:
                self.frame.method_def_use_summary.defined_this_symbol_id.add(symbol_id)
            else:
                self.frame.method_def_use_summary.defined_external_symbol_ids.add(symbol_id)
        return index

    def compute_target_method_states(
        self, stmt_id, stmt, status, in_states,
        callee_method_ids, target_symbol, args,
        this_state_set = set(), new_object_flag = False
    ):
        callee_ids_to_be_analyzed = []
        caller_id = self.frame.method_id
        call_stmt_id = stmt_id
        if config.DEBUG_FLAG:
            util.debug(f"positional_args of stmt <{stmt_id}>: {args.positional_args}")
            util.debug(f"named_args of stmt <{stmt_id}>: {args.named_args}")

        parameter_mapping_list = []

        for each_callee_id in callee_method_ids:
            callee_path = self.frame.path + (stmt_id, each_callee_id)
            # self.print_path(callee_path)
            new_path = APath(callee_path)
            new_call_site = (caller_id, stmt_id, each_callee_id)
            # TODO: 检查是否已经分析过
            if(
                self.path_manager.path_exists(new_path) or
                self.path_manager.count_cycles(callee_path) > 1 or
                each_callee_id in self.frame.path or
                new_call_site in self.frame.summary_collection
            ):
                continue

            callee_ids_to_be_analyzed.append(each_callee_id)
            # prepare callee parameters
            # 可能第二阶段没有这个caller->callee，因此该call的parameter_list可能是空的，在这个阶段还是需要生成一遍parameter_list
            parameters = self.prepare_parameters(each_callee_id)
            if config.DEBUG_FLAG:
                util.debug(f"parameters of callee <{each_callee_id}>: {parameters}\n")
            # current_parameter_mapping_list = self.loader.load_parameter_mapping(new_call_site)
            # if util.is_empty(current_parameter_mapping_list):
            current_parameter_mapping_list = []
            self.map_arguments(args, parameters, current_parameter_mapping_list, new_call_site, 3)
            parameter_mapping_list.extend(current_parameter_mapping_list)

        classes_of_method = []
        for index in this_state_set:
            print(index)
            instance_state = self.frame.symbol_state_space[index]
            if isinstance(instance_state, State) and self.is_state_a_class_decl(instance_state):
                classes_of_method.append(instance_state.value)
        if len(callee_ids_to_be_analyzed) != 0:
            # print(f"callee_ids_to_be_analyzed: {callee_ids_to_be_analyzed}")
            return P2ResultFlag(
                # states_changed = True,
                # defuse_changed = defuse_changed,
                interruption_flag = True,
                interruption_data = InterruptionData(
                    caller_id = self.frame.method_id,
                    call_stmt_id = stmt_id,
                    callee_ids = callee_ids_to_be_analyzed,
                    args_list = parameter_mapping_list,
                    classes_of_method = classes_of_method,
                ),
            )

        for each_callee_id in callee_method_ids:
            new_path = APath(self.frame.path + (stmt_id, each_callee_id))
            self.path_manager.add_path(new_path)
            new_call_site = (caller_id, stmt_id, each_callee_id)
            # prepare callee summary instance and compact space
            if new_call_site in self.frame.summary_collection:
                callee_summary = self.frame.summary_collection[new_call_site]
            else:
                continue
            callee_summary = callee_summary.copy()

            if new_call_site in self.frame.symbol_state_space_collection:
                callee_compact_space = self.frame.symbol_state_space_collection[new_call_site]
            else:
                continue
            callee_compact_space = callee_compact_space.copy()
            self.apply_callee_semantic_summary(
                stmt_id, each_callee_id, args, callee_summary,
                callee_compact_space, this_state_set, new_object_flag
            )

        return P2ResultFlag()

    # def call_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
    #     # pprint.pprint(status)
    #     target_index = status.defined_symbol
    #     target_symbol: Symbol = self.frame.symbol_state_space[target_index]

    #     name_index = status.used_symbols[0]
    #     name_symbol = self.frame.symbol_state_space[name_index]
    #     name_states = self.read_used_states(name_index, in_states)
    #     callee_method_ids = set()
    #     callee_class_ids = set()
    #     unsolved_callee_ids = set()

    #     args = self.prepare_args(stmt_id, stmt, status, in_states)
    #     if util.is_empty(callee_info):
    #         result = self.trigger_extern_callee(
    #             stmt_id, stmt, status, in_states, unsolved_callee_ids, name_symbol, defined_symbol, args
    #         )
    #         if util.is_available(result):
    #             return result
    #         return P2ResultFlag()
    #     if self.frame.callee_param != None:
    #         # 放置到status中
    #         self.frame.callee_param = None
    #         pass
    #     # TODO: JAVA CASE 处理java中 call this()的情况，应该去找它的构造函数
    #     if name_symbol.name == LianInternal.THIS:
    #         caller_id = self.frame.method_id
    #         class_id = self.loader.convert_method_id_to_class_id(caller_id)
    #         class_name = self.loader.convert_class_id_to_class_name(class_id)
    #         methods_in_class = self.loader.load_methods_in_class(class_id)
    #         for each_method in methods_in_class:
    #             if each_method.name == class_name:
    #                 if each_method.stmt_id != caller_id: # 不加自己
    #                     if callee_id := util.str_to_int(each_method.stmt_id):
    #                         callee_method_ids.add(callee_id)

    #     this_state_set = set()
    #     for each_state_index in name_states:
    #         each_state = self.frame.symbol_state_space[each_state_index]

    #         if self.is_state_a_method_decl(each_state):
    #             if each_state.value:
    #                 source_state_id = each_state.source_state_id
    #                 if source_state_id != each_state.state_id:
    #                     this_state_set.update(
    #                         self.resolver.obtain_parent_states(stmt_id, self.frame, status, each_state_index)
    #                     )
    #                 if callee_id := util.str_to_int(each_state.value):
    #                     callee_method_ids.add(callee_id)

    #         elif self.is_state_a_class_decl(each_state):
    #             callee_class_ids.add(each_state.value)
    #             return self.new_object_stmt_state(stmt_id, stmt, status, in_states)

    #         else:
    #             unsolved_callee_ids.add(each_state.value)

    #     if len(callee_method_ids) == 0 and len(unsolved_callee_ids) != 0:
    #         result = self.trigger_extern_callee(
    #             stmt_id, stmt, status, in_states, unsolved_callee_ids, name_symbol, target_symbol, args
    #         )
    #         if util.is_available(result):
    #             return result
    #         return P2ResultFlag()

    #     return self.compute_target_method_states(
    #         stmt_id, stmt, status, in_states, callee_method_ids, target_symbol, args, this_state_set
    #     )


    def parameter_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        """
        parameter_decl  attrs    data_type   name    default_value
        def: name
        use: default_value
        """
        parameter_name_symbol = self.frame.symbol_state_space[status.defined_symbol]
        symbol_id = parameter_name_symbol.symbol_id
        if isinstance(parameter_name_symbol, Symbol) and self.frame.params_list:
            parameter_name_symbol.states = set()
            for each_pair in self.frame.params_list:
                if each_pair.parameter_symbol_id == symbol_id:
                    parameter_state_index = each_pair.arg_index_in_space
                    # self.update_access_path_state_id(parameter_state_index)
                    parameter_name_symbol.states.add(parameter_state_index)
                    status.defined_states.add(parameter_state_index)
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
