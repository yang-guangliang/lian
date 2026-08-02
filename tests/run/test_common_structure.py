#!/usr/bin/env python3

from ctypes import c_void_p, cdll
import os,sys
import subprocess
import tempfile
import unittest
from collections import deque
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
import networkx as nx
import tree_sitter
from pyarrow.lib import ArrowInvalid

import tests.run.init_test as init_test

from lian.config import lang_config
from lian.config.constants import ANALYSIS_PHASE_ID
from lian import common_structs as common_structure
from lian.core.global_semantics import P3GlobalSemanticAnalysis
from lian.core.resolver import Resolver
from lian.core.stmt_states import StmtStates
from lian.lang import c_parser
from lian.taint.taint_analysis import TaintAnalysis


class TestSimpleWorkList(unittest.TestCase):
    def test_fifo_uses_constant_time_queue_without_changing_order(self):
        worklist = common_structure.SimpleWorkList([3, 1, 2, 1])

        self.assertIsInstance(worklist.work_list, deque)
        self.assertEqual([worklist.pop(), worklist.pop(), worklist.pop()], [3, 1, 2])

    def test_fifo_insert_to_first_preserves_priority(self):
        worklist = common_structure.SimpleWorkList([2, 3])

        worklist.insert_to_first(1)

        self.assertEqual([worklist.pop(), worklist.pop(), worklist.pop()], [1, 2, 3])


class TestStateFlowGraphStateIndex(unittest.TestCase):
    def test_tracks_state_nodes_from_both_edge_ends(self):
        graph = common_structure.StateFlowGraph(method_id=1)
        source_state = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.STATE, index=10, node_id=1
        )
        target_state = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.STATE, index=20, node_id=2
        )

        graph.add_edge(source_state, target_state)

        self.assertEqual(graph.state_index_to_nodes[10], {source_state})
        self.assertEqual(graph.state_index_to_nodes[20], {target_state})

    def test_keeps_all_distinct_state_nodes_for_an_index_without_duplicates(self):
        graph = common_structure.StateFlowGraph(method_id=1)
        first_state = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.STATE, index=10, node_id=1
        )
        second_state = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.STATE, index=10, node_id=2
        )
        target_symbol = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.SYMBOL, index=30, node_id=3
        )

        graph.add_edge([first_state, second_state, first_state], target_symbol)

        self.assertEqual(graph.state_index_to_nodes[10], {first_state, second_state})
        self.assertNotIn(30, graph.state_index_to_nodes)


