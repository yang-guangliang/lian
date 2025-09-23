#!/usr/bin/env python3


# tag propagation
# - given a statement, check if we need to propagate the operands' tags to the result/target
#    * symbol level
#    * state level
import sys

from pandas.core import frame
import config1 as config
sys.path.extend([config.LIAN_DIR, config.TAINT_DIR])
# dispatch stmt -> handle (check source/ manage tag/ check sink)
import taint.apps.event_return as er

from rule_manager import RuleManager

from taint.apps.app_template import EventData
from taint import config1 as config
from taint.constants import EventKind
from taint.taint_structs import (MethodTaintFrame, PropagationResult)#, TagBitVectorManager, CallInfo
from taint.propagation import TaintPropagationInMethod
from taint.apps.app_manager import AppManager
from lian.util import util
from lian.util.loader import Loader

from lian.semantic.semantic_structs import (
    Symbol
)

class GlobalPropagation(TaintPropagationInMethod):
    def __init__(self, frame: MethodTaintFrame):
        super().__init__(frame)
    
    def call_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        status = self.frame.stmt_id_to_status[stmt_id]
        event = EventData(
                "abc",
                EventKind.CALL_BEFORE,
                {
                    "stmt_id"           : stmt_id,
                    "stmt"              : stmt,
                    "operation"         : "call_stmt",
                    "rules"             : self.rule_manager,
                    "in_taint"          : in_taint,   
                    "taint_status"      : taint_status,
                    "frame"             : self.frame,
                    "taint_state_manager": self.frame.taint_state_manager,
                    "status"             : status,
                }
            )
        app_return = self.app_manager.notify(event)
        event.event = EventKind.TAINT_BEFORE
        app_return = self.app_manager.notify(event)
        event.event = EventKind.PROP_BEFORE
        app_return = self.app_manager.notify(event)
        event.event = EventKind.SINK_BEFORE
        app_return = self.app_manager.notify(event)
        if er.should_block_event_requester(app_return):
            return

        # 判断是否完全分析完了
        callee_info = PropagationResult(stmt_id)

        if len(self.frame.current_call_site) == 3 and self.frame.current_call_site[1] == stmt_id:
            callee_info.interruption_flag = True

        status = self.frame.stmt_id_to_status[stmt_id]
        target_space = self.frame.symbol_state_space[status.defined_symbol]
        # self.propagate_tags(stmt_id, in_taint, taint_status)
        # TODO：如果这条call_stmt在call_graph上没有后继，说明静态分析解析失败，调用LLM来处理

        callee_info.stmt_id = stmt_id
        # 收集return symbol的tag，交给target
        if self.frame.callee_return:
            taint_status.out_taint[target_space.symbol_id] = self.frame.callee_return
            self.frame.callee_return = None
        return callee_info