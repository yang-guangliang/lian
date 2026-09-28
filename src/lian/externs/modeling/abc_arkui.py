#!/usr/bin/env python3
"""ArkUI 状态管理建模（abc 字节码 / ArkTS 转译产物）。

背景
----
ArkTS 的 @State/@Link/@Prop/@Provide/@Consume/@ObjectLink/@Watch/@StorageLink/
@StorageProp 等装饰器，编译(转译)后会变成 ArkUI 运行时封装类：

    this.__message = new ObservedPropertySimplePU('Hello World', this, "message");
    set message(v) { this.__message.set(v); }
    get message()  { return this.__message.get(); }

其中 `set`/`get` 是外部(未解析)方法调用。若不建模，污点在 `set` 处就断了：
值虽然进了 acc，但接收者对象没有"内容字段"被写入；`get` 的返回值也取不到内容。

本模块参考 HScope 的实现方式（CollectionModeling.java 中的
`handleAppStorageSetOrCreate` / `handleAppStorageGet` / Map、Set 处理，以及
`handleArkuiInitializeConsume` 为 `ObservedPropertyAbstractPU` 建立带 `value`
字段的 wrapper 状态），把这类封装调用还原成"字段读写"语义：

    recv.set(v)   ->  recv.value = v                 (写入接收者内容字段)
    recv.get()    ->  target = recv.value            (读出接收者内容字段)
    recv.add(v)   ->  recv.tangping_elements += v    (Set 语义)

只对"ArkUI 封装接收者"生效（见 `_is_arkui_wrapper_receiver`），避免影响普通
的 set/get 调用（例如 Map / Preferences / 文件读写），以控制精度回归。
"""

from lian.common_structs import Argument, MethodCallArguments, State
from lian.util import util
from lian.config.constants import LIAN_INTERNAL


# 转译产物里 ArkUI 状态封装对象的常见标识（数据类名包含其一即认为是封装对象）
ARKUI_WRAPPER_MARKERS = (
    "ObservedProperty",
    "SynchedProperty",
    "AppStorage",
    "LocalStorage",
    "SubscriberManager",
    "ViewPU",
)

# 封装对象的内容字段名（与 HScope 的 wrapper `value` 字段保持一致）
WRAPPER_VALUE_KEY = "value"


# Navigation 的 payload 在 pushPathByName -> pageMap -> NavDestination.onReady
# 这一条框架调用链中传递。key 使用当前 SymbolStateSpace 的对象 id，避免 P2/P3
# 或不同入口点之间误用另一个状态空间的下标。
_NAVIGATION_PAYLOADS_BY_SPACE = {}

# observeComponentCreation2(callback, { name: "TargetPage" }) 会把组件名交给
# callback；callback 内部随后执行 ViewPU.create(component)。记录这层关联后，
# create 模型才能精确找到 TargetPage 对应的 initialRender。
_COMPONENT_NAME_BY_CALLBACK_METHOD = {}

# ABC 生命周期的字段读取可能生成不同的 dataSource 状态 id。条目按状态空间和
# aboutToAppear 方法保存，供对应 initialRender 的 LazyForEach 读取。
_LAZY_ITEMS_BY_LIFECYCLE = {}


def _access_path_key(point):
    key = getattr(point, "key", None)
    return key if isinstance(key, str) else ""


def _receiver_state_id(in_data):
    """被调状态(如 this.__message.set)的访问路径中，倒数第二段即接收者。"""
    frame = in_data.frame
    for callee_state_index in in_data.unsolved_callee_states:
        callee_state = frame.symbol_state_space[callee_state_index]
        if not isinstance(callee_state, State):
            continue
        access_path = callee_state.access_path
        if len(access_path) >= 2:
            state_id = getattr(access_path[-2], "state_id", -1)
            if isinstance(state_id, int) and state_id >= 0:
                return state_id
    return -1


def _receiver_access_path_key(in_data):
    """接收者在访问路径中的名字，例如 this.__message.set 的 __message。"""
    frame = in_data.frame
    for callee_state_index in in_data.unsolved_callee_states:
        callee_state = frame.symbol_state_space[callee_state_index]
        if not isinstance(callee_state, State):
            continue
        access_path = callee_state.access_path
        if len(access_path) >= 2:
            return _access_path_key(access_path[-2])
    return ""


def _receiver_states(in_data):
    """按 state_id 收集接收者当前最新的状态实例（对齐 HScope getReceiverStates）。

    若访问路径取不到（例如 ArkUI 里接收者被压进 acc 寄存器，路径末段是 acc 而不是
    %this），回退到"直接读被调符号的状态"——写法对齐 js_api.js_call。
    """
    frame = in_data.frame
    resolver = in_data.resolver
    status = in_data.status

    state_id = _receiver_state_id(in_data)
    if state_id >= 0:
        states = {
            index
            for index in resolver.collect_newest_states_by_state_ids(frame, status, {state_id})
            if index >= 0
        }
        if states:
            return states

    if status.used_symbols:
        return set(in_data.state_analysis.read_used_states(status.used_symbols[0], in_data.in_states))
    return set()


