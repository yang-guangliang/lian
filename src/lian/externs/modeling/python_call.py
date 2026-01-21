#!/usr/bin/env python3

from lian.events.handler_template import EventData

from lian.common_structs import (
    Argument,
    MethodCallArguments,
    State,
    Symbol
)
from lian.config.constants import LIAN_INTERNAL
import lian.events.event_return as er

def dispatch(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    state_analysis = in_data.state_analysis
    loader = state_analysis.loader
    app_return = er.config_event_unprocessed()
    stmt_src_code = "\n".join(loader.get_stmt_source_code_with_comment(stmt_id))
    if "cls.executor.apply_async" in stmt_src_code:
        apply_async(data)
        app_return = er.config_block_event_requester(app_return)
        return app_return
    elif "self.executor.submit" in stmt_src_code:
        executor_submit(data)
        app_return = er.config_block_event_requester(app_return)
        return app_return
    elif "return self._call_with_config(self._format_prompt_with_error_handling," in stmt_src_code:
        call_with_config(data)
        app_return = er.config_block_event_requester(app_return)
        return app_return
    elif "cls(*init_inputs, **init_kwargs)" in stmt_src_code:
        init(data)
        app_return = er.config_block_event_requester(app_return)
        return app_return
    elif "self.model_executor = executor_class(vllm_config=vllm_config, )" in stmt_src_code:
        executor_class(data)
        app_return = er.config_block_event_requester(app_return)
        return app_return
    else:
        app_return = er.config_continue_event_processing(app_return)
        return app_return


def executor_submit(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    state_analysis = in_data.state_analysis
    loader = state_analysis.loader
    stmt_src_code = "\n".join(loader.get_stmt_source_code_with_comment(stmt_id))
    if not "Executor.on_graph_execution" in stmt_src_code:
        return
    stmt = in_data.stmt
    status = in_data.status.copy()
    in_states = in_data.in_states
    defined_symbol = in_data.defined_symbol
    args = in_data.args

    real_method_ids = loader.convert_method_name_to_method_ids("on_graph_execution")
    real_positional_args = []
    positional_args = args.positional_args

    for arg_index,arg_set in enumerate(positional_args):
        if arg_index == 0:
            continue
        real_positional_args.append(arg_set)
    real_args = MethodCallArguments(real_positional_args, [])

    data.out_data = state_analysis.compute_target_method_states(
        stmt_id, stmt, status, in_states, real_method_ids, defined_symbol, real_args
    )


def apply_async(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    state_analysis = in_data.state_analysis
    loader = state_analysis.loader
    stmt_src_code = "\n".join(loader.get_stmt_source_code_with_comment(stmt_id))
    if not "cls.on_node_execution," in stmt_src_code:
        return
    stmt = in_data.stmt
    status = in_data.status.copy()
    in_states = in_data.in_states
    defined_symbol = in_data.defined_symbol
    args = in_data.args

    real_method_ids = loader.convert_method_name_to_method_ids("on_node_execution")
    real_positional_args = []
    positional_args = args.positional_args
    args_tuple = (None, None)

    for arg_index, arg_set in enumerate(positional_args):
        if arg_index == 0:
            continue
        args_tuple = arg_set
    real_positional_args.append(args_tuple)
    real_positional_args.append(args_tuple)
    real_args = MethodCallArguments(real_positional_args, [])

    data.out_data = state_analysis.compute_target_method_states(
        stmt_id, stmt, status, in_states, real_method_ids, defined_symbol, real_args
    )

def call_with_config(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    state_analysis = in_data.state_analysis
    loader = state_analysis.loader
    stmt = in_data.stmt
    status = in_data.status.copy()
    in_states = in_data.in_states
    defined_symbol = in_data.defined_symbol
    args = in_data.args

    real_method_ids = loader.convert_method_name_to_method_ids("_format_prompt_with_error_handling")
    real_positional_args = []
    positional_args = args.positional_args

    for arg_index, arg_set in enumerate(positional_args):
        if arg_index == 1:
            real_positional_args.append(arg_set)
    real_args = MethodCallArguments(real_positional_args, [])

    data.out_data = state_analysis.compute_target_method_states(
        stmt_id, stmt, status, in_states, real_method_ids, defined_symbol, real_args
    )

def init(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    state_analysis = in_data.state_analysis
    loader = state_analysis.loader
    stmt_src_code = "\n".join(loader.get_stmt_source_code_with_comment(stmt_id))

    stmt = in_data.stmt
    status = in_data.status.copy()
    in_states = in_data.in_states
    defined_symbol = in_data.defined_symbol

    args = in_data.args

    real_method_ids = loader.convert_method_name_to_method_ids("__init__")
    method_ids = set()
    for method_id in real_method_ids:
        stmt = loader.get_stmt_gir(method_id)
        if stmt.start_row == 167:
            method_ids.add(method_id)
            break


    data.out_data = state_analysis.compute_target_method_states(
        stmt_id, stmt, status, in_states, method_ids, defined_symbol, args
    )

def executor_class(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    state_analysis = in_data.state_analysis
    loader = state_analysis.loader
    stmt = in_data.stmt
    status = in_data.status.copy()
    in_states = in_data.in_states
    defined_symbol = in_data.defined_symbol
    args = in_data.args

    real_method_ids = loader.convert_method_name_to_method_ids("__init__")
    class_ids = loader.convert_class_name_to_class_ids("ExecutorBase")
    res = -1
    for real_method_id in real_method_ids:
        if loader.convert_method_id_to_class_id(real_method_id) in class_ids:
            res = real_method_id
            break
    real_method_ids = {res}
    # TODO 已经找到了正确的callee_id，待傲寒补充参数的传递
    # self.model_executor = executor_class(vllm_config=vllm_config, )
    # 将executor_class写死到ExecutorBase.__init__方法上去
    # 应该调用ExecutorBase.__init__(vllm_config=vllm_config, )

    data.out_data = state_analysis.compute_target_method_states(
        stmt_id, stmt, status, in_states, real_method_ids, defined_symbol, args
    )
