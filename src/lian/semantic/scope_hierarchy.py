#!/usr/bin/env python3

import pprint
import re

from lian.semantic.resolver import Resolver
from lian.config.constants import (
    CLASS_DECL_OPERATION,
    NAMESPACE_DECL_OPERATION,
    IMPORT_OPERATION,
    METHOD_DECL_OPERATION,
    VARIABLE_DECL_OPERATION,
    PARAMETER_DECL_OPERATION,
    EXPORT_STMT_OPERATION,
    FOR_STMT_OPERATION,
    ExportNodeType,
    ScopeKind
)

from lian.semantic.semantic_structure import (
    BasicGraph,
    MethodInClass,
    Scope,
    ScopeSpace,
    TypeGraphEdge,
    UnitSymbolDeclSummary,
    SimpleWorkList,
    ExportNode,
    TypeNode,
    MultipleDirectedGraph,
    ImportStmtInfo
)
from lian.util import util
from lian.util.loader import Loader

class UnitScopeHierarchyAnalysis:
    def __init__(self, loader: Loader, unit_id, unit_gir):
        self.loader = loader
        self.unit_gir = unit_gir
        self.unit_id = unit_id
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
            scope_kind = ScopeKind.UNIT_SCOPE
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
                    scope_kind = ScopeKind.PACKAGE_STMT,
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
                    scope_kind = ScopeKind.IMPORT_STMT,
                    source = util.read_stmt_field(row.source),
                    name = util.read_stmt_field(row.name),
                    alias = util.read_stmt_field(row.alias)
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
                    scope_kind = ScopeKind.VARIABLE_DECL,
                    name = util.read_stmt_field(row.name),
                    attrs = util.read_stmt_field(row.alias)
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
                    scope_kind = ScopeKind.PARAMETER_DECL,
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
                    scope_kind = ScopeKind.EXPORT_STMT,
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
                    scope_kind = ScopeKind.METHOD_SCOPE,
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
                    scope_kind = ScopeKind.FOR_SCOPE
                )
                self.scope_space.add(for_stmt_scope)
                self.all_scope_ids.add(stmt_id)

            elif row.operation in CLASS_DECL_OPERATION:
                self.class_stmt_ids.add(stmt_id)
                scope_id = self.determine_scope(row.parent_stmt_id)
                class_decl_scope = Scope(
                    unit_id = self.unit_id,
                    stmt_id = stmt_id,
                    scope_id = scope_id,
                    parent_stmt_id= row.parent_stmt_id,
                    scope_kind = ScopeKind.CLASS_SCOPE,
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
                    scope_kind = ScopeKind.NAMESPACE_SCOPE,
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
                    scope_kind = ScopeKind.BLOCK_SCOPE,
                )
                self.scope_space.add(block_scope)
                self.all_scope_ids.add(stmt_id)

    def correct_scopes(self):
        for stmt_id in self.class_stmt_ids:
            stmt = self.access_by_stmt_id(stmt_id)
            if util.is_available(stmt.fields):
                fields_block = self.read_block(stmt.fields)
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
                    ScopeKind.IMPORT_STMT,
                    ScopeKind.VARIABLE_DECL,
                    ScopeKind.PARAMETER_DECL,
                    ScopeKind.CLASS_SCOPE,
                    ScopeKind.METHOD_SCOPE,
                    ScopeKind.NAMESPACE_SCOPE,
            ]:
                if row.name not in symbol_name_to_scope_ids:
                    symbol_name_to_scope_ids[row.name] = set()
                symbol_name_to_scope_ids[row.name].add(row.scope_id)

                if row.scope_id not in scope_id_to_symbol_info:
                    scope_id_to_symbol_info[row.scope_id] = {}
                scope_id_to_symbol_info[row.scope_id][row.name] = row.stmt_id

            if row.scope_kind in [
                    ScopeKind.CLASS_SCOPE,
                    ScopeKind.METHOD_SCOPE,
                    ScopeKind.BLOCK_SCOPE,
                    ScopeKind.NAMESPACE_SCOPE,
                    ScopeKind.FOR_SCOPE,
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

class ImportHierarchy:
    def __init__(self, loader, resolver):
        self.loader = loader
        self.resolver = resolver
        self.analyzed_imported_unit_ids = set()
        self.import_graph = BasicGraph()

    def append_export_node(self, export_result, unit_id, stmt):

        export_result.append(ExportNode(
            unit_id = unit_id,
            stmt_id = stmt.stmt_id,
            name = stmt.name,
            export_type = stmt.scope_kind,
            source_module_id = unit_id,
            source_symbol_id= stmt.stmt_id
        ))
        return export_result

    def analyze_import_stmt(self, unit_id, stmt_id, stmt):
        def import_module_sync(result, module_id):
            self.analyze_unit_imports(module_id)
            self.import_graph.add_edge(unit_id, module_id, stmt_id)
            export_symbols = self.loader.load_unit_export_symbols(module_id)
            if not export_symbols: # TODO 2024.11.11 怀疑有import的循环依赖，分析1的过程中，又要load1的import
                return
            for each_symbol in export_symbols:
                # print("imported symbol: ", each_symbol)
                if each_symbol.name not in visited:
                    visited.add(each_symbol.name)
                    result.append(ExportNode(
                        unit_id = unit_id,
                        stmt_id = each_symbol.stmt_id,
                        name = each_symbol.name,
                        export_type = each_symbol.export_type,
                        source_module_id = each_symbol.source_module_id,
                        source_symbol_id = each_symbol.source_symbol_id
                    ))

        def may_append_unknown_node(result):
            if len(result) == 0:
                result.append(ExportNode(
                    unit_id = unit_id,
                    stmt_id = stmt_id,
                    name = target_name,
                    export_type = ExportNodeType.UNKNOWN_IMPORT,
                ))

        def append_import_module_node(result, module_id):
            if not self.loader.is_module_id(module_id):
                return

            # determine its module type
            module_type = ExportNodeType.MODULE_DIR
            if self.loader.is_unit_id(module_id):
                module_type = ExportNodeType.MODULE_UNIT

            # save node
            if target_name not in visited:
                visited.add(target_name)
                result.append(ExportNode(
                    unit_id = unit_id,
                    stmt_id = stmt_id,
                    name = target_name,
                    export_type = module_type,
                    source_module_id = module_id
                ))

        # resolve the import stmt
        # return the list of import nodes (unit_id, stmt_id, name, source_unit_id, source_stmt_id)
        target_name = stmt.name
        if stmt.alias:
            target_name = stmt.alias

        result = []
        visited = set()

        source = None
        if hasattr(stmt, 'source'):
            source = stmt.source
        elif hasattr(stmt, 'name'):
            source = stmt.name
        elif hasattr(stmt, 'module_path'):
            source = stmt.module_path
        # format: < import name as alias >
        print(stmt.name)
        print(9999999999999999999999999)
        print(source)

        if source == ""or source == ".":
            module_ids_result = self.loader.parse_import_module_path(stmt.name)
            for module_id in module_ids_result:
                if self.loader.is_module_dir_id(module_id) or self.loader.is_unit_id(module_id):
                    append_import_module_node(result, module_id)
                    self.import_graph.add_edge(unit_id, module_id, stmt_id)
                else:
                    import_module_sync(result, module_id)
            may_append_unknown_node(result)
            return result

        # format < from source import name as alias >
        source_module_ids, name_module_ids = self.loader.parse_import_module_path_with_extra_name(source, stmt.name)

        if len(source_module_ids) == 0:
            may_append_unknown_node(result)
            return result

        if stmt.name != "*":
            for source_id in source_module_ids:
                if self.loader.is_module_dir_id(source_id):
                    for name_id in name_module_ids:
                        append_import_module_node(result, name_id)
                        self.import_graph.add_edge(unit_id, name_id, stmt_id)
                else:
                    self.analyze_unit_imports(source_id)
                    # print("import_module_sync: ", source_id)
                    self.import_graph.add_edge(unit_id, source_id, stmt_id)
                    imported_symbols = self.loader.load_unit_export_symbols(source_id)
                    if imported_symbols:
                        for each_symbol in imported_symbols:
                            if each_symbol.name == stmt.name and each_symbol.name not in visited:
                                visited.add(each_symbol.name)
                                result.append(ExportNode(
                                    unit_id = unit_id,
                                    stmt_id = each_symbol.stmt_id,
                                    name = each_symbol.name,
                                    export_type = each_symbol.export_type,
                                    source_module_id = each_symbol.source_module_id,
                                    source_symbol_id = each_symbol.source_symbol_id
                                ))
        else:
            # format < from source import * >
            for source_id in source_module_ids:
                if self.loader.is_module_dir_id(source_id):
                    for name_id in name_module_ids:
                        append_import_module_node(result, name_id)
                        self.analyze_unit_imports(name_id)
                else:
                    self.analyze_unit_imports(source_id)
                    self.import_graph.add_edge(unit_id, source_id, stmt_id)
                    imported_symbols = self.loader.load_unit_export_symbols(source_id)
                    if imported_symbols:
                        for each_symbol in imported_symbols:
                            if each_symbol.name not in visited:
                                visited.add(each_symbol.name)
                                result.append(ExportNode(
                                    unit_id = unit_id,
                                    stmt_id = each_symbol.stmt_id,
                                    name = each_symbol.name,
                                    export_type = each_symbol.export_type,
                                    source_module_id = each_symbol.source_module_id,
                                    source_symbol_id = each_symbol.source_symbol_id
                                ))

        may_append_unknown_node(result)
        return result

    def analyze_unit_imports(self, unit_id):
        if unit_id in self.analyzed_imported_unit_ids:
            return

        # set flag to true and avoiding recursive analysis
        self.analyzed_imported_unit_ids.add(unit_id)
        #self.import_graph.add_node(unit_id)

        # start analysis from scope_hierarchy
        scope_hierarchy = self.loader.load_unit_scope_hierarchy(unit_id)
        gir = self.loader.load_unit_gir(unit_id)
        if not scope_hierarchy or not gir:
            return

        # obtain the global import stmts
        import_stmts = scope_hierarchy.query(
            (scope_hierarchy.scope_id == 0) &
            (scope_hierarchy.scope_kind == ScopeKind.IMPORT_STMT)
        )

        export_stmts = gir.query(gir.operation == "export_stmt")
        export_from_stmts = gir.query(gir.operation == "from_export_stmt")

        internal_symbols = scope_hierarchy.query(
            scope_hierarchy.scope_kind.isin(
                (ScopeKind.VARIABLE_DECL, ScopeKind.CLASS_SCOPE, ScopeKind.METHOD_SCOPE)
            )
        )

        # analyze each import stmt
        result = []
        for each_stmt in import_stmts:
            stmt_result = self.analyze_import_stmt(unit_id, each_stmt.stmt_id, each_stmt)
            result.extend(stmt_result)
        export_result = []
        if not export_stmts and not export_from_stmts:
            for each_symbol in internal_symbols:
                export_result = self.append_export_node(export_result, unit_id, each_symbol)
            result.extend(export_result)
        else:
            for each_stmt in export_stmts:
                symbols = internal_symbols.query(internal_symbols.name == each_stmt.name)
                for each_symbol in symbols:
                    export_result = self.append_export_node(export_result, unit_id, each_symbol)
            result.extend(export_result)
            for each_stmt in export_from_stmts:
                stmt_result = self.analyze_import_stmt(unit_id, each_stmt.stmt_id, each_stmt)
                result.extend(stmt_result)

        self.loader.save_unit_export_symbols(unit_id, result)

    def analyze(self, unit_id_list):
        for unit_id in unit_id_list:
            self.analyze_unit_imports(unit_id)
        self.loader.save_import_graph(self.import_graph)

class ImportGraphTranslatorToUnitLevel:
    def __init__(self, loader, import_graph, unit_id_list):
        self.loader = loader
        self.import_graph = import_graph
        self.unit_id_list = unit_id_list

    def convert(self):
        unit_import_graph = MultipleDirectedGraph()
        for unit_id in self.unit_id_list:
            unit_import_graph.add_node(unit_id)

        import_stmt_id_to_data = {}
        graph = self.import_graph.retrieve_graph()
        for node_id in graph.nodes:
            out_edges = graph[node_id]
            if not out_edges:
                continue

            for out_id in out_edges:
                stmt_id = out_edges[out_id]["weight"]
                import_data = ImportStmtInfo()
                import_data.stmt_id = stmt_id

                if self.loader.is_unit_id(out_id):
                    import_data.imported_unit_id = out_id
                    import_data.is_parsed = True
                    import_data.is_unit = True

                    unit_import_graph.add_edge(node_id, out_id, stmt_id)
                else:
                    unit_id = self.loader.convert_stmt_id_to_unit_id(out_id)
                    if unit_id > 0:
                        import_data.imported_unit_id = unit_id
                        import_data.imported_stmt_id = out_id
                        import_data.is_parsed = True

                if import_data.imported_unit_id > 0:
                    unit_import_graph.add_edge(node_id, import_data.imported_unit_id, stmt_id)
                import_stmt_id_to_data[stmt_id] = import_data

        return (unit_import_graph, import_stmt_id_to_data)

class TypeHierarchy:
    def __init__(self, loader, resolver):
        self.loader: Loader = loader
        self.resolver: Resolver = resolver
        self.type_graph = BasicGraph()
        self.analyzed_type_hierarchy_ids = set()
        self.analyzed_class_ids = set()
        self.class_to_methods = {}

    def parse_class_decl_stmt(self, unit_id, stmt_id, stmt):
        result = []
        if util.is_available(stmt.supers):
            supers = re.findall(r"'(.*?)'", stmt.supers)
            counter = 0
            for each_name in supers:
                ids = self.resolver.resolve_class_name_to_ids(unit_id, stmt_id, each_name)
                if ids:
                    for each_id in ids:
                        result.append(
                            TypeNode(
                                name = stmt.name,
                                unit_id= unit_id,
                                class_stmt_id = stmt_id,
                                parent_name = each_name,
                                parent_id = each_id,
                                parent_index = counter
                            )
                        )
                else :
                    result.append(
                        TypeNode(
                            name = stmt.name,
                            unit_id= unit_id,
                            class_stmt_id = stmt_id,
                            parent_id = -1,
                            parent_name = each_name,
                            parent_index = counter
                        )
                    )
                counter += 1
        else :
            result.append(
                TypeNode(
                    name = stmt.name,
                    unit_id= unit_id,
                    class_stmt_id = stmt_id,
                    parent_id = -1,
                    parent_name = "virtual_parent",
                    parent_index = 0
                    )
                )
        return result

    def analyze_class_decl_and_save_result(self, unit_id, stmt_id, stmt):
        if stmt_id in self.analyzed_type_hierarchy_ids:
            return
        self.analyzed_type_hierarchy_ids.add(stmt_id)

        result = self.parse_class_decl_stmt(unit_id, stmt_id, stmt)
        for type_node in result:
            self.type_graph.add_edge(
                stmt_id,
                type_node.parent_id,
                TypeGraphEdge(
                    name = type_node.name,
                    parent_name = type_node.parent_name,
                    parent_pos = type_node.parent_index
                )
            )

    def analyze_method_in_class(self, class_decl_stmt, scope_hierarchy):
        method_decls = scope_hierarchy.query(
            (scope_hierarchy.scope_id == class_decl_stmt.stmt_id) &
            (scope_hierarchy.scope_kind == ScopeKind.METHOD_SCOPE)
        )
        all_method_info = []
        for each_method in method_decls:
            all_method_info.append(MethodInClass(
                unit_id = each_method.unit_id,
                class_id = class_decl_stmt.stmt_id,
                name = each_method.name,
                stmt_id = each_method.stmt_id
            ))
        self.class_to_methods[class_decl_stmt.stmt_id] = all_method_info

    def analyze_type_hierarchy(self, unit_id):
        if unit_id in self.analyzed_type_hierarchy_ids:
            return
        self.analyzed_type_hierarchy_ids.add(unit_id)

        # start analysis from scope_hierarchy
        scope_hierarchy = self.loader.load_unit_scope_hierarchy(unit_id)
        if not scope_hierarchy:
            return

        # obtain class decls
        class_decl_stmts = scope_hierarchy.query(scope_hierarchy.scope_kind == ScopeKind.CLASS_SCOPE)

        for each_stmt in class_decl_stmts:
            # analyze each class decl
            self.analyze_class_decl_and_save_result(unit_id, each_stmt.stmt_id, each_stmt)

            # analyze method in class
            self.analyze_method_in_class(each_stmt, scope_hierarchy)

    def adjust_method_in_class_and_save(self, class_id):
        if class_id in self.analyzed_class_ids:
            return
        self.analyzed_class_ids.add(class_id)

        methods_in_class = []
        method_ids = set()

        if class_id in self.class_to_methods:
            methods_in_class = self.class_to_methods[class_id]
            for each_method in methods_in_class:
                method_ids.add(each_method.stmt_id)

        # adjust methods in class and save
        parent_ids = util.graph_successors(self.type_graph.graph, class_id)
        for each_parent_id in parent_ids:
            if each_parent_id == -1:
                continue
            self.adjust_method_in_class_and_save(each_parent_id)
            parent_methods = self.loader.load_methods_in_class(each_parent_id)
            for each_method in parent_methods:
                if each_method.stmt_id not in method_ids:
                    methods_in_class.append(
                        MethodInClass(
                            unit_id = each_method.unit_id,
                            class_id = class_id,
                            name = each_method.name,
                            stmt_id = each_method.stmt_id
                        )
                    )
                    method_ids.add(each_method.stmt_id)

        self.loader.save_methods_in_class(class_id, methods_in_class)

    def analyze(self, unit_id_list):
        for unit_id in unit_id_list:
            self.analyze_type_hierarchy(unit_id)

        # adjust methods in class and save
        for each_node in self.type_graph.graph.nodes():
            if self.loader.is_class_decl(each_node):
                self.adjust_method_in_class_and_save(each_node)

        # save type graph
        self.loader.save_type_graph(self.type_graph)