def _is_arkui_wrapper_receiver(in_data, receiver_states):
    """判断接收者是否是 ArkUI 状态封装对象（精度闸门）。

    转译产物中封装字段统一以 `__` 开头（this.__message / this.__taint ...），
    以此为主判据；否则回退到状态数据类名是否含 ArkUI 封装标识。
    """
    if _receiver_access_path_key(in_data).startswith("__"):
        return True

    frame = in_data.frame
    for state_index in receiver_states:
        state = frame.symbol_state_space[state_index]
        data_type = str(getattr(state, "data_type", "") or "")
        if any(marker in data_type for marker in ARKUI_WRAPPER_MARKERS):
            return True
    return False


def _read_arg_states(in_data, position):
    """读取第 position 个实参对应的状态集合（0 是被调符号/接收者）。"""
    status = in_data.status
    if len(status.used_symbols) <= position:
        return set()
    return set(
        in_data.state_analysis.read_used_states(
            status.used_symbols[position], in_data.in_states
        )
    )


def _read_arg_slot_states(in_data, slot):
    """读取第 slot 个显式实参；status.used_symbols[0] 是被调符号。"""
    return _read_arg_states(in_data, slot + 1)


def _read_string_value(frame, state_indexes):
    """从状态集合里尽力取一个字符串常量（用于 set(k, v) 的 key）。"""
    for state_index in state_indexes:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        value = state.value
        if isinstance(value, str) and len(value) > 0:
            return value.strip('"')
    return ""


def _publish_result(in_data, result_states):
    """把结果状态挂到当前语句定义的符号上（对齐 HScope 的 definedSymbol.states）。"""
    if not result_states:
        return
    defined_symbol = in_data.defined_symbol
    if defined_symbol is not None and hasattr(defined_symbol, "states"):
        defined_symbol.states = set(result_states)
    in_data.status.defined_states.update(result_states)


def _callee_access_path_keys(in_data):
    """返回未解析 callee 的访问路径 key，用于限制同名框架 API 模型。"""
    frame = in_data.frame
    for state_index in in_data.unsolved_callee_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        keys = [
            getattr(point, "key", None)
            for point in (getattr(state, "access_path", None) or [])
        ]
        if keys:
            yield keys


def _is_access_path_method(in_data, owner, method):
    """callee 访问路径同时包含 owner，且最后一段是 method。"""
    return any(keys[-1] == method and owner in keys for keys in _callee_access_path_keys(in_data))


def _build_arguments_from_states(in_data, state_indexes, position=0):
    """把状态下标集合转换为 compute_target_method_states 所需的 Argument 集合。"""
    frame = in_data.frame
    result = set()
    for state_index in state_indexes:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        result.add(
            Argument(
                state_id=state.state_id,
                call_stmt_id=in_data.stmt_id,
                position=position,
                source_symbol_id=state.source_symbol_id,
                access_path=state.access_path,
                index_in_space=state_index,
            )
        )
    return result


def _find_methods_after_constructor(loader, component_name, method_names):
    """兼容 ABC 嵌套组件被折叠到外层 class 的情况。

    HScope 的 ABC 模型也采用这一回退：先找到名为 component_name 的构造方法，
    再向后查找该组件的生命周期方法，遇到下一个组件边界时停止。
    """
    result = set()
    in_component = False
    for method_id in sorted(loader.get_all_method_ids() or set()):
        method_name = loader.convert_method_id_to_method_name(method_id) or ""
        if method_name == component_name:
            in_component = True
            continue
        if not in_component:
            continue
        if method_name in method_names:
            result.add(method_id)
            continue
        if method_name == "paramsLambda" or (
            method_name and not method_name.startswith("%") and method_name[0].isupper()
        ):
            break
    return result


def _find_about_to_appear_before_initial_render(loader, initial_render_id):
    """ABC 将同一文件的多个组件折叠进外层 class；按方法顺序找成对的生命周期。"""
    unit_id = loader.convert_method_id_to_unit_id(initial_render_id)
    for method_id in sorted(loader.get_all_method_ids() or set(), reverse=True):
        if method_id >= initial_render_id:
            continue
        if loader.convert_method_id_to_unit_id(method_id) != unit_id:
            continue
        method_name = loader.convert_method_id_to_method_name(method_id)
        if method_name == "initialRender":
            break
        if method_name == "aboutToAppear":
            return {method_id}
    return set()


