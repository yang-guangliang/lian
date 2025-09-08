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

def check_this_write(receiver_symbol, receiver_states, frame):
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

def write_to_this_class(data: EventData):
    in_data = data.in_data
    frame: ComputeFrame = in_data.frame
    status = in_data.status
    receiver_states = in_data.receiver_states
    receiver_symbol: Symbol = in_data.receiver_symbol
    field_states = in_data.field_states
    defined_symbol = in_data.defined_symbol
    stmt_id = in_data.stmt_id
    stmt = in_data.stmt
    state_analysis:StmtStateAnalysis = in_data.state_analysis
    loader:Loader = frame.loader
    source_states = in_data.source_states
    defined_states = in_data.defined_states
    app_return = er.config_event_unprocessed()
    resolver = state_analysis.resolver
    if not check_this_write(receiver_symbol, receiver_states, frame):
        return app_return
    class_id = loader.convert_method_id_to_class_id(frame.method_id)
    class_members = loader.load_class_id_to_members(class_id)
    for each_field_state_index in field_states:
        each_field_state = frame.symbol_state_space[each_field_state_index]
        if not isinstance(each_field_state, State):
            continue
        field_name = str(each_field_state.value)
        if len(field_name) == 0:
            continue
        # FIXME 分支living graph，会覆盖
        class_members[field_name] = source_states
    loader.save_class_id_to_members(class_id, class_members)
    return app_return

def appstorage_write(data: EventData):
    name_states = data.in_data.name_states
    args = data.in_data.args
    space = data.in_data.space
    for state_index in name_states:
        state = space[state_index]
        access_path = access_path_formatter(state.access_path)
        if access_path == "AppStorage.SetOrCreate":


            break
    pass


def access_path_formatter(state_access_path):
    key_list = []
    for item in state_access_path:
        key = item.key
        key = key if isinstance(key, str) else str(key)
        if key != "":
            key_list.append(key)

    # 使用点号连接所有 key 值
    access_path = '.'.join(key_list)
    return access_path