#!/usr/bin/env python3
import pprint
import sys
import traceback
from tqdm import tqdm
from lian.incremental.unit_level_checker import UnitLevelChecker
from lian.util import util
from lian.config import config
import lian.util.data_model as dm
from lian.config.constants import (
    ExportNodeType,
    SymbolDependencyKind,
    ScopeKind,
    SymbolKind,
    EventKind,
    CalleeType,
    BasicCallGraphNodeKind
)
from lian.semantic.semantic_structure import (
    Symbol,
    State,
    ComputeFrame,
    ComputeFrameStack,
    SimpleWorkList,
    CallGraph,
    BasicCallGraph,
    BasicGraph,
    MethodDefUseSummary,
    MethodSummaryTemplate,
    MethodSummaryInstance,
    SimplyGroupedMethodTypes,
    ExportNode,
)
from lian.util.loader import Loader
from lian.semantic.resolver import Resolver
from lian.semantic.scope_hierarchy import (
    UnitScopeHierarchyAnalysis,
    ImportHierarchy,
    TypeHierarchy
)
from lian.semantic.entry_points import EntryPointGenerator
from lian.semantic.control_flow import ControlFlowAnalysis
from lian.semantic.stmt_def_use_analysis import StmtDefUseAnalysis
from lian.incremental import unit_level_checker