def _find_constructor_before_initial_render(loader, initial_render_id):
    """找到当前组件的构造方法；ABC 组件方法在同一单元中连续排列。"""
    unit_id = loader.convert_method_id_to_unit_id(initial_render_id)
    for method_id in sorted(loader.get_all_method_ids() or set(), reverse=True):
        if method_id >= initial_render_id:
            continue
        if loader.convert_method_id_to_unit_id(method_id) != unit_id:
            continue
        name = loader.convert_method_id_to_method_name(method_id) or ""
        if name and name[0].isupper() and not name.startswith("%"):
            return {method_id}
    return set()


def _find_page_map_methods(in_data):
    loader = in_data.frame.loader
    current_class = loader.convert_method_id_to_class_id(in_data.frame.method_id)
    result = set()
    if current_class:
        for method_id in loader.convert_class_id_to_method_ids(current_class) or set():
            if loader.convert_method_id_to_method_name(method_id) == "pageMap":
                result.add(method_id)
    if not result:
        result.update(loader.convert_method_name_to_method_ids("pageMap") or set())
    return result


def _read_object_field_string(in_data, slot, field_name):
    frame = in_data.frame
    for state_index in _read_arg_slot_states(in_data, slot):
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        for field_index in state.fields.get(field_name, set()):
            field_state = frame.symbol_state_space[field_index]
            if isinstance(field_state, State) and util.is_available(field_state.value):
                return str(field_state.value).strip('"').strip("'")
    return ""


def model_set(data):
    """recv.set(v) / recv.set(k, v)：把实参状态写入接收者的内容字段。"""
    in_data = data.in_data
    frame = in_data.frame

    receiver_states = _receiver_states(in_data)
    if not receiver_states or not _is_arkui_wrapper_receiver(in_data, receiver_states):
        return

    # 两个实参视为 (key, value)（对齐 HScope 的 Map.set / AppStorage.SetOrCreate），
    # 一个实参则是纯 value 写入（ObservedPropertySimplePU.set）。
    value_key = WRAPPER_VALUE_KEY
    if len(in_data.status.used_symbols) >= 3:
        key = _read_string_value(frame, _read_arg_states(in_data, 1))
        if util.is_available(key):
            value_key = key
        value_states = _read_arg_states(in_data, 2)
    else:
        value_states = _read_arg_states(in_data, 1)

    if not value_states:
        return

    for state_index in receiver_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        bucket = state.fields.get(value_key)
        if bucket is None:
            bucket = set()
            state.fields[value_key] = bucket
        bucket.update(value_states)

    # set 的返回值即接收者本身（链式调用场景），对齐 HScope。
    _publish_result(in_data, receiver_states)


def model_get(data):
    """recv.get() / recv.get(k)：从接收者的内容字段读出状态作为返回值。"""
    in_data = data.in_data
    frame = in_data.frame

    receiver_states = _receiver_states(in_data)
    if not receiver_states or not _is_arkui_wrapper_receiver(in_data, receiver_states):
        return

    want_key = ""
    if len(in_data.status.used_symbols) >= 2:
        want_key = _read_string_value(frame, _read_arg_states(in_data, 1))

    result_states = set()
    for state_index in receiver_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        if util.is_available(want_key):
            bucket = state.fields.get(want_key)
            if bucket:
                result_states.update(bucket)
        else:
            # 未指定 key：内容字段与躺平元素全部返回
            for bucket in state.fields.values():
                if bucket:
                    result_states.update(bucket)
            result_states.update(state.tangping_elements)

    _publish_result(in_data, result_states)


def model_add(data):
    """recv.add(v)：Set 语义，把实参并入接收者的躺平元素。"""
    in_data = data.in_data
    frame = in_data.frame

    receiver_states = _receiver_states(in_data)
    if not receiver_states or not _is_arkui_wrapper_receiver(in_data, receiver_states):
        return

    value_states = _read_arg_states(in_data, 1)
    if not value_states:
        return

    for state_index in receiver_states:
        state = frame.symbol_state_space[state_index]
        if isinstance(state, State):
            state.tangping_flag = True
            state.tangping_elements.update(value_states)

    _publish_result(in_data, receiver_states)