class TestStmtStateIndexValidation(unittest.TestCase):
    def test_missing_state_index_does_not_become_a_concrete_state(self):
        stmt_states = object.__new__(StmtStates)
        stmt_states.frame = SimpleNamespace(
            symbol_state_space=common_structure.SymbolStateSpace()
        )

        self.assertEqual(stmt_states.read_used_states(-1, {}), set())

    def test_concrete_state_index_remains_available(self):
        state_space = common_structure.SymbolStateSpace()
        state_index = state_space.add(common_structure.State(state_id=101))
        stmt_states = object.__new__(StmtStates)
        stmt_states.frame = SimpleNamespace(symbol_state_space=state_space)

        self.assertEqual(stmt_states.read_used_states(state_index, {}), {state_index})

    def test_field_merge_ignores_missing_index_without_dropping_valid_state(self):
        state_space = common_structure.SymbolStateSpace()
        valid_state_index = state_space.add(
            common_structure.State(state_id=101, tangping_flag=True)
        )
        stmt_states = object.__new__(StmtStates)
        stmt_states.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        stmt_states.frame = SimpleNamespace(symbol_state_space=state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=common_structure.StmtStatus(stmt_id=7),
            state_set_in_summary_field=set(),
            state_set_in_arg_field={-1, valid_state_index},
            source_symbol_id=11,
            access_path=[],
        )

        self.assertEqual(
            result,
            {valid_state_index},
            "an unresolved field sentinel must not discard concrete caller state",
        )

    def test_field_merge_handles_deep_nested_state_graph_without_python_recursion(self):
        depth = 600
        state_space = common_structure.SymbolStateSpace()
        summary_indexes = [
            state_space.add(common_structure.State(state_id=1000 + index))
            for index in range(depth)
        ]
        argument_indexes = [
            state_space.add(common_structure.State(state_id=2000 + index))
            for index in range(depth)
        ]
        for index in range(depth - 1):
            state_space[summary_indexes[index]].fields = {
                "next": {summary_indexes[index + 1]}
            }
            state_space[argument_indexes[index]].fields = {
                "next": {argument_indexes[index + 1]}
            }

        stmt_states = object.__new__(StmtStates)
        stmt_states.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        stmt_states.frame = SimpleNamespace(symbol_state_space=state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=common_structure.StmtStatus(stmt_id=7),
            state_set_in_summary_field={summary_indexes[0]},
            state_set_in_arg_field={argument_indexes[0]},
            source_symbol_id=11,
            access_path=[],
        )

        self.assertEqual(result, {argument_indexes[0]})

    def test_field_merge_preserves_self_referential_argument_field(self):
        state_space = common_structure.SymbolStateSpace()
        summary_index = state_space.add(common_structure.State(state_id=101))
        argument_index = state_space.add(common_structure.State(state_id=201))
        state_space[summary_index].fields = {"self": {summary_index}}
        state_space[argument_index].fields = {"self": {argument_index}}

        stmt_states = object.__new__(StmtStates)
        stmt_states.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        stmt_states.frame = SimpleNamespace(symbol_state_space=state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=common_structure.StmtStatus(stmt_id=7),
            state_set_in_summary_field={summary_index},
            state_set_in_arg_field={argument_index},
            source_symbol_id=11,
            access_path=[],
        )

        self.assertEqual(result, {argument_index})
        self.assertEqual(state_space[argument_index].fields["self"], {argument_index})

    def test_field_merge_preserves_nested_and_nonoverlapping_fields(self):
        state_space = common_structure.SymbolStateSpace()
        summary_root = state_space.add(common_structure.State(state_id=101))
        summary_child = state_space.add(common_structure.State(state_id=102))
        summary_leaf = state_space.add(common_structure.State(state_id=103))
        summary_only = state_space.add(common_structure.State(state_id=104))
        argument_root = state_space.add(common_structure.State(state_id=201))
        argument_child = state_space.add(common_structure.State(state_id=202))
        argument_leaf = state_space.add(common_structure.State(state_id=203))
        argument_only = state_space.add(common_structure.State(state_id=204))

        state_space[summary_root].fields = {
            "shared": {summary_child},
            "summary_only": {summary_only},
        }
        state_space[summary_child].fields = {"from_summary": {summary_leaf}}
        state_space[argument_root].fields = {
            "shared": {argument_child},
            "argument_only": {argument_only},
        }
        state_space[argument_child].fields = {"from_argument": {argument_leaf}}

        stmt_states = object.__new__(StmtStates)
        stmt_states.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        stmt_states.frame = SimpleNamespace(symbol_state_space=state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=common_structure.StmtStatus(stmt_id=7),
            state_set_in_summary_field={summary_root},
            state_set_in_arg_field={argument_root},
            source_symbol_id=11,
            access_path=[],
        )

        self.assertEqual(result, {argument_root})
        self.assertEqual(
            state_space[argument_root].fields,
            {
                "shared": {argument_child},
                "summary_only": {summary_only},
                "argument_only": {argument_only},
            },
        )
        self.assertEqual(
            state_space[argument_child].fields,
            {
                "from_argument": {argument_leaf},
                "from_summary": {summary_leaf},
            },
        )


