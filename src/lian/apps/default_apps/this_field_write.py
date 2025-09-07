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
    if receiver_symbol.name != LIAN_INTERNAL.THIS:
        return app_return
    class_id = loader.convert_method_id_to_class_id(frame.method_id)
    class_members = loader.class_id_to_members[class_id]
    for each_field_state_index in field_states:
        each_field_state = frame.symbol_state_space[each_field_state_index]
        if not isinstance(each_field_state, State):
            continue
        field_name = str(each_field_state.value)
        if len(field_name) == 0:
            continue
        # FIXME 分支living graph，会覆盖
        class_members[field_name] = source_states
    return app_return