def model_data_source_add_item(data):
    """IDataSource.addItem(item)：保存条目，供 LazyForEach.create 枚举。"""
    in_data = data.in_data
    frame = in_data.frame
    receiver_ids = {
        state.access_path[-2].state_id
        for index in in_data.unsolved_callee_states
        for state in [frame.symbol_state_space[index]]
        if isinstance(state, State) and len(state.access_path) >= 2
        and state.access_path[-2].state_id > 0
    }
    receiver_states = {
        index for index, state in enumerate(frame.symbol_state_space)
        if isinstance(state, State) and state.state_id in receiver_ids
    }
    if not receiver_states or not (
        _receiver_access_path_key(in_data) == "dataSource"
        or any(
            "DataSource" in str(getattr(frame.symbol_state_space[index], "data_type", ""))
            for index in receiver_states
        )
    ):
        return
    item_states = _read_arg_slot_states(in_data, 0)
    if not item_states:
        return
    if frame.method_name == "aboutToAppear":
        key = (id(frame.symbol_state_space), frame.method_id)
        # 保留状态空间的引用，防止后续入口复用其 id 后误取旧条目。
        space, saved_items = _LAZY_ITEMS_BY_LIFECYCLE.setdefault(
            key, (frame.symbol_state_space, set())
        )
        if space is frame.symbol_state_space:
            saved_items.update(item_states)
    for state_index in receiver_states:
        state = in_data.frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        state.tangping_elements.update(item_states)
        for items_index in state.fields.get("items", set()):
            items_state = in_data.frame.symbol_state_space[items_index]
            if isinstance(items_state, State):
                items_state.tangping_elements.update(item_states)
                items_state.array.append(set(item_states))
    _publish_result(in_data, receiver_states)


def _collect_callback_method_ids(in_data, state_index):
    """取出某个实参状态里承载的方法 id（即回调）。

    两种形态都要覆盖：
      1. 直接传入的函数/闭包，如 `Text.onClick(() => { this.func1(); })`；
      2. 成员形式的方法引用，如 `this.declareWatch("brand", this.onBrandChanged)`
         或 `Button.onClick(this.method)`，此时实参是成员读取的结果状态，
         真正承载方法的状态需经 resolver 解析（写法对齐 js_api.js_call 里
         用 obtain_parent_states 定位方法状态的做法）。
    """
    frame = in_data.frame
    state_analysis = in_data.state_analysis

    candidate_indexes = [state_index]
    try:
        candidate_indexes.extend(
            in_data.resolver.obtain_parent_states(
                in_data.stmt_id, frame, in_data.status, state_index
            ) or set()
        )
    except Exception:
        pass

    method_ids = set()
    for candidate_index in candidate_indexes:
        state = frame.symbol_state_space[candidate_index]
        if not isinstance(state, State):
            continue
        if getattr(state, "data_type", None) != LIAN_INTERNAL.METHOD_DECL:
            try:
                if not state_analysis.is_state_a_method_decl(state):
                    continue
            except Exception:
                continue
        value = getattr(state, "value", None)
        # 列式数据模型里方法 id 可能是 float（如 137.0），需一并接受
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and value > 0:
            method_ids.add(int(value))
    return method_ids


def _method_ids_from_component_fields(in_data, component_states, field_name):
    """优先使用组件实例上的方法字段，避免 ABC 同一外层 class 中的方法同名。"""
    method_ids = set()
    frame = in_data.frame
    for state_index in component_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        for field_index in state.fields.get(field_name, set()):
            method_ids.update(_collect_callback_method_ids(in_data, field_index))
    return method_ids


def model_callback(data):
    """ArkUI 事件回调建模：把绑定的回调函数当作被调方法分析。

    对应 HScope 的 handleUiCallback / isUiCallbackMethod。典型形态：

        Text.onClick(() => { this.func1(); })      -> onClick(cb)
        this.observeComponentCreation2((elmtId, isInitialRender) => {...}, Text)
        Text.onChange((value) => {...})
        this.declareWatch("brand", this.onBrandChanged)

    这些调用自身是外部方法，回调体的宿主方法(如 Child.func1，汇点 hilog 所在处)
    若不分析，污点在 SFG 中就没有汇点，必然漏报。
    """
    in_data = data.in_data
    state_analysis = in_data.state_analysis
    status = in_data.status
    defined_symbol = in_data.defined_symbol
    args = in_data.args

    callback_method_ids = set()
    for arg_set in (getattr(args, "positional_args", None) or []):
        for arg in arg_set:
            callback_method_ids.update(_collect_callback_method_ids(in_data, arg.index_in_space))

    if not callback_method_ids:
        return

    # pageMap 中的 observeComponentCreation2(cb, {name: "TargetPage"})：
    # 把目标组件名带到 cb 内的 ViewPU.create(component)。
    if any(
        keys[-1] == "observeComponentCreation2"
        for keys in _callee_access_path_keys(in_data)
    ):
        component_name = _read_object_field_string(in_data, 1, "name")
        if util.is_available(component_name):
            for method_id in callback_method_ids:
                _COMPONENT_NAME_BY_CALLBACK_METHOD[method_id] = component_name

    this_states = set()
    receiver_state_id = _receiver_state_id(in_data)
    if receiver_state_id >= 0:
        this_states = _receiver_states(in_data)

    # 独立入口的 initialRender 也必须先运行本组件的 aboutToAppear，
    # 否则父组件在该生命周期写入的状态无法传给之后创建的子组件。
    frame = in_data.frame
    if (
        any(keys[-1] == "observeComponentCreation2" for keys in _callee_access_path_keys(in_data))
        and frame.loader.convert_method_id_to_method_name(frame.method_id) == "initialRender"
        and frame.caller_id < 0
        and this_states
    ):
        for marker, lifecycle_ids in (
            ("_arkui_constructor_called", _find_constructor_before_initial_render(frame.loader, frame.method_id)),
            ("_arkui_about_to_appear_called", _find_about_to_appear_before_initial_render(frame.loader, frame.method_id)),
        ):
            if getattr(frame, marker, False):
                continue
            if lifecycle_ids:
                data.out_data = state_analysis.compute_target_method_states(
                    in_data.stmt_id, in_data.stmt, status, in_data.in_states,
                    lifecycle_ids, defined_symbol, MethodCallArguments(), this_states,
                )
                if data.out_data and data.out_data.interruption_flag:
                    return
            setattr(frame, marker, True)

    data.out_data = state_analysis.compute_target_method_states(
        in_data.stmt_id, in_data.stmt, status, in_data.in_states,
        callback_method_ids, defined_symbol, args, this_states
    )