class TestResolverStateGraphDepth(unittest.TestCase):
    def test_resolves_deep_state_graph_without_python_recursion(self):
        depth = 1100
        state_space = common_structure.SymbolStateSpace()
        old_indexes = [None] * depth
        for position in range(depth - 1, -1, -1):
            fields = (
                {} if position == depth - 1
                else {"next": {old_indexes[position + 1]}}
            )
            old_indexes[position] = state_space.add(
                common_structure.State(
                    stmt_id=1,
                    state_id=position + 1,
                    fields=fields,
                )
            )

        latest_indexes = [None] * depth
        for position in range(depth - 1, -1, -1):
            fields = (
                {} if position == depth - 1
                else {"next": {old_indexes[position + 1]}}
            )
            latest_indexes[position] = state_space.add(
                common_structure.State(
                    stmt_id=2,
                    state_id=position + 1,
                    fields=fields,
                )
            )

        definitions = {
            position + 1: {
                common_structure.StateDefNode(
                    index=latest_indexes[position],
                    state_id=position + 1,
                    stmt_id=2,
                )
            }
            for position in range(depth)
        }
        available_definitions = set().union(*definitions.values())
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states=definitions,
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )
        resolver = object.__new__(Resolver)

        resolved_indexes = resolver.retrieve_latest_states(
            frame,
            7,
            state_space,
            {old_indexes[0]},
            available_definitions,
            {},
        )

        resolved_index = next(iter(resolved_indexes))
        for expected_state_id in range(1, depth + 1):
            resolved_state = state_space[resolved_index]
            self.assertEqual(resolved_state.state_id, expected_state_id)
            if expected_state_id < depth:
                resolved_index = next(iter(resolved_state.fields["next"]))
        self.assertEqual(
            state_space[old_indexes[0]].fields,
            {"next": {old_indexes[1]}},
        )

    def test_resolves_latest_state_cycle_without_reusing_old_edges(self):
        state_space = common_structure.SymbolStateSpace()
        old_first = state_space.add(
            common_structure.State(stmt_id=1, state_id=10, fields={"next": {1}})
        )
        old_second = state_space.add(
            common_structure.State(stmt_id=1, state_id=20, fields={"previous": {0}})
        )
        latest_first = state_space.add(
            common_structure.State(
                stmt_id=2, state_id=10, fields={"next": {old_second}}
            )
        )
        latest_second = state_space.add(
            common_structure.State(
                stmt_id=2, state_id=20, fields={"previous": {old_first}}
            )
        )
        first_definition = common_structure.StateDefNode(
            index=latest_first, state_id=10, stmt_id=2
        )
        second_definition = common_structure.StateDefNode(
            index=latest_second, state_id=20, stmt_id=2
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={10: {first_definition}, 20: {second_definition}},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )
        resolver = object.__new__(Resolver)

        resolved_first = next(iter(resolver.retrieve_latest_states(
            frame,
            7,
            state_space,
            {old_first},
            {first_definition, second_definition},
            {},
        )))
        resolved_second = next(iter(state_space[resolved_first].fields["next"]))

        self.assertNotIn(resolved_first, {old_first, latest_first})
        self.assertNotIn(resolved_second, {old_second, latest_second})
        self.assertEqual(
            state_space[resolved_second].fields["previous"], {resolved_first}
        )
        self.assertEqual(state_space[old_first].fields, {"next": {old_second}})
        self.assertEqual(state_space[old_second].fields, {"previous": {old_first}})

    def test_resolves_field_array_and_tangping_children_consistently(self):
        state_space = common_structure.SymbolStateSpace()
        old_child = state_space.add(
            common_structure.State(stmt_id=1, state_id=20, value="old")
        )
        parent = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=10,
                fields={"child": {old_child}},
                array=[{old_child}],
                tangping_elements={old_child},
            )
        )
        latest_child = state_space.add(
            common_structure.State(stmt_id=2, state_id=20, value="latest")
        )
        child_definition = common_structure.StateDefNode(
            index=latest_child, state_id=20, stmt_id=2
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={20: {child_definition}},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )
        resolver = object.__new__(Resolver)

        resolved_parent_index = next(iter(resolver.retrieve_latest_states(
            frame,
            7,
            state_space,
            {parent},
            {child_definition},
            {},
        )))
        resolved_parent = state_space[resolved_parent_index]

        self.assertEqual(resolved_parent.fields, {"child": {latest_child}})
        self.assertEqual(resolved_parent.array, [{latest_child}])
        self.assertEqual(resolved_parent.tangping_elements, {latest_child})
        self.assertEqual(state_space[parent].fields, {"child": {old_child}})

    def test_reuses_one_resolved_child_across_shared_parent_edges(self):
        state_space = common_structure.SymbolStateSpace()
        old_child = state_space.add(
            common_structure.State(stmt_id=1, state_id=30, value="old")
        )
        first_parent = state_space.add(
            common_structure.State(
                stmt_id=1, state_id=10, fields={"child": {old_child}}
            )
        )
        second_parent = state_space.add(
            common_structure.State(
                stmt_id=1, state_id=20, fields={"child": {old_child}}
            )
        )
        latest_child = state_space.add(
            common_structure.State(stmt_id=2, state_id=30, value="latest")
        )
        child_definition = common_structure.StateDefNode(
            index=latest_child, state_id=30, stmt_id=2
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={30: {child_definition}},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )

        resolved_parents = Resolver.retrieve_latest_states(
            object.__new__(Resolver),
            frame,
            7,
            state_space,
            {first_parent, second_parent},
            {child_definition},
            {},
        )

        self.assertEqual(len(resolved_parents), 2)
        self.assertEqual(len(state_space), 6)
        for parent_index in resolved_parents:
            self.assertEqual(
                state_space[parent_index].fields, {"child": {latest_child}}
            )


