#!/usr/bin/env python3
"""ArkUI 组件树建模（abc / ArkTS 转译产物）。

参考 HScope 的 AbcModeling.modelArkuiComponentParent（注册在 new_object 之后），
在子组件实例被构造时记录父子关系：

    __arkui_parent : 子组件状态 -> 父组件状态集合
    __arkui_child  : 父组件状态 -> 子组件状态集合

为什么要建这条链：@Provide/@Consume 这类装饰器编译后是"按字符串 key 注册 /
按 key 读取"的运行时注册表（addProvidedVar / initializeConsume），字节码里
两者之间没有任何调用边，只能沿着组件父子链回溯才能把提供方的值交给消费方
（见 externs/modeling/abc_arkui.py 的 initializeConsume 建模）。
"""

from lian.events.handler_template import EventData
import lian.events.event_return as er
from lian.common_structs import State
from lian.externs.modeling.abc_arkui import ARKUI_PARENT_BY_STATE_ID

# 与 HScope 保持一致（AbcModeling / CollectionModeling 里同名常量）
ARKUI_PARENT_FIELD = "__arkui_parent"
ARKUI_CHILD_FIELD = "__arkui_child"


def _arg_state_indexes(in_data, position):
    """取第 position 个实参（0 起）对应的状态下标集合。"""
    args = getattr(in_data, "args", None)
    positional_args = getattr(args, "positional_args", None) or []
    if position >= len(positional_args):
        return set()
    return {
        arg.index_in_space
        for arg in positional_args[position]
        if getattr(arg, "index_in_space", -1) >= 0
    }


def model_arkui_component_parent(data: EventData):
    """new Child(this, params, ...) 之后：记录【子组件 -> 父组件】与反向链接。"""
    in_data = data.in_data
    frame = in_data.frame
    defined_symbol = getattr(in_data, "defined_symbol", None)
    app_return = er.config_event_unprocessed()
    if defined_symbol is None:
        return er.config_continue_event_processing(app_return)

    # 父组件 = 构造子组件时的第一个实参（ArkUI 转译产物里就是父组件的 this）
    parent_states = {
        index
        for index in _arg_state_indexes(in_data, 0)
        if isinstance(frame.symbol_state_space[index], State)
    }
    if not parent_states:
        return er.config_continue_event_processing(app_return)

    # 子组件实例 = 本次 new_object 新建的状态（before 阶段已登记）
    child_states = set((getattr(in_data, "type_state_to_new_index", None) or {}).values())
    if not child_states:
        child_states = set(getattr(defined_symbol, "states", set()) or set())

    for child_index in child_states:
        child_state = frame.symbol_state_space[child_index]
        if not isinstance(child_state, State):
            continue
        child_state.fields.setdefault(ARKUI_PARENT_FIELD, set()).update(parent_states)
        child_state_id = getattr(child_state, "state_id", None)
        if child_state_id is not None:
            # 同时按 state_id 登记（带状态空间 id，下标只在同一空间内有效）：
            # 同一组件实例的多个状态副本都能接上父链
            space_id = id(frame.symbol_state_space)
            ARKUI_PARENT_BY_STATE_ID.setdefault(child_state_id, set()).update(
                (space_id, index) for index in parent_states
            )
        for parent_index in parent_states:
            parent_state = frame.symbol_state_space[parent_index]
            if isinstance(parent_state, State):
                parent_state.fields.setdefault(ARKUI_CHILD_FIELD, set()).add(child_index)

    return er.config_continue_event_processing(app_return)
