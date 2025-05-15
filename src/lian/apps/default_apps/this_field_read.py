#!/usr/bin/env python3
from lian.semantic.semantic_structure import AccessPoint, State, ComputeFrame
from lian.semantic.stmt_state_analysis import StmtStateAnalysis
from lian.apps.app_template import EventData
from lian.config.constants import (
    EventKind,
    LianInternal,
    StateTypeKind,
    ScopeKind,
    AccessPointKind
)
import lian.apps.event_return as er
from lian.util import util
from lian.util.loader import Loader
from lian.config.constants import LianInternal
import pprint

def resolve_this_field_method(data: EventData):
    """
    用于处理field_read: self.func的情况，找到类中定义的field_methods，并添加到self状态的field "func"中。
    """
    in_data = data.in_data
    frame: ComputeFrame = in_data.frame
    status = in_data.status
    receiver_states = in_data.receiver_states
    receiver_symbol = in_data.receiver_symbol
    field_states = in_data.field_states
    defined_symbol = in_data.defined_symbol
    stmt_id = in_data.stmt_id
    state_analysis:StmtStateAnalysis = in_data.state_analysis
    loader:Loader = frame.loader
    defined_states = in_data.defined_states
    app_return = er.config_event_unprocessed()

    # 只处理对self的field_read
    if receiver_symbol.name != LianInternal.THIS:
        data.out_data.receiver_states = receiver_states
        app_return = er.config_continue_event_processing(app_return)
        return app_return
    # 取出该类的methods_in_class
    current_method_id = frame.method_id
    current_class_id = loader.convert_method_id_to_class_id(current_method_id)
    methods_in_class = loader.load_methods_in_class(current_class_id)
    method_name = loader.convert_method_id_to_method_name(current_method_id)
    class_name = loader.convert_class_id_to_class_name(current_class_id)
    # print("methods_in_class: \n",methods_in_class)
    print("receiver_states:",receiver_states,\
          "\n当前方法是来自",class_name,"类的",method_name)
    print([frame.symbol_state_space[i].data_type for i in receiver_states])
    # input("11111111111111111111")
    for each_receiver_state_index in receiver_states:
        each_receiver_state : State = frame.symbol_state_space[each_receiver_state_index]
        # if each_receiver_state.data_type != LianInternal.THIS:
        #     continue

        for each_field_state_index in field_states:
            each_field_state = frame.symbol_state_space[each_field_state_index]
            if not isinstance(each_field_state, State):
                continue
            field_name = str(each_field_state.value)    
            print("resolve_this_field_method@ field_name是",field_name)
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
                    data_type = LianInternal.METHOD_DECL,
                    value = each_method_id,
                    access_path = state_analysis.copy_and_extend_access_path(
                        each_receiver_state.access_path,
                        AccessPoint(
                            kind = AccessPointKind.FIELD_NAME,
                            key = field_name
                        )
                    )            
                )
                state_analysis.update_access_path_state_id(field_method_state_index)
                util.add_to_dict_with_default_set(new_receiver_state.fields, field_name, field_method_state_index)
            receiver_states.discard(each_receiver_state_index)
            receiver_states.add(new_receiver_state_index)
            print("copy_on_change 产生的新state是",new_receiver_state_index,"原来是",each_receiver_state_index)
            # pprint.pprint(new_receiver_state)

    data.out_data.receiver_states = receiver_states
    app_return = er.config_continue_event_processing(app_return)
    return app_return