class TestP3IndexSpaceShift(unittest.TestCase):
    def test_shifts_all_index_references_without_bit_vector_managers(self):
        status = common_structure.StmtStatus(
            stmt_id=7,
            defined_symbol=4,
            used_symbols=[1, -1],
            implicitly_defined_symbols=[3],
            implicitly_used_symbols=[2, -1],
            defined_states={5},
            in_state_bits={
                common_structure.StateDefNode(index=8, state_id=80, stmt_id=7)
            },
        )
        space = common_structure.SymbolStateSpace()
        space.add(common_structure.Symbol(states={0}))
        space.add(
            common_structure.State(
                fields={"field": {1}},
                array=[{2}],
                tangping_elements={3},
            )
        )
        defined_state = common_structure.StateDefNode(
            index=5, state_id=50, stmt_id=7
        )
        frame = SimpleNamespace(
            defined_states={50: {defined_state}},
            all_symbol_defs=set(),
            all_state_defs={defined_state},
        )
        summary = common_structure.MethodSummaryTemplate(
            parameter_symbols={1: {0}},
            external_symbol_to_state={3: 0},
            raw_to_new_index={0: 0},
            index_to_default_value={0: 77},
        )

        P3GlobalSemanticAnalysis.adjust_index_of_status_space(
            object.__new__(P3GlobalSemanticAnalysis),
            10,
            frame,
            {7: status},
            space,
            {},
            None,
            None,
            summary,
        )

        self.assertEqual(status.defined_symbol, 14)
        self.assertEqual(status.used_symbols, [11, -1])
        self.assertEqual(status.implicitly_used_symbols, [12, -1])
        self.assertEqual(status.implicitly_defined_symbols, [13])
        self.assertEqual(status.defined_states, {15})
        self.assertEqual(
            status.in_state_bits,
            {common_structure.StateDefNode(index=18, state_id=80, stmt_id=7)},
        )
        self.assertEqual(space[0].states, {10})
        self.assertEqual(space[1].fields, {"field": {11}})
        self.assertEqual(space[1].array, [{12}])
        self.assertEqual(space[1].tangping_elements, {13})
        self.assertEqual(summary.parameter_symbols, {1: {10}})
        self.assertEqual(summary.external_symbol_to_state, {3: 10})
        self.assertEqual(summary.raw_to_new_index, {10: 0})
        self.assertEqual(summary.index_to_default_value, {10: 77})
        self.assertEqual(
            frame.defined_states,
            {50: {common_structure.StateDefNode(index=15, state_id=50, stmt_id=7)}},
        )

    def test_rebuilds_bit_vector_lookup_after_shifting_nodes(self):
        symbol_node = common_structure.SymbolDefNode(
            index=1, symbol_id=10, stmt_id=7
        )
        state_node = common_structure.StateDefNode(
            index=2, state_id=20, stmt_id=7
        )
        symbol_bits = common_structure.BitVectorManager()
        state_bits = common_structure.BitVectorManager()
        symbol_bits.add_bit_id(symbol_node)
        state_bits.add_bit_id(state_node)

        P3GlobalSemanticAnalysis.adjust_index_of_status_space(
            object.__new__(P3GlobalSemanticAnalysis),
            10,
            SimpleNamespace(
                defined_states={}, all_symbol_defs=set(), all_state_defs=set()
            ),
            {},
            common_structure.SymbolStateSpace(),
            {},
            symbol_bits,
            state_bits,
            common_structure.MethodSummaryTemplate(),
        )

        shifted_symbol = common_structure.SymbolDefNode(
            index=11, symbol_id=10, stmt_id=7
        )
        shifted_state = common_structure.StateDefNode(
            index=12, state_id=20, stmt_id=7
        )
        self.assertEqual(symbol_bits.bit_pos_to_id, {1: shifted_symbol})
        self.assertEqual(state_bits.bit_pos_to_id, {1: shifted_state})
        self.assertEqual(symbol_bits.find_bit_pos_by_id(shifted_symbol), 1)
        self.assertEqual(state_bits.find_bit_pos_by_id(shifted_state), 1)