class BasicSemanticAnalysis:
    def __init__(self, options, app_manager, loader, resolver, incremental_checker, extern_system):
        self.analysis_phases = []
        self.options = options
        self.app_manager = app_manager
        self.extern_system = extern_system
        self.loader:Loader = loader
        self.resolver: Resolver = resolver
        self.incremental_checker: UnitLevelChecker = incremental_checker
        self.entry_points = EntryPointGenerator(options, app_manager, loader)
        self.basic_call_graph = BasicCallGraph()
        self.analyzed_method_ids = set()

    def analyze_stmt_def_use(self, method_id, import_result, incremental_flag = False):
        frame = ComputeFrame(method_id = method_id, loader = self.loader)
        method_decl_stmt, parameter_decls, method_body = self.loader.load_method_gir(method_id)
        frame.method_decl_stmt = method_decl_stmt
        cfg = None
        if incremental_flag:
            # util.debug("cfg incremental")
            cfg = self.incremental_checker.fetch_cfg(method_id)
            self.loader.save_method_cfg(method_id, cfg)
        else:
            cfg = ControlFlowAnalysis(self.loader, method_id, parameter_decls, method_body).analyze()
        all_cfg_nodes = set(cfg.nodes())

        if util.is_available(parameter_decls):
            for row in parameter_decls:
                frame.stmt_id_to_stmt[row.stmt_id] = row
        if util.is_available(method_body):
            for row in method_body:
                frame.stmt_id_to_stmt[row.stmt_id] = row

        # Perform def-use analysis; This is flow-insensitive
        frame.stmt_def_use_analysis = StmtDefUseAnalysis(
            self.loader,
            self.resolver,
            self.basic_call_graph,
            compute_frame = frame,
            import_result=import_result,
        )

        for stmt_id in frame.stmt_id_to_stmt:
            if stmt_id in all_cfg_nodes:
                frame.stmt_def_use_analysis.analyze_stmt(stmt_id, frame.stmt_id_to_stmt[stmt_id])

        # print("frame.method_def_use_summary", frame.method_def_use_summary)
        self.loader.save_stmt_status_p1(method_id, frame.stmt_id_to_status)
        self.loader.save_symbol_state_space_p1(method_id, frame.symbol_state_space)
        self.loader.save_method_symbol_to_define(method_id, frame.symbol_to_define)
        self.loader.save_method_symbol_to_use(method_id, frame.symbol_to_use)
        self.loader.save_method_state_to_define_p1(frame.method_id, frame.state_to_define)
        self.loader.save_method_internal_callees(method_id, frame.basic_callees)
        self.loader.save_method_def_use_summary(method_id, frame.method_def_use_summary)

    def search_impacted_parent_nodes(self, graph, node):
        if node not in graph:
            return set()

        results = set()
        worklist = SimpleWorkList(node)
        while len(worklist) != 0:
            node = worklist.pop()
            if node in results:
                continue
            results.add(node)
            for tmp_node in util.graph_predecessors(graph, node):
                if tmp_node not in results:
                    worklist.add(tmp_node)
        return results

    def group_methods_by_callee_types(self):
        graph = self.basic_call_graph.graph

        containing_dynamic_callees = self.search_impacted_parent_nodes(graph, BasicCallGraphNodeKind.DYNAMIC_METHOD)
        containing_error_callees = self.search_impacted_parent_nodes(graph, BasicCallGraphNodeKind.ERROR_METHOD)

        # print(containing_dynamic_callees)
        # print(containing_error_callees)
        leaf_nodes = util.find_graph_nodes_with_zero_out_degree(graph)

        only_direct_callees = set()
        mixed_direct_callees = set()
        dynamic_error_set = containing_error_callees | containing_dynamic_callees
        for method_id in dynamic_error_set:
            flag = False
            for child_id in util.graph_successors(graph, method_id):
                if child_id not in dynamic_error_set:
                    only_direct_callees.add(child_id)
                    flag = True
            if flag:
                mixed_direct_callees.add(method_id)

        only_dynamic_callees = containing_dynamic_callees - mixed_direct_callees
        only_direct_callees -= leaf_nodes
        has_calls = only_direct_callees | mixed_direct_callees | only_dynamic_callees | containing_error_callees | containing_dynamic_callees
        no_callees = self.loader.load_all_method_ids() - has_calls

        extra = {BasicCallGraphNodeKind.DYNAMIC_METHOD, BasicCallGraphNodeKind.ERROR_METHOD}
        types = SimplyGroupedMethodTypes(
            no_callees - extra,
            only_direct_callees - extra,
            mixed_direct_callees - extra,
            only_dynamic_callees - extra,
            containing_dynamic_callees - extra,
            containing_error_callees - extra
        )
        # if self.options.debug:
        #     util.debug(f"Grouped methods:\n{types}")
        self.loader.save_grouped_methods(types)
        return types

    @profile
    def run(self):
        unit_list = []
        # Analyze each unit's scope hierarchy and entry points
        for unit_info in self.loader.load_all_unit_info():
            unit_id = unit_info.module_id
            unit_list.append(unit_id)
            unit_gir = self.loader.load_unit_gir(unit_id)

            unit_scope = None
            incremental_flag = False
            if self.options.incremental:
                if self.options.debug:
                    util.debug("Scope incremental:")
                previous_scope_analysis_pack = self.incremental_checker.previous_scope_hierarchy_analysis_results(unit_info)
                if previous_scope_analysis_pack:
                    incremental_flag = True
                    unit_scope = UnitScopeHierarchyAnalysis(self.loader, unit_id, unit_gir).reuse_analysis(previous_scope_analysis_pack)

            if not incremental_flag:
                unit_scope = UnitScopeHierarchyAnalysis(self.loader, unit_id, unit_gir).analyze()
            self.entry_points.collect_entry_points_from_unit_scope(unit_info, unit_scope)
            self.extern_system.install_mock_code_file(unit_info, unit_scope)
        self.loader.export_scope_hierarchy()
        self.loader.export_entry_points()

        self.extern_system.display_all_installed_rules()

        # Given an import stmt, how to construct export nodes of each unit and unit hierarchy
        importAnalysis = ImportHierarchy(self.loader, self.resolver)
        importAnalysis.analyze(unit_list)
        # Given a class decl stmt and its supers' names, how to resolve them with its id?
        print("=== Analyzing Type Hierarchy ===")
        TypeHierarchy(self.loader, self.resolver).analyze(unit_list)

        # Conduct basic analysis, i.e., context-insensitive and flow-insensitive analysis
        # reversed() is to improve cache hit rates
        print("=== Analyzing def_use ===")
        unit_list.reverse()
        for unit_id in tqdm(unit_list):
            incremental_flag = (self.incremental_checker.check_unit_id_analyzed(unit_id) is not None)
            all_unit_methods = self.loader.convert_unit_id_to_method_ids(unit_id)
            for method_id in all_unit_methods:
                self.analyze_stmt_def_use(method_id, importAnalysis, incremental_flag)
        self.loader.save_call_graph_p1(self.basic_call_graph)

        self.group_methods_by_callee_types()
        self.loader.export()

        return self
