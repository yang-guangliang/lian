#!/usr/bin/env python3

import os
import ast
import yaml
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
from lian.events.handler_template import EventData
from lian.semantic.semantic_structs import SimpleWorkList

@dataclasses.dataclass
class EntryPointRule:
    lang: str = ""
    unit_id: int = -1
    unit_path: str = ""
    unit_name: str = ""
    method_id: int = -1
    method_list: list[str] = dataclasses.field(default_factory=list)
    attrs: list[str] = dataclasses.field(default_factory=list)
    args: str = ""
    return_type: str = ""

class EntryPointGenerator:
    def __init__(self, options, event_manager, loader) -> None:
        self.options = options
        self.event_manager = event_manager
        self.loader:Loader = loader
        self.entry_points = set()
        self.entry_point_rules = []

        self._load_settings()

    def _parse_config_file(self, default_lang, file_path):
        # 判断是否可以打开
        if not os.path.isfile(file_path):
            util.error("Failed to parse entry point file: " + file_path)
            return

        data = None
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
            if data is None:
                util.error("Failed to parse entry point file: " + file_path)
                return

        for line in data:
            self.entry_point_rules.append(
                EntryPointRule(
                    **line
                )
            )

    def _load_settings(self):
        for root, dirs, files in os.walk(self.options.default_settings):
            for file_name in files:
                processing_flag, default_lang = util.check_file_processing_flag_and_extract_lang(file_name, config.ENTRY_POINTS_FILE)
                if not processing_flag:
                    continue

                self._parse_config_file(default_lang, os.path.join(root, file_name))

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

            if len(rule.method_list) > 0:
                if method_name not in rule.method_list:
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

    def export(self):
        self.loader.save_entry_points(self.entry_points)

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

