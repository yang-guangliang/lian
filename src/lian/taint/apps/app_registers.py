#!/usr/bin/env python3


from lian.apps.app_template import (
    AppSummary,
    EventHandler
)
from taint.apps.taint_apps.read_rules import (
    RuleApply,
)
from taint.apps.taint_apps.prop_app import (
    foreach_item_prop,
    send_to_router,
    read_from_router,
)
from taint.constants import (
    EventKind,
)
from lian.config import config

class DefaultApp(AppSummary):
    def enable(self):
        self.app_manager.register_list([
            EventHandler(
                event = EventKind.PROP_FOREACH_ITEM,
                handler = foreach_item_prop,
                langs = [config.ANY_LANG]
            ),
            EventHandler(
                event = EventKind.CALL_BEFORE,
                handler = send_to_router,
                langs = [config.ANY_LANG]
            ),
            EventHandler(
                event = EventKind.CALL_BEFORE,
                handler = read_from_router,
                langs = [config.ANY_LANG]
            ),
            EventHandler(
                event = EventKind.TAINT_BEFORE,
                handler = RuleApply().read_and_apply_source_rules,
                langs = [config.ANY_LANG]
            ),

            EventHandler(
                event = EventKind.SINK_BEFORE,
                handler = RuleApply().read_and_apply_sink_rules,
                langs = [config.ANY_LANG]
            ),
            EventHandler(
                event = EventKind.PROP_BEFORE,
                handler = RuleApply().read_and_apply_prop_rules,
                langs = [config.ANY_LANG]
            ),

        ])

