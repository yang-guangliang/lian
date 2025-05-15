#!/usr/bin/env python3

from lian.apps.app_template import EventData

from lian.semantic.semantic_structure import (
    State,
    Symbol
)

def js_call(data: EventData):
    in_data = data.in_data
    stmt_id = in_data.stmt_id
    stmt = in_data.stmt
    status = in_data.status.copy()
    in_states = in_data.in_states
    defined_symbol = in_data.defined_symbol
    resolver = in_data.resolver
    frame = in_data.frame
    state_analysis = in_data.state_analysis
    args = in_data.args

    this_symbol_index = status.used_symbols.pop(0)
    name_symbol: Symbol = frame.symbol_state_space[this_symbol_index]
    this_states = state_analysis.read_used_states(this_symbol_index, in_states)

    real_method_ids = set()
    unsolved_callee_states = in_data.unsolved_callee_states
    for callee_state in unsolved_callee_states:
        parent_id = resolver.obtain_parent_states(stmt_id, frame, status, callee_state)
        if not parent_id:
            continue
        state_analysis.cancel_key_state(name_symbol.symbol_id, callee_state, stmt_id)
        real_method_ids.update(parent_id)

    callee_method_ids = set()
    for each_state_index in real_method_ids:
        each_state = frame.symbol_state_space[each_state_index]
        if not isinstance(each_state, State):
            continue

        if state_analysis.is_state_a_method_decl(each_state):
            if each_state.value:
                callee_method_ids.add(int(each_state.value))

    return state_analysis.compute_target_method_states(
        stmt_id, stmt, status, in_states, callee_method_ids, defined_symbol, args, this_states
    )