def model_navigation_push_path_by_name(data):
    """NavPathStack.pushPathByName(name, payload)：保存 payload 并进入 pageMap。

    官方语义是把 name 对应的 NavDestination 页面连同 payload 一起入栈。
    ABC benchmark 中目标构造通过当前组件的 pageMap(name, payload) 完成，因此
    这里显式调用 pageMap，让后续 ViewPU.create/onReady 模型自然接上。
    """
    in_data = data.in_data
    frame = in_data.frame

    target_name = _read_string_value(frame, _read_arg_slot_states(in_data, 0))
    payload_states = {
        index
        for index in _read_arg_slot_states(in_data, 1)
        if isinstance(frame.symbol_state_space[index], State)
    }
    if not util.is_available(target_name) or not payload_states:
        return

    _NAVIGATION_PAYLOADS_BY_SPACE[id(frame.symbol_state_space)] = set(payload_states)

    page_map_methods = _find_page_map_methods(in_data)
    if not page_map_methods:
        return

    real_args = MethodCallArguments(
        positional_args=[
            _build_arguments_from_states(in_data, _read_arg_slot_states(in_data, 0), 0),
            _build_arguments_from_states(in_data, payload_states, 1),
        ],
        named_args=[],
    )
    data.out_data = in_data.state_analysis.compute_target_method_states(
        in_data.stmt_id,
        in_data.stmt,
        in_data.status,
        in_data.in_states,
        page_map_methods,
        in_data.defined_symbol,
        real_args,
        _receiver_states(in_data),
    )


def model_view_create(data):
    """ViewPU/ViewV2.create(component)：先触发 aboutToAppear，再首次渲染。"""
    in_data = data.in_data
    if _is_access_path_method(in_data, "LazyForEach", "create"):
        model_lazy_foreach_create(data)
        return
    if not (
        _is_access_path_method(in_data, "ViewPU", "create")
        or _is_access_path_method(in_data, "ViewV2", "create")
    ):
        return

    component_states = {
        index
        for index in _read_arg_slot_states(in_data, 0)
        if isinstance(in_data.frame.symbol_state_space[index], State)
    }
    component_name = _COMPONENT_NAME_BY_CALLBACK_METHOD.get(in_data.frame.method_id, "")
    if not component_states or not util.is_available(component_name):
        return

    loader = in_data.frame.loader
    about_to_appear_methods = _method_ids_from_component_fields(
        in_data, component_states, "aboutToAppear"
    )
    initial_render_methods = _method_ids_from_component_fields(
        in_data, component_states, "initialRender"
    )
    if not initial_render_methods:
        initial_render_methods = _find_methods_after_constructor(
            loader, component_name, {"initialRender"}
        )
    if not about_to_appear_methods:
        about_to_appear_methods = _find_methods_after_constructor(
            loader, component_name, {"aboutToAppear"}
        )
    for method_ids in (about_to_appear_methods, initial_render_methods):
        if not method_ids:
            continue
        data.out_data = in_data.state_analysis.compute_target_method_states(
            in_data.stmt_id,
            in_data.stmt,
            in_data.status,
            in_data.in_states,
            method_ids,
            in_data.defined_symbol,
            MethodCallArguments(),
            component_states,
        )
        if data.out_data and data.out_data.interruption_flag:
            return


