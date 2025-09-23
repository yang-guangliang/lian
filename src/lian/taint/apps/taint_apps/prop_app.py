import re
import struct
import ast
import dataclasses
import taint.apps.event_return as er
from taint import config1 as config
from taint.apps.app_template import EventData
from taint.taint_structs import TagBitVectorManager,TaintEnv
from taint.constants import TAG_KEYWORD
from taint import util
from lian.semantic.semantic_structs import (
    Symbol,
    State
)

# used for foreach item prop
def foreach_item_prop(data: EventData):
    data = data.in_data
    # in_taint是个字典{symbol_name: tag_bv}
    in_taint = data.in_taint
    stmt = data.stmt
    frame = data.frame
    taint_env = frame.taint_env
    taint_status = data.taint_status
    app_result = None
    taint_state_manager = frame.taint_state_manager
    status = data.status
    tag = data.tag
    if stmt.operation != "assign_stmt" or stmt.target != "item":
        return app_result
    taint_state_manager.add_path_to_tag(stmt.target, tag)
    
    


def send_to_router(data: EventData):
    data = data.in_data
    # in_taint是个字典{symbol_name: tag_bv}
    in_taint = data.in_taint
    stmt = data.stmt
    frame = data.frame
    taint_env = frame.taint_env
    taint_status = data.taint_status
    taint_state_manager = frame.taint_state_manager
    stmt_id_to_status = frame.stmt_id_to_status
    status = stmt_id_to_status[stmt.stmt_id]
    if not status:
        return
    space = frame.symbol_state_space
    app_result = None

    target = status.defined_symbol
    name = status.used_symbols[0]

    name_symbol = space[name]
    name_state_index = list(name_symbol.states)[0]
    name_state = space[name_state_index]
    if not isinstance(name_state, State) :
        return
    name_access_path = access_path_formatter(name_state.access_path)
    if name_access_path != "router.default.back":
        return app_result
    tag = taint_state_manager.get_path_tag("%this.addressList")
    taint_state_manager.add_path_to_tag("router.params.item", tag)

def read_from_router(data: EventData):
    data = data.in_data
    # in_taint是个字典{symbol_name: tag_bv}
    in_taint = data.in_taint
    stmt = data.stmt
    frame = data.frame
    taint_env = frame.taint_env
    taint_status = data.taint_status
    taint_state_manager = frame.taint_state_manager
    stmt_id_to_status = frame.stmt_id_to_status
    status = stmt_id_to_status[stmt.stmt_id]
    if not status:
        return
    space = frame.symbol_state_space
    app_result = None

    target = status.defined_symbol
    name = status.used_symbols[0]
    name_symbol = space[name]
    name_state_index = list(name_symbol.states)[0]
    name_state = space[name_state_index]
    if not isinstance(name_state, State) :
        return
    name_access_path = access_path_formatter(name_state.access_path)
    if name_access_path != "router.default.getParams":
        return app_result
    tag = taint_state_manager.get_path_tag("router.params.item")
    symbol_id = space[target].symbol_id
    taint_status.out_taint[symbol_id] = tag
    


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