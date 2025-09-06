#!/usr/bin/env python3

import os
import ast
import dataclasses,pprint
import lian.util.data_model as dm

from lian.util import util
from lian.config import config
from lian.util.loader import Loader
from lian.config.constants import (
    EVENT_KIND,
    LIAN_SYMBOL_KIND,
    LIAN_INTERNAL
)
from lian.apps.app_template import EventData
from lian.semantic.semantic_structs import SimpleWorkList

@dataclasses.dataclass
class EntryPointRule:
    lang: str = ""
    unit_id: int = -1
    unit_path: str = ""
    unit_name: str = ""
    method_id: int = -1
    method_name: list[str] = dataclasses.field(default_factory=list)
    attrs: list[str] = dataclasses.field(default_factory=list)
    args: str = ""
    return_type: str = ""

class EntryPointGenerator:
    def __init__(self, options, app_manager, loader) -> None:
        self.options = options
        self.app_manager = app_manager
        self.loader:Loader = loader
        self.entry_points = set()
        self.entry_point_rules = [
            EntryPointRule(method_name = [LIAN_INTERNAL.UNIT_INIT]),
            EntryPointRule(lang = "java", method_name = ["main"], attrs = ["static"]),
            EntryPointRule(lang = "abc", method_name = ["init", "paramsLambda", "requestOAIDTrackingConsentPermissions", "onPageShow", "aboutToAppear", "func_main_0", "onWindowStageCreate"]),
        ]

    def scan_js_ts_exported_method(self):
        pass

    def check_entry_point_rules(self, lang, unit_id, unit_path, method_id, method_name, attrs = [], args = "", return_type = ""):
        unit_name = os.path.basename(unit_path)
        for rule in self.entry_point_rules:
            if rule.lang:
                if rule.lang != lang:
                    continue

            if rule.unit_id >= 0:
                if rule.unit_id != unit_id:
                    continue
            else:
                if rule.unit_name:
                    if rule.unit_name != unit_name:
                        continue
                if rule.unit_path:
                    if rule.unit_path != unit_path:
                        continue

            if rule.method_id >= 0:
                if rule.method_id == method_id:
                    return True
                continue

            if len(rule.method_name) > 0:
                if method_name not in rule.method_name:
                    continue

            if rule.attrs:
                if len(attrs) == 0:
                    continue
                contained_flag = True
                for one_attr in rule.attrs:
                    if one_attr not in attrs:
                        contained_flag = False
                        break
                if not contained_flag:
                    continue

            if rule.args:
                if rule.args != args:
                    continue

            if rule.return_type:
                if rule.return_type != return_type:
                    continue
            return True

        return False

    def collect_entry_points_from_unit_scope(self, unit_info, unit_scope):
        all_method_scopes = unit_scope.query(unit_scope.scope_kind.eq(LIAN_SYMBOL_KIND.METHOD_KIND))
        for scope in all_method_scopes:
            name = ""
            attrs = []
            if util.is_available(scope.name):
                name = scope.name
            if util.is_available(scope.attrs):
                attrs = scope.attrs
            if self.check_entry_point_rules(
                    unit_info.lang, unit_info.module_id, unit_info.unit_path, scope.stmt_id, name, attrs
            ):
                self.entry_points.add(scope.stmt_id)
                continue

        self.export()


    def export(self):
        self.loader.save_entry_points(self.entry_points)