def model_lazy_foreach_create(data):
    """LazyForEach.create：以数据源中的条目执行条目生成回调。"""
    in_data = data.in_data
    frame = in_data.frame
    data_source_states = _read_arg_slot_states(in_data, 2)
    item_states = set()
    for state_index in data_source_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        item_states.update(state.tangping_elements)
        for items_index in state.fields.get("items", set()):
            items_state = frame.symbol_state_space[items_index]
            if not isinstance(items_state, State):
                continue
            item_states.update(items_state.tangping_elements)
            for slot in items_state.array:
                item_states.update(slot)
    for lifecycle_id in _find_about_to_appear_before_initial_render(frame.loader, frame.method_id):
        saved = _LAZY_ITEMS_BY_LIFECYCLE.get((id(frame.symbol_state_space), lifecycle_id))
        if saved and saved[0] is frame.symbol_state_space:
            item_states.update(saved[1])

    callback_method_ids = set()
    for slot in (3, 4):
        for state_index in _read_arg_slot_states(in_data, slot):
            callback_method_ids.update(_collect_callback_method_ids(in_data, state_index))
    callback_method_ids = {
        method_id for method_id in callback_method_ids
        if (frame.loader.convert_method_id_to_method_name(method_id) or "").startswith(
            "__lazyForEachItem"
        )
    }
    if not callback_method_ids or not item_states:
        return

    real_args = MethodCallArguments(
        positional_args=[_build_arguments_from_states(in_data, item_states, 0)],
        named_args=[],
    )
    data.out_data = in_data.state_analysis.compute_target_method_states(
        in_data.stmt_id, in_data.stmt, in_data.status, in_data.in_states,
        callback_method_ids, in_data.defined_symbol, real_args, set(),
    )


def model_nav_destination_on_ready(data):
    """NavDestination.onReady(cb)：以 context.pathInfo.param 调用 cb。"""
    in_data = data.in_data
    if not _is_access_path_method(in_data, "NavDestination", "onReady"):
        return

    callback_method_ids = set()
    for state_index in _read_arg_slot_states(in_data, 0):
        callback_method_ids.update(_collect_callback_method_ids(in_data, state_index))

    payload_states = set(
        _NAVIGATION_PAYLOADS_BY_SPACE.get(id(in_data.frame.symbol_state_space), set())
    )
    if not callback_method_ids or not payload_states:
        return

    state_analysis = in_data.state_analysis
    status = in_data.status
    path_info_index = state_analysis.create_state_and_add_space(
        status,
        in_data.stmt_id,
        value="NavDestination.pathInfo",
        data_type="object",
    )
    context_index = state_analysis.create_state_and_add_space(
        status,
        in_data.stmt_id,
        value="NavDestination.context",
        data_type="object",
    )
    path_info_state = in_data.frame.symbol_state_space[path_info_index]
    context_state = in_data.frame.symbol_state_space[context_index]
    path_info_state.fields["param"] = set(payload_states)
    context_state.fields["pathInfo"] = {path_info_index}
    status.defined_states.update({path_info_index, context_index})

    for payload_index in payload_states:
        state_analysis.sfg.add_edge(
            state_analysis.make_state_sfg_node(payload_index),
            state_analysis.make_state_sfg_node(path_info_index),
            state_analysis.make_stmt_sfg_edge(
                in_data.stmt_id,
                name="NavDestination.onReady.param",
            ),
        )

    real_args = MethodCallArguments(
        positional_args=[_build_arguments_from_states(in_data, {context_index}, 0)],
        named_args=[],
    )
    data.out_data = state_analysis.compute_target_method_states(
        in_data.stmt_id,
        in_data.stmt,
        status,
        in_data.in_states,
        callback_method_ids,
        in_data.defined_symbol,
        real_args,
        set(),
    )


def model_ability_on_create_return(data):
    """UIAbility.onCreate 结束后，以同一实例进入可能发生的 onForeground。"""
    in_data = data.in_data
    frame = in_data.frame
    if frame.method_name != "onCreate":
        return

    loader = frame.loader
    class_id = loader.convert_method_id_to_class_id(frame.method_id)
    class_name = loader.convert_class_id_to_class_name(class_id) if class_id else ""
    if not class_name.endswith(".EntryAbility"):
        return
    on_foreground_ids = {
        method_id
        for method_id in loader.convert_class_id_to_method_ids(class_id) or set()
        if loader.convert_method_id_to_method_name(method_id) == "onForeground"
    }
    this_symbol_id = frame.method_def_use_summary.this_symbol_id
    initial_this_states = {
        state_index
        for symbol in frame.symbol_state_space
        if getattr(symbol, "name", None) == "%this"
        and getattr(symbol, "symbol_id", None) == this_symbol_id
        for state_index in getattr(symbol, "states", set())
    }
    this_state_ids = {
        frame.symbol_state_space[index].state_id
        for index in initial_this_states
        if isinstance(frame.symbol_state_space[index], State)
    }
    this_states = set(in_data.state_analysis.resolver.collect_newest_states_by_state_ids(
        frame, in_data.status, this_state_ids
    )) if this_state_ids else set()
    if not on_foreground_ids or not this_states:
        return

    data.out_data = in_data.state_analysis.compute_target_method_states(
        in_data.stmt_id,
        in_data.stmt,
        in_data.status,
        in_data.in_states,
        on_foreground_ids,
        None,
        MethodCallArguments(),
        this_states,
    )


