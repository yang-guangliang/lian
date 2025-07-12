#!/usr/bin/env python3

import pprint
import re
import networkx as nx

from lian.config import config
from lian.semantic.resolver import Resolver
from lian.config.constants import (
    CASE_AS_OPERATION,
    CLASS_DECL_OPERATION,
    NAMESPACE_DECL_OPERATION,
    IMPORT_OPERATION,
    METHOD_DECL_OPERATION,
    VARIABLE_DECL_OPERATION,
    PARAMETER_DECL_OPERATION,
    EXPORT_STMT_OPERATION,
    FOR_STMT_OPERATION,
    SymbolKind,
)

from lian.semantic.semantic_structs import (
    Scope,
    ScopeSpace,
    UnitSymbolDeclSummary,
    SimpleWorkList,
)
from lian.util import util
from lian.util.loader import Loader

class UnitScopeHierarchyAnalysis:
    def __init__(self, lian, loader, unit_id, unit_info, unit_gir):
        self.lian = lian
        self.options = lian.options
        self.loader:Loader = loader
        self.unit_gir = unit_gir
        self.unit_id = unit_id
        self.unit_info = unit_info
        self.stmt_id_to_gir = {}
        self.stmt_id_to_scope_id_cache = {}
        self.class_stmt_ids = set()
        self.namespace_stmt_ids = set()
        self.method_stmt_ids = set()
        self.for_stmt_ids = set()
        self.method_id_to_parameter_ids = {}
        self.class_id_to_class_name = {}
        self.method_id_to_method_name = {}
        self.variable_ids = set()
        self.import_stmt_ids = set()
        self.all_scope_ids = set()
        self.scope_space = ScopeSpace()
        self.symbol_decl_summary = UnitSymbolDeclSummary()
        self.symbol_name_to_scope_ids = {}
        self.scope_id_to_symbol_info = {}
        self.scope_id_to_available_scope_ids = {}
        self.class_id_to_class_field_ids = {}
        self.class_id_to_class_method_ids = {}

    def read_block(self, block_id):
        return self.unit_gir.read_block(block_id)

    def init(self):
        if util.is_empty(self.unit_gir):
            # util.error("UnitScopeHierarchyAnalysis.unit_gir is empty")
            return
        for row in self.unit_gir:
            if row.stmt_id in self.stmt_id_to_gir:
                continue
            self.stmt_id_to_gir[row.stmt_id] = row

    def analyze(self):
        self.init()
        self.discover_scopes()
        self.correct_scopes()
        self.summarize_symbol_decls()
        return self.save_necessary_info()

    def access_by_stmt_id(self, stmt_id):
        return self.stmt_id_to_gir.get(stmt_id)

    def determine_scope(self, stmt_id):
        if stmt_id == 0:
            return 0

        if stmt_id in self.stmt_id_to_scope_id_cache:
            return self.stmt_id_to_scope_id_cache[stmt_id]

        stmt = self.access_by_stmt_id(stmt_id)
        if util.is_empty(stmt):
            return 0

        result = stmt.stmt_id
        if stmt.stmt_id not in self.all_scope_ids:
            result = self.determine_scope(stmt.parent_stmt_id)

        self.stmt_id_to_scope_id_cache[stmt_id] = result
        return result

    def discover_scopes(self):
        root_scope = Scope(
            unit_id = self.unit_id,
            stmt_id = 0,
            scope_id = -1,
            parent_stmt_id = -1,
            scope_kind = SymbolKind.UNIT_KIND
        )
        root_scope_id = 0
        self.scope_space.add(root_scope)
        self.all_scope_ids.add(root_scope_id)

        for stmt_id in sorted(self.stmt_id_to_gir.keys()):
            row = self.stmt_id_to_gir[stmt_id]
            if row.operation == "package_stmt":
                scope_id = self.determine_scope(row.parent_stmt_id)
                package_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.PACKAGE_STMT,
                    name = util.read_stmt_field(row.name)
                )
                self.scope_space.add(package_scope)

            elif row.operation in IMPORT_OPERATION:
                scope_id = self.determine_scope(row.parent_stmt_id)
                import_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.IMPORT_STMT,
                    source = util.read_stmt_field(row.source),
                    name = util.read_stmt_field(row.name),
                    alias = util.read_stmt_field(row.alias),
                    attrs = util.read_stmt_field(row.attrs, "public")
                )
                self.scope_space.add(import_scope)
                self.import_stmt_ids.add(stmt_id)

            elif row.operation in VARIABLE_DECL_OPERATION:
                scope_id = self.determine_scope(row.parent_stmt_id)
                variable_decl_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id = row.parent_stmt_id,
                    scope_kind = SymbolKind.VARIABLE_DECL,
                    name = util.read_stmt_field(row.name),
                    attrs = util.read_stmt_field(row.alias)
                )
                self.scope_space.add(variable_decl_scope)
                self.variable_ids.add(stmt_id)

            elif row.operation in CASE_AS_OPERATION:
                if util.is_available(row.name):
                    scope_id = row.body
                    variable_decl_scope = Scope(
                        unit_id = self.unit_id,
                        stmt_id = stmt_id,
                        scope_id = scope_id,
                        parent_stmt_id = row.stmt_id,
                        scope_kind = SymbolKind.VARIABLE_DECL,
                        name = util.read_stmt_field(row.name)
                    )
                    self.scope_space.add(variable_decl_scope)
                    self.variable_ids.add(stmt_id)

            elif row.operation in PARAMETER_DECL_OPERATION:
                scope_id = self.determine_scope(row.parent_stmt_id)
                parameter_decl_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.PARAMETER_DECL,
                    name = util.read_stmt_field(row.name),
                    attrs = util.read_stmt_field(row.attrs)
                )
                self.scope_space.add(parameter_decl_scope)
                # self.variable_ids.add(stmt_id)

            elif row.operation in EXPORT_STMT_OPERATION:
                scope_id = self.determine_scope(row.parent_stmt_id)
                export_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.EXPORT_STMT,
                    source = util.read_stmt_field(row.source),
                    name = util.read_stmt_field(row.name),
                    alias = util.read_stmt_field(row.alias)
                )
                self.scope_space.add(export_scope)

            elif row.operation in METHOD_DECL_OPERATION:
                self.method_stmt_ids.add(stmt_id)
                scope_id = self.determine_scope(row.parent_stmt_id)
                method_decl_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.METHOD_KIND,
                    name = util.read_stmt_field(row.name),
                    attrs = util.read_stmt_field(row.attrs)
                )
                self.scope_space.add(method_decl_scope)
                self.all_scope_ids.add(stmt_id)
                self.method_id_to_method_name[stmt_id] = util.read_stmt_field(row.name)

            elif row.operation in FOR_STMT_OPERATION:
                self.for_stmt_ids.add(stmt_id)
                scope_id = self.determine_scope(row.parent_stmt_id)
                for_stmt_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.FOR_KIND
                )
                self.scope_space.add(for_stmt_scope)
                self.all_scope_ids.add(stmt_id)

            elif row.operation in CLASS_DECL_OPERATION:
                self.class_stmt_ids.add(stmt_id)
                scope_id = self.determine_scope(row.parent_stmt_id)
                #print("scope_id:", scope_id, "row", row)
                class_decl_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.CLASS_KIND,
                    name = util.read_stmt_field(row.name),
                    attrs = util.read_stmt_field(row.attrs),
                    supers = util.read_stmt_field(row.supers)
                )
                self.scope_space.add(class_decl_scope)
                self.all_scope_ids.add(stmt_id)
                self.class_id_to_class_name[stmt_id] = util.read_stmt_field(row.name)

            elif row.operation in NAMESPACE_DECL_OPERATION:
                self.namespace_stmt_ids.add(stmt_id)
                scope_id = self.determine_scope(row.parent_stmt_id)
                namespace_decl_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.NAMESPACE_KIND,
                    name = util.read_stmt_field(row.name),
                )
                self.scope_space.add(namespace_decl_scope)
                self.all_scope_ids.add(stmt_id)

            elif row.operation == "block_start":
                scope_id = self.determine_scope(row.parent_stmt_id)
                block_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = SymbolKind.BLOCK_KIND,
                )
                self.scope_space.add(block_scope)
                self.all_scope_ids.add(stmt_id)

    def correct_scopes(self):
        for stmt_id in self.class_stmt_ids:
            stmt = self.access_by_stmt_id(stmt_id)
            if util.is_available(stmt.fields):
                #print(stmt)
                fields_block = self.read_block(stmt.fields)
                #print(fields_block)
                variable_decl_stmts = fields_block.query(fields_block.operation == "variable_decl")
                for variable_decl in variable_decl_stmts:
                    item = self.scope_space.find_first_by_id(variable_decl.stmt_id)
                    item.scope_id = stmt_id

                    util.add_to_dict_with_default_set(
                        self.class_id_to_class_field_ids, stmt_id, variable_decl.stmt_id
                    )

            if util.is_available(stmt.methods):
                methods_block = self.read_block(stmt.methods)
                method_decl_stmts = methods_block.query(methods_block.operation == "method_decl")
                for method_decl in method_decl_stmts:
                    item = self.scope_space.find_first_by_id(method_decl.stmt_id)
                    item.scope_id = stmt_id

                    util.add_to_dict_with_default_set(
                        self.class_id_to_class_method_ids, stmt_id, method_decl.stmt_id
                    )

        for stmt_id in self.method_stmt_ids:
            parameter_ids = set()
            stmt = self.access_by_stmt_id(stmt_id)
            method_parameters = stmt.parameters
            if util.is_available(method_parameters):
                method_parameters_block = self.read_block(method_parameters)
                parameter_decl_stmts = method_parameters_block.query(
                    method_parameters_block.operation == "parameter_decl"
                )
                for parameter_decl in parameter_decl_stmts:
                    parameter_ids.add(parameter_decl.stmt_id)
                    item = self.scope_space.find_first_by_id(parameter_decl.stmt_id)
                    item.scope_id = stmt_id

            self.method_id_to_parameter_ids[stmt_id] = parameter_ids

        for stmt_id in self.for_stmt_ids:
            stmt = self.access_by_stmt_id(stmt_id)
            init_body = stmt.init_body
            if util.is_available(init_body):
                init_body_block = self.read_block(init_body)
                variable_decl_stmts = init_body_block.query(
                    init_body_block.operation == "variable_decl"
                )
                for variable_decl in variable_decl_stmts:
                    item = self.scope_space.find_first_by_id(variable_decl.stmt_id)
                    item.scope_id = stmt_id

    def summarize_symbol_decls(self):
        symbol_name_to_scope_ids = {}
        scope_id_to_symbol_info = {}
        scope_id_to_available_scope_ids = {}
        for row in self.scope_space:
            if row.scope_kind in [
                    SymbolKind.IMPORT_STMT,
                    SymbolKind.VARIABLE_DECL,
                    SymbolKind.PARAMETER_DECL,
                    SymbolKind.CLASS_KIND,
                    SymbolKind.METHOD_KIND,
                    SymbolKind.NAMESPACE_KIND,
            ]:
                if row.name not in symbol_name_to_scope_ids:
                    symbol_name_to_scope_ids[row.name] = set()
                symbol_name_to_scope_ids[row.name].add(row.scope_id)

                if util.is_available(row.name):
                    if self.options.strict_parse_mode:
                        if row.scope_id in scope_id_to_symbol_info:
                            if row.name in scope_id_to_symbol_info[row.scope_id]:
                                previous_decl_id = scope_id_to_symbol_info[row.scope_id][row.name]
                                previous_stmt = self.stmt_id_to_gir.get(previous_decl_id)
                                util.error_and_quit_with_stmt_info(
                                    self.unit_info.original_path,
                                    previous_stmt,
                                    f"{row.name} already declared in {self.unit_info.original_path}:{previous_stmt.start_row}"
                                )

                    if row.scope_id not in scope_id_to_symbol_info:
                        scope_id_to_symbol_info[row.scope_id] = {}
                    scope_id_to_symbol_info[row.scope_id][row.name] = row.stmt_id

            if row.scope_kind in [
                    SymbolKind.CLASS_KIND,
                    SymbolKind.METHOD_KIND,
                    SymbolKind.BLOCK_KIND,
                    SymbolKind.NAMESPACE_KIND,
                    SymbolKind.FOR_KIND,
            ]:
                if row.stmt_id not in scope_id_to_available_scope_ids:
                    scope_id_to_available_scope_ids[row.stmt_id] = set()
                scope_id_to_available_scope_ids[row.stmt_id].add(row.scope_id)

        visited_set = set()
        for scope_id in scope_id_to_available_scope_ids:
            wl = SimpleWorkList().add(scope_id_to_available_scope_ids[scope_id])
            while len(wl) != 0:
                tmp_id = wl.pop()
                if tmp_id <= 0:
                    continue
                if tmp_id in scope_id_to_available_scope_ids:
                    scope_id_to_available_scope_ids[scope_id] |= scope_id_to_available_scope_ids[tmp_id]

                    for _id in scope_id_to_available_scope_ids[tmp_id]:
                        if _id not in visited_set:
                            wl.add(_id)

            visited_set.add(scope_id)

        for scope_id in scope_id_to_available_scope_ids:
            scope_id_to_available_scope_ids[scope_id].add(scope_id)

        self.loader.save_unit_symbol_decl_summary(
            self.unit_id,
            UnitSymbolDeclSummary(
                self.unit_id, symbol_name_to_scope_ids, scope_id_to_symbol_info, scope_id_to_available_scope_ids
            )
        )

    def save_necessary_info(self):
        self.loader.save_unit_id_to_stmt_ids(self.unit_id, self.stmt_id_to_gir.keys())
        self.loader.save_unit_id_to_method_ids(self.unit_id, self.method_stmt_ids)
        self.loader.save_unit_id_to_class_ids(self.unit_id, self.class_stmt_ids)
        self.loader.save_unit_id_to_namespace_ids(self.unit_id, self.namespace_stmt_ids)
        self.loader.save_unit_id_to_variable_ids(self.unit_id, self.variable_ids)
        self.loader.save_unit_id_to_import_stmt_ids(self.unit_id, self.import_stmt_ids)

        for stmt_id in self.method_id_to_method_name:
            self.loader.save_method_id_to_method_name(stmt_id, self.method_id_to_method_name[stmt_id])
        for stmt_id in self.class_id_to_class_name:
            self.loader.save_class_id_to_class_name(stmt_id, self.class_id_to_class_name[stmt_id])
        for stmt_id in self.method_id_to_parameter_ids:
            self.loader.save_method_id_to_parameter_ids(stmt_id, self.method_id_to_parameter_ids[stmt_id])
        for stmt_id in self.class_id_to_class_field_ids:
            self.loader.save_class_id_to_field_ids(stmt_id, self.class_id_to_class_field_ids[stmt_id])
        for stmt_id in self.class_id_to_class_method_ids:
            self.loader.save_class_id_to_method_ids(stmt_id, self.class_id_to_class_method_ids[stmt_id])

        return self.loader.save_unit_scope_hierarchy(self.unit_id, self.scope_space)

    def display_results(self):
        pprint.pprint(self.scope_space.to_dict())