class TestMethodSummaryIndexMapping(unittest.TestCase):
    def test_composes_raw_indexes_without_remapping_overlapping_values(self):
        summary = common_structure.MethodSummaryInstance(
            key=common_structure.CallSite(1, 2, 3),
            parameter_symbols={1: {3}, 2: {0}},
            return_symbols={-1: {3}},
        )

        summary.adjust_ids({3: 0, 0: 1})

        self.assertEqual(summary.parameter_symbols, {1: {3}, 2: {0}})
        self.assertEqual(summary.return_symbols, {-1: {3}})
        self.assertEqual(summary.raw_to_new_index, {3: 0, 0: 1})
        self.assertEqual(
            set(summary.to_dict()["parameter_symbols"]),
            {(1, 3, 0), (2, 0, 1)},
        )

        summary.adjust_ids({0: 10, 1: 11})
        p3_states = object.__new__(StmtStates)
        p3_states.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        self.assertEqual(summary.raw_to_new_index, {3: 10, 0: 11})
        self.assertEqual(
            p3_states.adjust_indexes(
                common_structure.SymbolStateSpace(), summary, {-1, 3, 0}
            ),
            {10, 11},
        )

    def test_copy_preserves_index_metadata_without_aliasing_records(self):
        summary = common_structure.MethodSummaryInstance(
            key=common_structure.CallSite(1, 2, 3),
            parameter_symbols={10: {20}},
            external_symbol_to_state={30: 20},
            raw_to_new_index={40: 20},
            index_to_default_value={20: 50},
        )

        copied = summary.copy()

        self.assertEqual(copied.external_symbol_to_state, {30: 20})
        self.assertEqual(copied.raw_to_new_index, {40: 20})
        self.assertEqual(copied.index_to_default_value, {20: 50})
        copied.parameter_symbols[10].add(21)
        self.assertEqual(summary.parameter_symbols, {10: {20}})


class TestP3SummaryGeneration(unittest.TestCase):
    def test_includes_external_state_stored_at_index_zero(self):
        class IdentityResolver:
            def retrieve_latest_states(
                self, frame, stmt_id, symbol_state_space, state_indexes,
                available_defined_states, state_index_old_to_new,
            ):
                return state_indexes.copy()

        state_space = common_structure.SymbolStateSpace()
        state_space.add(
            common_structure.State(stmt_id=7, state_id=11, value="external")
        )
        cfg = nx.DiGraph()
        cfg.add_node(7)
        frame = SimpleNamespace(
            method_def_use_summary=common_structure.MethodDefUseSummary(
                method_id=1, defined_external_symbol_ids={99}
            ),
            symbol_state_space=state_space,
            cfg=cfg,
            unit_gir=SimpleNamespace(
                get_stmt_by_id=lambda stmt_id: SimpleNamespace(
                    operation="return_stmt"
                )
            ),
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
            symbol_bit_vector_manager=SimpleNamespace(explain=lambda bits: set()),
            state_bit_vector_manager=SimpleNamespace(explain=lambda bits: set()),
            external_symbol_id_to_initial_state_index={99: 0},
        )
        analysis = object.__new__(P3GlobalSemanticAnalysis)
        analysis.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        analysis.resolver = IdentityResolver()

        summary = analysis.generate_and_save_analysis_summary(
            frame, common_structure.MethodSummaryTemplate(key=1)
        )

        self.assertEqual(summary.defined_external_symbols, {99: {0}})


class TestBinaryStateEvaluation(unittest.TestCase):
    def _compute(self, operator, left, right):
        stmt_states = object.__new__(StmtStates)
        status = common_structure.StmtStatus(stmt_id=7)
        stmt_states.frame = SimpleNamespace(stmt_id_to_status={7: status})
        captured = []
        stmt_states.create_state_and_add_space = (
            lambda *args, **kwargs: captured.append(kwargs) or 1
        )
        stmt_states.update_access_path_state_id = lambda index: None

        result = stmt_states.compute_two_states(
            SimpleNamespace(stmt_id=7, operator=operator),
            left,
            right,
            common_structure.Symbol(symbol_id=9, name="result"),
        )
        return result, captured

    def test_evaluates_c_logical_or_instead_of_materializing_expression_text(self):
        result, captured = self._compute(
            "||",
            common_structure.State(value=1, data_type="%int"),
            common_structure.State(value=0, data_type="%int"),
        )

        self.assertEqual(result, {1})
        self.assertIs(captured[0]["value"], True)

    def test_preserves_false_comparison_as_a_concrete_state(self):
        result, captured = self._compute(
            ">",
            common_structure.State(value=1, data_type="%int"),
            common_structure.State(value=2, data_type="%int"),
        )

        self.assertEqual(result, {1})
        self.assertIs(captured[0]["value"], False)

    def test_compares_numeric_state_strings_as_numbers(self):
        result, captured = self._compute(
            ">",
            common_structure.State(value="10", data_type="%int"),
            common_structure.State(value="2", data_type="%int"),
        )

        self.assertEqual(result, {1})
        self.assertIs(captured[0]["value"], True)

    def test_keeps_symbolic_string_logical_operands_symbolic(self):
        result, captured = self._compute(
            "||",
            common_structure.State(value="left_expr", data_type="%string"),
            common_structure.State(value="right_expr", data_type="%string"),
        )

        self.assertEqual(result, {1})
        self.assertEqual(captured[0]["value"], "left_expr||right_expr")

    def test_keeps_language_dependent_word_logical_operator_symbolic(self):
        result, captured = self._compute(
            "and",
            common_structure.State(value=1, data_type="%int"),
            common_structure.State(value=2, data_type="%int"),
        )

        self.assertEqual(result, {1})
        self.assertEqual(captured[0]["value"], "1and2")
        self.assertEqual(captured[0]["data_type"], "%string")