# 会调用其回调参数的 ArkUI 事件绑定方法（对齐 HScope 的 isUiCallbackMethod 白名单）
UI_CALLBACK_METHODS = (
    "onClick",
    "onChange",
    "onSubmit",
    "onAppear",
    "onDisAppear",
    "onDetach",
    "onAreaChange",
    "onScroll",
    "onTouch",
    "onHover",
    "observeComponentCreation2",
    "ifElseBranchUpdateFunction",
    "loadContent",
    # @Watch('cb') 转译为 this.declareWatch("<属性名>", this.cb)：
    # 属性变更时由框架触发 cb，cb 内会重新读取该属性（污点由此到达汇点）。
    "declareWatch",
)


# emitter 事件名 -> 已登记回调方法 id。emit 时据此把事件数据交给回调。
_EMITTER_CALLBACKS = {}


def model_emitter_register(data):
    """emitter.on/once(eventName, cb)：按事件名登记回调。

    蓝牙 stateChange 由系统事件触发，没有应用侧 emit；注册时也分析其回调。
    """
    in_data = data.in_data
    frame = in_data.frame
    args = in_data.args

    event_name = _read_string_value(frame, _read_arg_states(in_data, 1))
    if not util.is_available(event_name):
        return

    callbacks = set()
    for arg_set in (getattr(args, "positional_args", None) or []):
        for arg in arg_set:
            callbacks.update(_collect_callback_method_ids(in_data, arg.index_in_space))
    if callbacks:
        _EMITTER_CALLBACKS.setdefault(event_name, set()).update(callbacks)
        if event_name == "stateChange" and any(
            keys[-1] == "on" and "bluetooth.access" in keys
            for keys in _callee_access_path_keys(in_data)
        ):
            data.out_data = in_data.state_analysis.compute_target_method_states(
                in_data.stmt_id, in_data.stmt, in_data.status, in_data.in_states,
                callbacks, in_data.defined_symbol, MethodCallArguments(), set(),
            )


def model_emitter_emit(data):
    """emitter.emit(eventName, eventData)：把事件数据作为实参调用已登记的回调。

    不建模时，`emitter.once(name, (event) => {... data['brand'] ... hilog ...})`
    的回调体永远不可达，汇点不存在，污点必然漏报。
    """
    in_data = data.in_data
    frame = in_data.frame
    state_analysis = in_data.state_analysis
    status = in_data.status

    event_name = _read_string_value(frame, _read_arg_states(in_data, 1))
    callback_method_ids = set(_EMITTER_CALLBACKS.get(event_name, set()))
    if not callback_method_ids:
        return

    payload_args = set()
    for state_index in _read_arg_states(in_data, 2):
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        payload_args.add(
            Argument(
                state_id = state.state_id,
                call_stmt_id = in_data.stmt_id,
                position = state,
                source_symbol_id = state.source_symbol_id,
                access_path = state.access_path,
                index_in_space = state_index,
            )
        )
    real_args = MethodCallArguments([payload_args], []) if payload_args else in_data.args

    data.out_data = state_analysis.compute_target_method_states(
        in_data.stmt_id, in_data.stmt, status, in_data.in_states,
        callback_method_ids, in_data.defined_symbol, real_args, set()
    )


# ---- @Provide / @Consume：按字符串 key 的跨组件通道 ----
# 常量与 events/default_event_handlers/abc_arkui_component.py 保持一致
# （HScope 里这两个常量也是两个文件各写一份）。
ARKUI_PROVIDED_PREFIX = "ArkUI.provided:"
ARKUI_PARENT_FIELD = "__arkui_parent"

# 组件通道注册表：用 state_id 索引而不是状态下标。
# 原因：同一个组件实例在分析中会有多个"状态副本"（构造时的 %this 与 new_object
# 建出的实例状态下标不同，但共享同一个 state_id），只按下标找会在中间断链。
# 提供方 state_id -> {key: {wrapper 状态下标}}
ARKUI_PROVIDED_BY_STATE_ID = {}
# 子组件 state_id -> {父组件状态下标}（下标属于记录时的那个状态空间）
ARKUI_PARENT_BY_STATE_ID = {}
# 状态空间 id -> {key: {wrapper 状态下标}}（同一次入口分析内的扁平注册表）
ARKUI_PROVIDED_IN_SPACE = {}


