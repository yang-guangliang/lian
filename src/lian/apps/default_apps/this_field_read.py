#!/usr/bin/env python3
import copy
from lian.semantic.semantic_structs import AccessPoint, State, ComputeFrame, Symbol
from lian.semantic.summary_analysis.stmt_state_analysis import StmtStateAnalysis
from lian.apps.app_template import EventData
from lian.config.constants import (
    EVENT_KIND,
    LIAN_INTERNAL,
    STATE_TYPE_KIND,
    LIAN_SYMBOL_KIND,
    ACCESS_POINT_KIND
)
import lian.apps.event_return as er
from lian.util import util
from lian.util.loader import Loader
from lian.config.constants import LIAN_INTERNAL

def check_this_read(receiver_symbol, receiver_states, frame):
    """
    判断此次field_read是否是对this的read: this.field
    """
    this_flag = False
    if len(receiver_states) != 0:
        for each_receiver_state_index in receiver_states:
            each_receiver_state : State = frame.symbol_state_space[each_receiver_state_index]
            if hasattr(each_receiver_state, "data_type") and each_receiver_state.data_type == LIAN_INTERNAL.THIS:
                this_flag = True
                break
    if receiver_symbol.name != LIAN_INTERNAL.THIS and this_flag == False:
        return False
    return True


def resolve_this_field_method(data: EventData):
    """
    用于处理field_read: self.func的情况，找到类中定义的field_methods，并添加到self状态的field "func"中。
    """
    in_data = data.in_data
    frame: ComputeFrame = in_data.frame
    status = in_data.status
    receiver_states = in_data.receiver_states
    receiver_symbol: Symbol = in_data.receiver_symbol
    field_states = in_data.field_states
    defined_symbol = in_data.defined_symbol
    stmt_id = in_data.stmt_id
    state_analysis:StmtStateAnalysis = in_data.state_analysis
    loader:Loader = frame.loader
    defined_states = in_data.defined_states
    app_return = er.config_event_unprocessed()

    # 只处理对self的field_read
    if not check_this_read(receiver_symbol,receiver_states,frame):
        data.out_data.receiver_states = receiver_states
        app_return = er.config_continue_event_processing(app_return)
        return app_return
    # 取出该类的methods_in_class
    current_method_id = frame.method_id
    current_class_id = loader.convert_method_id_to_class_id(current_method_id)
    methods_in_class = copy.deepcopy(loader.load_methods_in_class(current_class_id))
    # print(methods_in_class)
    # print(f"精确大小: {asizeof.asizeof(methods_in_class)} 字节")
    for each_class in frame.classes_of_method:
        if each_class != current_class_id:
            method_in_current_class = loader.load_methods_in_class(each_class)
            methods_in_class.extend(method_in_current_class)
    method_name = loader.convert_method_id_to_method_name(current_method_id)
    class_name = loader.convert_class_id_to_class_name(current_class_id)
    # print("methods_in_class: \n",methods_in_class)
    # print("receiver_states:",receiver_states,\
    #       "\n当前方法是来自",class_name,"类的",method_name)
    # print([frame.symbol_state_space[i].data_type for i in receiver_states])
    for each_receiver_state_index in receiver_states:
        each_receiver_state : State = frame.symbol_state_space[each_receiver_state_index]
        if not isinstance(each_receiver_state, State):
            continue

        for each_field_state_index in field_states:
            each_field_state = frame.symbol_state_space[each_field_state_index]
            if not isinstance(each_field_state, State):
                continue
            field_name = str(each_field_state.value)
            # print("resolve_this_field_method@ field_name是",field_name)
            if len(field_name) == 0:
                continue

            # 如果当前receiver_this_state中已经有该field存在，就pass
            if field_name in each_receiver_state.fields and len(each_receiver_state.fields[field_name]) > 0:
                continue

            # 取出该methods_in_class中，所有方法名为field_name的方法
            found_method_ids = [method.stmt_id for method in methods_in_class if method.name == field_name]
            if util.is_empty(found_method_ids):
                continue

            # copy_on_change 创建一个原receiver_state的副本
            new_receiver_state_index = state_analysis.create_copy_of_state_and_add_space(status, stmt_id, each_receiver_state_index)
            new_receiver_state = frame.symbol_state_space[new_receiver_state_index]
            for each_method_id in found_method_ids:
                field_method_state_index = state_analysis.create_state_and_add_space(
                    stmt_id = stmt_id,
                    status = status,
                    source_symbol_id = each_method_id,
                    source_state_id = each_receiver_state.source_state_id,
                    data_type = LIAN_INTERNAL.METHOD_DECL,
                    value = each_method_id,
                    access_path = state_analysis.copy_and_extend_access_path(
                        each_receiver_state.access_path,
                        AccessPoint(
                            kind = ACCESS_POINT_KIND.FIELD_NAME,
                            key = field_name
                        )
                    )
                )
                state_analysis.update_access_path_state_id(field_method_state_index)
                util.add_to_dict_with_default_set(new_receiver_state.fields, field_name, field_method_state_index)
            receiver_states.discard(each_receiver_state_index)
            receiver_states.add(new_receiver_state_index)
            # 新创了this_state副本之后，要把之前summary中的key_dynamic_content中原来的this_state去掉。否则之后取this_state的时候会状态爆炸
            state_analysis.cancel_key_state(receiver_symbol.symbol_id, each_receiver_state_index)
            # print("copy_on_change 产生的新state是",new_receiver_state_index,"原来是",each_receiver_state_index)
            # pprint.pprint(new_receiver_state)

    data.out_data.receiver_states = receiver_states
    app_return = er.config_continue_event_processing(app_return)
    return app_return


def read_from_this_class(data: EventData):
    in_data = data.in_data
    frame: ComputeFrame = in_data.frame
    status = in_data.status
    receiver_states = in_data.receiver_states
    receiver_symbol: Symbol = in_data.receiver_symbol
    field_states = in_data.field_states
    defined_symbol = in_data.defined_symbol
    stmt_id = in_data.stmt_id
    state_analysis:StmtStateAnalysis = in_data.state_analysis
    loader:Loader = frame.loader
    defined_states = in_data.defined_states
    app_return = er.config_event_unprocessed()
    resolver = state_analysis.resolver

    # 只在global_analysis的this_field_read开启
    if not check_this_read(receiver_symbol,receiver_states,frame) or state_analysis.phase != 3:
        data.out_data.receiver_states = receiver_states
        app_return = er.config_continue_event_processing(app_return)
        return app_return

    result = set()
    class_id = loader.convert_method_id_to_class_id(frame.method_id)
    class_members = loader.load_class_id_to_members(class_id)
    for each_field_state_index in field_states:
        each_field_state = frame.symbol_state_space[each_field_state_index]
        if not isinstance(each_field_state, State):
            continue
        field_name = str(each_field_state.value)
        if len(field_name) == 0 or each_field_state.state_type == STATE_TYPE_KIND.ANYTHING:
            continue
        if field_name in class_members:
            index_set = class_members.get(field_name, set())
            result.update(index_set)

    if not util.is_empty(result):
        data.out_data.defined_states = result
        app_return = er.config_block_event_requester(app_return)
        return app_return

    data.out_data.receiver_states = receiver_states
    app_return = er.config_continue_event_processing(app_return)
    return app_return