class TestSearchGraph(unittest.TestCase):
    def setUp(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(11, 1)
        graph.add_edge(12, 1)
        graph.add_edge(1, 2)
        graph.add_edge(21, 2)
        graph.add_edge(22, 2)
        graph.add_edge(211, 21)
        graph.add_edge(212, 21)
        graph.add_edge(2, 3)

        # 3 -> 2 -> 21 -> 211
        #              -> 212
        #        -> 22
        #        -> 1  -> 11
        #              -> 12

        self.result = {
            1: False,
            11: [11],
            12: [12],
            2: False,
            21: False,
            211: True,
            212: True,
            22: None,
            3: None,
        }

        self.graph = graph

    def test_backward_search(self):
        result = self.result
        class Test:
            def test(self, node):
                nonlocal result
                return result.get(node)

        search = common_structure.BasicGraph()
        search.graph = self.graph
        self.assertEqual(search.backward_search(3, Test().test), {11, 12, 211, 212})

    def test_pre_process_graph(self):
        pass


class TestCParserArrayDataType(unittest.TestCase):
    def parse_c_gir(self, code: str):
        lang = next(item for item in lang_config.LANG_TABLE if item.name == "c")
        lib = cdll.LoadLibrary(lang.so_path)
        lang_fn = getattr(lib, "tree_sitter_c")
        lang_fn.restype = c_void_p

        language = tree_sitter.Language(lang_fn())
        parser = tree_sitter.Parser(language)
        tree = parser.parse(code.encode("utf8"))

        options = type("Options", (), {
            "debug": False,
            "print_stmts": False,
            "strict_parse_mode": False,
        })()
        unit_info = type("UnitInfo", (), {"original_path": "array_decl_test.c"})()
        statements = []
        c_parser.Parser(options, unit_info).parse_gir(tree.root_node, statements)
        return statements

    def test_array_declaration_data_type_keeps_declared_size(self):
        statements = self.parse_c_gir(
            "int arr[3];\n"
            "int matrix[2][4];\n"
            "int *ptrs[5];\n"
        )

        decls = [stmt["variable_decl"] for stmt in statements if "variable_decl" in stmt]
        self.assertEqual(decls[0]["data_type"], "int[3]")
        self.assertEqual(decls[1]["data_type"], "int[2][4]")
        self.assertEqual(decls[2]["data_type"], "int*[5]")

    def test_multidimensional_array_initializer_stays_array(self):
        statements = self.parse_c_gir(
            "int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};\n"
        )

        operations = [
            next(iter(stmt.keys()))
            for stmt in statements
            if isinstance(stmt, dict) and stmt
        ]
        new_arrays = [stmt["new_array"] for stmt in statements if "new_array" in stmt]
        empty_type_structs = [
            stmt["new_struct"]
            for stmt in statements
            if "new_struct" in stmt and not stmt["new_struct"].get("data_type")
        ]

        self.assertGreaterEqual(len(new_arrays), 3)
        self.assertNotIn("new_struct", operations)
        self.assertEqual(empty_type_structs, [])

    def test_struct_initializer_with_array_field_stays_struct(self):
        statements = self.parse_c_gir(
            "struct Buffer { int data[4]; int *cursor; };\n"
            "struct Buffer buf = {{3, 1, 4, 1}, 0};\n"
        )

        struct_news = [stmt["new_struct"] for stmt in statements if "new_struct" in stmt]
        self.assertTrue(
            any(stmt.get("data_type") == "Buffer" for stmt in struct_news),
            msg=f"new_struct statements: {struct_news}",
        )

    def test_anonymous_struct_array_initializer_keeps_element_type(self):
        statements = self.parse_c_gir(
            'static struct { const char *s; int c; } keys[] = {{"x", 1}, {0, 0}};\n'
        )

        struct_news = [stmt["new_struct"] for stmt in statements if "new_struct" in stmt]
        empty_type_structs = [stmt for stmt in struct_news if not stmt.get("data_type")]

        self.assertEqual(empty_type_structs, [])
        self.assertGreaterEqual(len(struct_news), 2)
        self.assertTrue(
            all(stmt.get("data_type", "").startswith("%vv") for stmt in struct_news),
            msg=f"new_struct statements: {struct_news}",
        )


class TestCppParserEntrypoints(unittest.TestCase):
    def test_cpp_qualified_method_is_available_for_entry_point_selection(self):
        lang = next(item for item in lang_config.LANG_TABLE if item.name == "cpp")
        lib = cdll.LoadLibrary(lang.so_path)
        lang_fn = getattr(lib, "tree_sitter_cpp")
        lang_fn.restype = c_void_p

        parser = tree_sitter.Parser(tree_sitter.Language(lang_fn()))
        tree = parser.parse(b"int ProfileModel::importProfilesFromZip() { return 0; }")
        options = type("Options", (), {
            "debug": False,
            "print_stmts": False,
            "strict_parse_mode": False,
        })()
        unit_info = type("UnitInfo", (), {"original_path": "profile_model.cpp"})()
        statements = []

        lang.parser(options, unit_info).parse_gir(tree.root_node, statements)

        self.assertIn(
            "ProfileModel::importProfilesFromZip",
            [stmt["method_decl"]["name"] for stmt in statements if "method_decl" in stmt],
        )

    def test_cpp_constructor_declaration_without_a_type_does_not_abort_parsing(self):
        lang = next(item for item in lang_config.LANG_TABLE if item.name == "cpp")
        lib = cdll.LoadLibrary(lang.so_path)
        lang_fn = getattr(lib, "tree_sitter_cpp")
        lang_fn.restype = c_void_p

        parser = tree_sitter.Parser(tree_sitter.Language(lang_fn()))
        tree = parser.parse(
            b"class ProfileModel { public: ProfileModel(int value); };"
            b"int parseable_function() { return 0; }"
        )
        options = type("Options", (), {
            "debug": False,
            "print_stmts": False,
            "strict_parse_mode": False,
        })()
        unit_info = type("UnitInfo", (), {"original_path": "profile_model.cpp"})()
        statements = []

        lang.parser(options, unit_info).parse_gir(tree.root_node, statements)

        self.assertIn(
            "parseable_function",
            [stmt["method_decl"]["name"] for stmt in statements if "method_decl" in stmt],
        )


class TestCP2AddrOf(unittest.TestCase):
    def test_addr_of_parameter_does_not_crash_in_p2(self):
        with tempfile.TemporaryDirectory(prefix="lian_c_p2_addr_of_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_dir = tmp_path / "project"
            workspace_dir = tmp_path / "workspace"
            project_dir.mkdir()
            (project_dir / "addr_of.c").write_text(
                "void callee(int *p) {}\n"
                "void f(int n) { callee(&n); }\n",
                encoding="utf8",
            )

            env = os.environ.copy()
            src_path = str(Path(__file__).resolve().parents[2] / "src")
            env["PYTHONPATH"] = (
                src_path
                if not env.get("PYTHONPATH")
                else src_path + os.pathsep + env["PYTHONPATH"]
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lian.main",
                    "run",
                    str(project_dir),
                    "-l",
                    "c",
                    "-w",
                    str(workspace_dir),
                    "-f",
                    "--enable-p2",
                    "-q",
                ],
                cwd=Path(__file__).resolve().parents[2],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )

    def test_yank_anonymous_struct_array_does_not_crash_in_p2(self):
        with tempfile.TemporaryDirectory(prefix="lian_c_p2_yank_") as tmp_dir:
            workspace_dir = Path(tmp_dir) / "workspace"
            repo_root = Path(__file__).resolve().parents[2]

            env = os.environ.copy()
            src_path = str(repo_root / "src")
            env["PYTHONPATH"] = (
                src_path
                if not env.get("PYTHONPATH")
                else src_path + os.pathsep + env["PYTHONPATH"]
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lian.main",
                    "run",
                    str(repo_root / "tests" / "wy_bug" / "yank.c"),
                    "-l",
                    "c",
                    "-w",
                    str(workspace_dir),
                    "-f",
                    "--enable-p2",
                    "-q",
                ],
                cwd=repo_root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )

    def test_struct_field_write_does_not_crash_in_p2(self):
        with tempfile.TemporaryDirectory(prefix="lian_c_p2_mem_write_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_dir = tmp_path / "project"
            workspace_dir = tmp_path / "workspace"
            project_dir.mkdir()
            (project_dir / "mem_write.c").write_text(
                "typedef struct Node {\n"
                "    struct Node *next;\n"
                "} Node;\n"
                "\n"
                "void link(Node *p, Node *q) {\n"
                "    p->next = q;\n"
                "}\n",
                encoding="utf8",
            )

            env = os.environ.copy()
            src_path = str(Path(__file__).resolve().parents[2] / "src")
            env["PYTHONPATH"] = (
                src_path
                if not env.get("PYTHONPATH")
                else src_path + os.pathsep + env["PYTHONPATH"]
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lian.main",
                    "run",
                    str(project_dir),
                    "-l",
                    "c",
                    "-w",
                    str(workspace_dir),
                    "-f",
                    "--enable-p2",
                    "-q",
                ],
                cwd=Path(__file__).resolve().parents[2],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )


class TestTaintUnreadableSFG(unittest.TestCase):
    def _make_analysis(self, loader):
        lian = SimpleNamespace(loader=loader)
        options = SimpleNamespace(
            default_settings=str(Path(__file__).resolve().parents[2] / "default_settings"),
            quiet=False,
        )
        return TaintAnalysis(lian, options)

    def test_run_skips_unreadable_entry_point_and_continues(self):
        loader = SimpleNamespace(
            get_all_method_ids=lambda: [101, 202, 303],
            get_global_sfg_by_entry_point=lambda method_id: (
                (_ for _ in ()).throw(ArrowInvalid("File is too small"))
                if method_id == 202 else
                f"sfg-{method_id}"
            ),
        )
        analysis = self._make_analysis(loader)
        processed = []

        def fake_update_sfg(sfg):
            analysis.sfg = sfg

        analysis._update_sfg = fake_update_sfg
        analysis.find_sources = lambda: processed.append(("sources", analysis.current_entry_point)) or []
        analysis.find_sinks = lambda: processed.append(("sinks", analysis.current_entry_point)) or []
        analysis.find_flows = lambda sources, sinks: processed.append(("flows", analysis.current_entry_point)) or []

        with patch("builtins.print") as mock_print:
            result = analysis.run()

        self.assertIs(result, analysis)
        self.assertEqual(
            processed,
            [
                ("sources", 101), ("sinks", 101), ("flows", 101),
                ("sources", 303), ("sinks", 303), ("flows", 303),
            ],
        )
        printed = "\n".join(" ".join(str(arg) for arg in call.args) for call in mock_print.call_args_list)
        self.assertIn("Skip taint entry point 202", printed)
        self.assertIn("Skipped 1 entry points due to unreadable SFG bundles.", printed)

    def test_run_preserves_normal_taint_flow_path(self):
        loader = SimpleNamespace(
            get_all_method_ids=lambda: [11, 22],
            get_global_sfg_by_entry_point=lambda method_id: f"sfg-{method_id}",
        )
        analysis = self._make_analysis(loader)
        processed = []

        def fake_update_sfg(sfg):
            analysis.sfg = sfg

        analysis._update_sfg = fake_update_sfg
        analysis.find_sources = lambda: processed.append(("sources", analysis.current_entry_point)) or ["source"]
        analysis.find_sinks = lambda: processed.append(("sinks", analysis.current_entry_point)) or ["sink"]
        analysis.find_flows = lambda sources, sinks: processed.append(("flows", analysis.current_entry_point)) or []

        with patch("builtins.print") as mock_print:
            result = analysis.run()

        self.assertIs(result, analysis)
        self.assertEqual(
            processed,
            [
                ("sources", 11), ("sinks", 11), ("flows", 11),
                ("sources", 22), ("sinks", 22), ("flows", 22),
            ],
        )
        printed = "\n".join(" ".join(str(arg) for arg in call.args) for call in mock_print.call_args_list)
        self.assertNotIn("Skip taint entry point", printed)
        self.assertNotIn("Skipped 1 entry points", printed)



if __name__ == '__main__':
    unittest.main()