def model_add_provided_var(data):
    """this.addProvidedVar("brand", this.__brand, false)：登记 key -> 提供的 wrapper 状态。

    对齐 HScope CollectionModeling.handleArkuiAddProvidedVar：把 wrapper 记在提供方
    组件自身状态（this）的字段里，供后代组件按 key 回溯。
    """
    in_data = data.in_data
    frame = in_data.frame
    receiver_states = _receiver_states(in_data)
    if not receiver_states:
        return

    key = _read_string_value(frame, _read_arg_states(in_data, 1))
    if not util.is_available(key):
        return
    wrapper_states = _read_arg_states(in_data, 2)
    if not wrapper_states:
        return

    for state_index in receiver_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        state.fields.setdefault(ARKUI_PROVIDED_PREFIX + key, set()).update(wrapper_states)
        state_id = getattr(state, "state_id", None)
        if state_id is not None:
            # 记录 (状态空间 id, 下标)：下标只在同一状态空间内有效
            space_id = id(frame.symbol_state_space)
            ARKUI_PROVIDED_BY_STATE_ID.setdefault(state_id, {}).setdefault(key, set()).update(
                (space_id, index) for index in wrapper_states
            )
            # 同时登记到"按空间的扁平注册表"：@Provide/@Consume 在运行时本就是全局
            # key 注册表，组件树被 ViewPU.create 串进同一入口后，按 key 直查即可，
            # 不受"状态副本 state_id 不同"的影响。
            ARKUI_PROVIDED_IN_SPACE.setdefault(space_id, {}).setdefault(key, set()).update(
                wrapper_states
            )


def _find_provided_states(frame, start_states, key):
    """沿组件父链向上回溯，找到 key 对应的提供方 wrapper 状态。

    同时走两条路：状态自身的字段（同一下标空间内直接可见）与按 state_id 登记的
    注册表（跨"状态副本"，即同一实例在构造时与 new_object 时下标不同的情况）。
    """
    queue = list(start_states)
    visited_state_ids = set()
    while queue:
        state_index = queue.pop(0)
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue

        state_id = getattr(state, "state_id", None)
        if state_id is not None:
            if state_id in visited_state_ids:
                continue
            visited_state_ids.add(state_id)

        space_id = id(frame.symbol_state_space)
        provided = set(state.fields.get(ARKUI_PROVIDED_PREFIX + key) or set())
        if not provided and state_id is not None:
            for entry_space_id, index in (ARKUI_PROVIDED_BY_STATE_ID.get(state_id) or {}).get(key, set()):
                if entry_space_id == space_id:
                    provided.add(index)
        if provided:
            return provided

        queue.extend(state.fields.get(ARKUI_PARENT_FIELD) or set())
        if state_id is not None:
            for entry_space_id, index in ARKUI_PARENT_BY_STATE_ID.get(state_id, set()):
                if entry_space_id == space_id:
                    queue.append(index)
    return set()


def model_initialize_consume(data):
    """this.initializeConsume("brand", "brand")：沿父链取到提供方的值作为本字段的值。

    对齐 HScope CollectionModeling.handleArkuiInitializeConsume：先沿父子链找到
    提供方登记的 wrapper，再取其内容字段（wrapper 的 value）作为消费方的值。
    """
    in_data = data.in_data
    frame = in_data.frame
    receiver_states = _receiver_states(in_data)
    if not receiver_states:
        return

    key = _read_string_value(frame, _read_arg_states(in_data, 1))
    if not util.is_available(key):
        return

    provided_states = _find_provided_states(frame, receiver_states, key)
    if not provided_states:
        return

    value_states = set()
    for state_index in provided_states:
        state = frame.symbol_state_space[state_index]
        if not isinstance(state, State):
            continue
        value_states.update(state.fields.get(WRAPPER_VALUE_KEY, set()))
    if not value_states:
        # 兜底：至少把 wrapper 本身当作值，保留别名关系
        value_states = set(provided_states)

    _publish_result(in_data, value_states)


METHOD_NAME_TO_MODEL = {
    "set": model_set,
    "get": model_get,
    "add": model_add,
    "addItem": model_data_source_add_item,
    # Promise.then(cb)：自身是外部方法，但必须分析 cb（汇点常在 cb 内）。
    "then": model_callback,
    # emitter 事件：按事件名把 emit 的数据交给 on/once 登记的回调。
    "on": model_emitter_register,
    "once": model_emitter_register,
    "emit": model_emitter_emit,
    # @Provide / @Consume：按字符串 key 的跨组件通道（沿组件父子链回溯）
    "addProvidedVar": model_add_provided_var,
    "initializeConsume": model_initialize_consume,
    # Navigation：push 保存参数并进入 pageMap；ViewPU.create 触发目标组件渲染；
    # onReady 以 context.pathInfo.param 把参数交给目标页回调。
    "pushPathByName": model_navigation_push_path_by_name,
    "create": model_view_create,
    "onReady": model_nav_destination_on_ready,
}
METHOD_NAME_TO_MODEL.update({name: model_callback for name in UI_CALLBACK_METHODS})
