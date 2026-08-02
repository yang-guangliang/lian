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
from unittest.mock import MagicMock, patch
import pandas as pd
import networkx as nx
import tree_sitter
from pyarrow.lib import ArrowInvalid

import tests.run.init_test as init_test

from lian.config import lang_config
from lian.config.constants import ANALYSIS_PHASE_ID, LIAN_INTERNAL, STATE_TYPE_KIND
from lian import common_structs as common_structure
from lian.core.global_semantics import P3GlobalSemanticAnalysis
from lian.core.prelim_semantics import P2PrelimSemanticAnalysis
from lian.core.resolver import Resolver
from lian.core.stmt_states import StmtStates
from lian.lang import c_parser
from lian.lang.lang_analysis import GIRParser
from lian.taint.taint_analysis import TaintAnalysis
from lian.util import util
from lian.util.data_model import DataModel
from lian.util.loader import CalleeParameterMapping, Loader, SymbolStateSpaceLoader


class CountingCalleeParameterMapping(CalleeParameterMapping):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decode_count = 0
        self.raw_read_count = 0

    def get_raw_item_by_id(self, item_id):
        self.raw_read_count += 1
        return super().get_raw_item_by_id(item_id)

    def unflatten_item_dataframe_when_loading(self, item_id, flattened_item):
        self.decode_count += 1
        return super().unflatten_item_dataframe_when_loading(item_id, flattened_item)


class TestCalleeParameterMappingCache(unittest.TestCase):
    @staticmethod
    def make_loader(tmp_dir):
        return CountingCalleeParameterMapping(
            options=None,
            item_schema=[],
            bundle_path_summary=os.path.join(tmp_dir, "parameter_mapping"),
            item_cache_capacity=20,
            bundle_cache_capacity=2,
        )

    @staticmethod
    def make_mapping(arg_state_id):
        return common_structure.ParameterMapping(
            arg_index_in_space=3,
            arg_state_id=arg_state_id,
            arg_source_symbol_id=7,
            arg_access_path=[common_structure.AccessPoint(kind=1, key="field", state_id=11)],
            parameter_symbol_id=13,
            parameter_access_path=common_structure.AccessPoint(kind=2, key="0", state_id=17),
        )

    def test_repeated_reads_decode_a_call_site_only_once(self):
        with tempfile.TemporaryDirectory(prefix="lian_parameter_mapping_") as tmp_dir:
            loader = self.make_loader(tmp_dir)
            call_site = common_structure.CallSite(1, 2, 3)
            loader.save(call_site, [self.make_mapping(5)])

            loader.get_item_by_id(call_site)
            loader.get_item_by_id(call_site)

            self.assertEqual(loader.decode_count, 1)
            self.assertEqual(loader.raw_read_count, 2)

    def test_cached_reads_return_independent_mutable_values(self):
        with tempfile.TemporaryDirectory(prefix="lian_parameter_mapping_") as tmp_dir:
            loader = self.make_loader(tmp_dir)
            call_site = common_structure.CallSite(1, 2, 3)
            loader.save(call_site, [self.make_mapping(5)])

            first = loader.get_item_by_id(call_site)
            first[0].arg_access_path[0].key = "changed"
            first[0].parameter_access_path.key = "changed"
            second = loader.get_item_by_id(call_site)

            self.assertEqual(second[0].arg_access_path[0].key, "field")
            self.assertEqual(second[0].parameter_access_path.key, "0")


class CountingSymbolStateSpaceLoader(SymbolStateSpaceLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decode_count = 0
        self.raw_read_count = 0

    def get_raw_item_by_id(self, item_id):
        self.raw_read_count += 1
        return super().get_raw_item_by_id(item_id)

    def unflatten_item_dataframe_when_loading(self, item_id, flattened_item):
        self.decode_count += 1
        return super().unflatten_item_dataframe_when_loading(item_id, flattened_item)


class TestP1SymbolStateSpaceCache(unittest.TestCase):
    @staticmethod
    def make_loader(tmp_dir, raw_cache_capacity=20):
        raw_loader = CountingSymbolStateSpaceLoader(
            options=None,
            item_schema=[],
            bundle_path_summary=os.path.join(tmp_dir, "symbol_state_space"),
            item_cache_capacity=raw_cache_capacity,
            bundle_cache_capacity=2,
        )
        loader = object.__new__(Loader)
        loader._symbol_state_space_p1_loader = raw_loader
        loader._symbol_state_space_p1_decoded_cache = util.LRUCache(4)
        return loader, raw_loader

    @staticmethod
    def make_space(state_id):
        space = common_structure.SymbolStateSpace()
        space.add(common_structure.Symbol(symbol_id=3, states={1}))
        space.add(
            common_structure.State(
                state_id=state_id,
                fields={"field": {0}},
                array=[{0}],
                tangping_elements={0},
                access_path=[
                    common_structure.AccessPoint(
                        kind=1, key="field", state_id=state_id
                    )
                ],
            )
        )
        return space

    def test_repeated_reads_decode_a_method_only_once(self):
        with tempfile.TemporaryDirectory(prefix="lian_p1_space_") as tmp_dir:
            loader, raw_loader = self.make_loader(tmp_dir)
            raw_loader.save(7, self.make_space(11))

            loader.get_symbol_state_space_p1_copy(7)
            loader.get_symbol_state_space_p1_copy(7)

            self.assertEqual(raw_loader.decode_count, 1)
            self.assertEqual(raw_loader.raw_read_count, 2)

    def test_cached_reads_return_fully_independent_spaces(self):
        with tempfile.TemporaryDirectory(prefix="lian_p1_space_") as tmp_dir:
            loader, raw_loader = self.make_loader(tmp_dir)
            raw_loader.save(7, self.make_space(11))

            first = loader.get_symbol_state_space_p1_copy(7)
            first[0].states.add(99)
            first[1].fields["field"].add(99)
            first[1].array[0].add(99)
            first[1].tangping_elements.add(99)
            first[1].access_path[0].state_id = 99
            second = loader.get_symbol_state_space_p1_copy(7)

            self.assertEqual(second[0].states, {1})
            self.assertEqual(second[1].fields, {"field": {0}})
            self.assertEqual(second[1].array, [{0}])
            self.assertEqual(second[1].tangping_elements, {0})
            self.assertEqual(second[1].access_path[0].state_id, 11)

    def test_replacing_the_raw_data_model_forces_a_new_decode(self):
        with tempfile.TemporaryDirectory(prefix="lian_p1_space_") as tmp_dir:
            loader, raw_loader = self.make_loader(tmp_dir)
            raw_loader.save(7, self.make_space(11))
            loader.get_symbol_state_space_p1_copy(7)

            raw_loader.item_cache.remove(7)
            raw_loader.active_bundle[7].data_model = None
            loader.get_symbol_state_space_p1_copy(7)

            self.assertEqual(raw_loader.decode_count, 2)

    def test_decoded_cache_hits_still_refresh_the_raw_lru_order(self):
        with tempfile.TemporaryDirectory(prefix="lian_p1_space_") as tmp_dir:
            loader, raw_loader = self.make_loader(tmp_dir, raw_cache_capacity=2)
            for method_id in (1, 2, 3):
                raw_loader.save(method_id, self.make_space(method_id))

            loader.get_symbol_state_space_p1_copy(1)
            loader.get_symbol_state_space_p1_copy(2)
            loader.get_symbol_state_space_p1_copy(1)
            loader.get_symbol_state_space_p1_copy(3)

            self.assertEqual(set(raw_loader.item_cache.cache), {1, 3})

    def test_already_decoded_items_are_still_returned_as_owned_copies(self):
        with tempfile.TemporaryDirectory(prefix="lian_p1_space_") as tmp_dir:
            loader, raw_loader = self.make_loader(tmp_dir)
            source = self.make_space(11)
            raw_loader.item_cache.put(7, source)

            copied = loader.get_symbol_state_space_p1_copy(7)
            copied[1].fields["field"].add(99)

            self.assertEqual(source[1].fields, {"field": {0}})


class CountingParameterBlock(DataModel):
    def __init__(self, data):
        super().__init__(data)
        self.iteration_count = 0

    def __iter__(self):
        self.iteration_count += 1
        yield from super().__iter__()


class TestMethodDeclParametersCache(unittest.TestCase):
    @staticmethod
    def make_block(first_symbol_id):
        return CountingParameterBlock(
            {
                "operation": [
                    "parameter_decl",
                    "parameter_decl",
                    "parameter_decl",
                    "return_stmt",
                ],
                "name": ["value", "args", "kwargs", ""],
                "stmt_id": [
                    first_symbol_id,
                    first_symbol_id + 1,
                    first_symbol_id + 2,
                    first_symbol_id + 3,
                ],
                "attrs": [
                    None,
                    [LIAN_INTERNAL.PACKED_POSITIONAL_PARAMETER],
                    [LIAN_INTERNAL.PACKED_NAMED_PARAMETER],
                    None,
                ],
            }
        )

    def test_repeated_parameter_preparation_decodes_once_and_touches_header(self):
        first_block = self.make_block(10)
        current_block = [first_block]
        header_reads = []
        loader = object.__new__(Loader)
        loader._method_decl_parameters_cache = util.LRUCache(100)

        def get_method_header(method_id):
            header_reads.append(method_id)
            return object(), current_block[0]

        loader.get_method_header = get_method_header
        stmt_states = object.__new__(StmtStates)
        stmt_states.loader = loader

        first = stmt_states.prepare_parameters(7)
        second = stmt_states.prepare_parameters(7)

        self.assertEqual(first_block.iteration_count, 1)
        self.assertEqual(header_reads, [7, 7])
        self.assertEqual(first.positional_parameters[0].name, "value")
        self.assertEqual(second.positional_parameters[0].name, "value")
        self.assertEqual(second.packed_positional_parameter.name, "args")
        self.assertEqual(second.packed_named_parameter.name, "kwargs")

    def test_cached_parameters_are_owned_and_redecoded_after_header_replacement(self):
        first_block = self.make_block(10)
        current_block = [first_block]
        loader = object.__new__(Loader)
        loader._method_decl_parameters_cache = util.LRUCache(100)
        loader.get_method_header = lambda method_id: (object(), current_block[0])
        stmt_states = object.__new__(StmtStates)
        stmt_states.loader = loader

        first = stmt_states.prepare_parameters(7)
        first.positional_parameters[0].name = "changed"
        first.packed_positional_parameter.packed_content.append("changed")
        first.packed_named_parameter.name = "changed"
        second = stmt_states.prepare_parameters(7)

        self.assertEqual(second.positional_parameters[0].name, "value")
        self.assertEqual(second.packed_positional_parameter.packed_content, [])
        self.assertEqual(second.packed_named_parameter.name, "kwargs")
        self.assertIsNot(
            first.positional_parameters[0], second.positional_parameters[0]
        )
        self.assertIn(second.positional_parameters[0], second.all_parameters)
        self.assertIn(second.packed_positional_parameter, second.all_parameters)
        self.assertIn(second.packed_named_parameter, second.all_parameters)

        replacement_block = self.make_block(20)
        current_block[0] = replacement_block
        replaced = stmt_states.prepare_parameters(7)

        self.assertEqual(replacement_block.iteration_count, 1)
        self.assertEqual(replaced.positional_parameters[0].symbol_id, 20)
        self.assertEqual(replaced.packed_named_parameter.symbol_id, 22)

class TestSimpleWorkList(unittest.TestCase):
    def test_fifo_uses_constant_time_queue_without_changing_order(self):
        worklist = common_structure.SimpleWorkList([3, 1, 2, 1])

        self.assertIsInstance(worklist.work_list, deque)
        self.assertEqual([worklist.pop(), worklist.pop(), worklist.pop()], [3, 1, 2])

    def test_fifo_insert_to_first_preserves_priority(self):
        worklist = common_structure.SimpleWorkList([2, 3])

        worklist.insert_to_first(1)

        self.assertEqual([worklist.pop(), worklist.pop(), worklist.pop()], [1, 2, 3])


class TestStateCopyIsolation(unittest.TestCase):
    def test_mutating_a_copied_access_path_does_not_change_the_source_state(self):
        source = common_structure.State(
            state_id=10,
            access_path=[
                common_structure.AccessPoint(kind=1, key="field", state_id=3)
            ],
        )

        copied = source.copy()
        copied.access_path[0].state_id = 10

        self.assertEqual(source.access_path[0].state_id, 3)


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


class TestGroupInStatesPredecessorLookup(unittest.TestCase):
    @staticmethod
    def make_analysis_and_frame():
        analysis = object.__new__(P2PrelimSemanticAnalysis)
        analysis.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        analysis.resolver = SimpleNamespace(
            collect_newest_states_by_state_indexes=(
                lambda frame, stmt_id, indexes, available_defs: set(indexes)
            )
        )

        frame = common_structure.ComputeFrame(method_id=1)
        first_symbol = frame.symbol_state_space.add(
            common_structure.Symbol(
                stmt_id=10, symbol_id=100, name="first", states={1}
            )
        )
        frame.symbol_state_space.add(
            common_structure.State(stmt_id=10, state_id=1000)
        )
        second_symbol = frame.symbol_state_space.add(
            common_structure.Symbol(
                stmt_id=20, symbol_id=200, name="second", states={3}
            )
        )
        frame.symbol_state_space.add(
            common_structure.State(stmt_id=20, state_id=2000)
        )
        frame.is_first_round[50] = True
        frame.state_bit_vector_manager = SimpleNamespace(explain=lambda bits: set())
        frame.stmt_state_analysis = SimpleNamespace(
            fuse_states_to_one_state=(
                lambda indexes, stmt_id, stmt, status, **kwargs: set(indexes)
            )
        )

        stmt = SimpleNamespace(operation="test_stmt", start_row=1)
        status = common_structure.StmtStatus(
            stmt_id=50, used_symbols=[first_symbol, second_symbol]
        )
        stmt_node = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.STMT,
            def_stmt_id=50,
            name=stmt.operation,
            context=frame.get_context(),
            stmt=stmt,
        )
        same_index_predecessor = common_structure.SFGNode(
            node_type=common_structure.SFG_NODE_KIND.SYMBOL,
            def_stmt_id=999,
            index=first_symbol,
            node_id=999,
            context=frame.get_context(),
        )
        frame.state_flow_graph.add_edge(same_index_predecessor, stmt_node)
        return analysis, frame, stmt, status, stmt_node, same_index_predecessor

    def test_reads_stmt_predecessors_once_without_changing_index_semantics(self):
        analysis, frame, stmt, status, stmt_node, same_index_predecessor = (
            self.make_analysis_and_frame()
        )
        original_graph_predecessors = util.graph_predecessors

        with patch(
            "lian.core.prelim_semantics.util.graph_predecessors",
            wraps=original_graph_predecessors,
        ) as graph_predecessors:
            analysis.group_in_states(50, stmt, status.used_symbols, frame, status)

        predecessors = set(frame.state_flow_graph.graph.predecessors(stmt_node))
        self.assertEqual(graph_predecessors.call_count, 1)
        self.assertEqual(
            {
                node.index
                for node in predecessors
                if node.node_type == common_structure.SFG_NODE_KIND.SYMBOL
            },
            {0, 2},
        )
        self.assertIn(same_index_predecessor, predecessors)
        self.assertNotIn(
            common_structure.SFGNode(
                node_type=common_structure.SFG_NODE_KIND.SYMBOL,
                def_stmt_id=10,
                index=0,
                node_id=100,
                context=frame.get_context(),
            ),
            predecessors,
        )


class TestStmtStateIndexValidation(unittest.TestCase):
    @staticmethod
    def make_global_field_merge(state_space, defined_state_indexes=()):
        status = common_structure.StmtStatus(
            stmt_id=7, defined_states=set(defined_state_indexes)
        )
        stmt_states = object.__new__(StmtStates)
        stmt_states.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        stmt_states.context = None
        stmt_states.sfg = common_structure.StateFlowGraph(method_id=1)
        stmt_states.frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={},
            all_state_defs=set(),
            state_bit_vector_manager=SimpleNamespace(
                add_bit_id=lambda node: None
            ),
        )
        return stmt_states, status

    def test_regular_empty_array_is_distinct_from_unknown_array(self):
        stmt_states = object.__new__(StmtStates)

        known_empty = common_structure.State(
            data_type=LIAN_INTERNAL.ARRAY,
            state_type=STATE_TYPE_KIND.REGULAR,
        )
        unknown_empty = common_structure.State(
            data_type=LIAN_INTERNAL.ARRAY,
            state_type=STATE_TYPE_KIND.ANYTHING,
        )
        unknown_with_known_element = common_structure.State(
            data_type=LIAN_INTERNAL.ARRAY,
            state_type=STATE_TYPE_KIND.ANYTHING,
            array=[{1}],
        )

        self.assertFalse(stmt_states.is_state_array_empty(known_empty))
        self.assertTrue(stmt_states.is_state_array_empty(unknown_empty))
        self.assertFalse(
            stmt_states.is_state_array_empty(unknown_with_known_element)
        )

    def test_copy_keeps_large_precise_array_without_mutating_history(self):
        state_space = common_structure.SymbolStateSpace()
        old_index = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=101,
                array=[{10}, {11}, {12}, {13}, {14}],
            )
        )
        graph = common_structure.StateFlowGraph(method_id=1)
        stmt_states = object.__new__(StmtStates)
        stmt_states.context = None
        stmt_states.sfg = graph
        stmt_states.frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={},
            all_state_defs=set(),
            state_bit_vector_manager=SimpleNamespace(add_bit_id=lambda node: None),
        )
        status = common_structure.StmtStatus(stmt_id=7, defined_states={old_index})

        new_index = stmt_states.create_copy_of_state_and_add_space(
            status, 7, old_index, SimpleNamespace(operation="array_write")
        )

        self.assertFalse(state_space[old_index].tangping_flag)
        self.assertEqual(state_space[old_index].array, [{10}, {11}, {12}, {13}, {14}])
        self.assertFalse(state_space[new_index].tangping_flag)
        self.assertEqual(state_space[new_index].array, state_space[old_index].array)
        self.assertIsNot(state_space[new_index].array[0], state_space[old_index].array[0])

    def test_contiguous_array_growth_beyond_four_slots_stays_precise(self):
        stmt_states, state_space, old_array_index, output_symbol = (
            self._array_write_fixture([{20}, {21}, {22}, {23}], index_value=4)
        )

        stmt_states.array_write_stmt_state(
            7,
            SimpleNamespace(operation="array_write"),
            stmt_states.frame.stmt_id_to_status[7],
            {},
        )

        new_array_index = next(iter(output_symbol.states))
        self.assertFalse(state_space[new_array_index].tangping_flag)
        self.assertEqual(state_space[new_array_index].array[4], {6})
        self.assertEqual(state_space[old_array_index].array, [{20}, {21}, {22}, {23}])

    def test_array_slot_update_does_not_mutate_historical_state(self):
        stmt_states, state_space, old_array_index, output_symbol = (
            self._array_write_fixture([{20}], index_value=0)
        )

        stmt_states.array_write_stmt_state(
            7,
            SimpleNamespace(operation="array_write"),
            stmt_states.frame.stmt_id_to_status[7],
            {},
        )

        new_array_index = next(iter(output_symbol.states))
        self.assertEqual(state_space[old_array_index].array, [{20}])
        self.assertEqual(state_space[new_array_index].array, [{20, 6}])
        self.assertIsNot(
            state_space[new_array_index].array[0],
            state_space[old_array_index].array[0],
        )

    def test_extremely_sparse_array_write_does_not_allocate_to_index(self):
        stmt_states, state_space, old_array_index, output_symbol = (
            self._array_write_fixture([{20}], index_value=1_000_000)
        )

        stmt_states.array_write_stmt_state(
            7,
            SimpleNamespace(operation="array_write"),
            stmt_states.frame.stmt_id_to_status[7],
            {},
        )

        new_array_index = next(iter(output_symbol.states))
        self.assertTrue(state_space[new_array_index].tangping_flag)
        self.assertLessEqual(len(state_space[new_array_index].array), 1)
        self.assertEqual(state_space[old_array_index].array, [{20}])

    def _array_write_fixture(self, array, index_value):
        state_space = common_structure.SymbolStateSpace()
        array_symbol_index = state_space.add(common_structure.Symbol(symbol_id=1))
        index_symbol_index = state_space.add(common_structure.Symbol(symbol_id=2))
        source_symbol_index = state_space.add(common_structure.Symbol(symbol_id=3))
        output_symbol = common_structure.Symbol(symbol_id=4)
        output_symbol_index = state_space.add(output_symbol)
        old_array_index = state_space.add(
            common_structure.State(stmt_id=1, state_id=101, array=array)
        )
        index_state_index = state_space.add(
            common_structure.State(stmt_id=1, state_id=102, value=str(index_value))
        )
        source_state_index = state_space.add(
            common_structure.State(stmt_id=1, state_id=103, value="source")
        )
        status = common_structure.StmtStatus(
            stmt_id=7,
            defined_symbol=output_symbol_index,
            used_symbols=[array_symbol_index, index_symbol_index, source_symbol_index],
            defined_states={old_array_index},
        )
        graph = common_structure.StateFlowGraph(method_id=1)
        stmt_states = object.__new__(StmtStates)
        stmt_states.context = None
        stmt_states.sfg = graph
        stmt_states.frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={},
            all_state_defs=set(),
            state_bit_vector_manager=SimpleNamespace(add_bit_id=lambda node: None),
            stmt_counters={7: 1},
            stmt_id_to_status={7: status},
        )
        used_states = {
            array_symbol_index: {old_array_index},
            index_symbol_index: {index_state_index},
            source_symbol_index: {source_state_index},
        }
        stmt_states.read_used_states = lambda symbol_index, in_states: used_states[symbol_index]
        return stmt_states, state_space, old_array_index, output_symbol

    def test_copy_keeps_large_precise_record_without_mutating_history(self):
        fields = {f"field{index}": {100 + index} for index in range(33)}
        state_space = common_structure.SymbolStateSpace()
        old_index = state_space.add(
            common_structure.State(stmt_id=1, state_id=101, fields=fields)
        )
        stmt_states = object.__new__(StmtStates)
        stmt_states.context = None
        stmt_states.sfg = common_structure.StateFlowGraph(method_id=1)
        stmt_states.frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={},
            all_state_defs=set(),
            state_bit_vector_manager=SimpleNamespace(add_bit_id=lambda node: None),
        )
        status = common_structure.StmtStatus(stmt_id=7, defined_states={old_index})

        new_index = stmt_states.create_copy_of_state_and_add_space(
            status, 7, old_index, SimpleNamespace(operation="field_write")
        )

        self.assertFalse(state_space[old_index].tangping_flag)
        self.assertEqual(state_space[old_index].fields, fields)
        self.assertFalse(state_space[new_index].tangping_flag)
        self.assertEqual(state_space[new_index].fields, fields)
        self.assertIsNot(
            state_space[new_index].fields["field0"],
            state_space[old_index].fields["field0"],
        )

    def test_known_record_field_growth_beyond_32_stays_precise(self):
        stmt_states, state_space, receiver_index, output_symbol, source_states = (
            self._field_write_fixture(field_count=32)
        )

        stmt_states.field_write_stmt_state(
            7,
            SimpleNamespace(operation="field_write"),
            stmt_states.frame.stmt_id_to_status[7],
            {},
        )

        new_receiver_index = next(iter(output_symbol.states))
        self.assertFalse(state_space[receiver_index].tangping_flag)
        self.assertEqual(len(state_space[receiver_index].fields), 32)
        self.assertFalse(state_space[new_receiver_index].tangping_flag)
        self.assertEqual(len(state_space[new_receiver_index].fields), 33)
        self.assertEqual(
            state_space[new_receiver_index].fields["field32"], source_states
        )

    def test_tangping_field_write_copies_history_and_keeps_all_sources(self):
        stmt_states, state_space, receiver_index, output_symbol, source_states = (
            self._field_write_fixture(tangping=True, source_count=6)
        )
        old_elements = state_space[receiver_index].tangping_elements.copy()

        stmt_states.field_write_stmt_state(
            7,
            SimpleNamespace(operation="field_write"),
            stmt_states.frame.stmt_id_to_status[7],
            {},
        )

        new_receiver_index = next(iter(output_symbol.states))
        self.assertNotEqual(new_receiver_index, receiver_index)
        self.assertEqual(
            state_space[receiver_index].tangping_elements, old_elements
        )
        self.assertEqual(
            state_space[new_receiver_index].tangping_elements,
            old_elements | source_states,
        )

    def _field_write_fixture(self, field_count=0, tangping=False, source_count=1):
        state_space = common_structure.SymbolStateSpace()
        receiver_symbol_index = state_space.add(
            common_structure.Symbol(symbol_id=1)
        )
        field_symbol_index = state_space.add(common_structure.Symbol(symbol_id=2))
        source_symbol_index = state_space.add(common_structure.Symbol(symbol_id=3))
        output_symbol = common_structure.Symbol(symbol_id=4)
        output_symbol_index = state_space.add(output_symbol)
        field_state_index = state_space.add(
            common_structure.State(stmt_id=1, state_id=102, value=f"field{field_count}")
        )
        source_states = {
            state_space.add(
                common_structure.State(
                    stmt_id=1, state_id=200 + index, value=f"source{index}"
                )
            )
            for index in range(source_count)
        }
        old_tangping_elements = set()
        if tangping:
            old_tangping_elements.add(
                state_space.add(
                    common_structure.State(
                        stmt_id=1, state_id=300, value="historical"
                    )
                )
            )
        receiver_index = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=101,
                fields={
                    f"field{index}": {min(source_states)}
                    for index in range(field_count)
                },
                tangping_flag=tangping,
                tangping_elements=old_tangping_elements,
            )
        )
        status = common_structure.StmtStatus(
            stmt_id=7,
            defined_symbol=output_symbol_index,
            used_symbols=[
                receiver_symbol_index,
                field_symbol_index,
                source_symbol_index,
            ],
            defined_states={receiver_index},
        )
        stmt_states = object.__new__(StmtStates)
        stmt_states.context = None
        stmt_states.lang = "c"
        stmt_states.resolver = object()
        stmt_states.sfg = common_structure.StateFlowGraph(method_id=1)
        stmt_states.event_manager = SimpleNamespace(notify=lambda event: None)
        stmt_states.frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={},
            all_state_defs=set(),
            state_bit_vector_manager=SimpleNamespace(add_bit_id=lambda node: None),
            stmt_counters={7: 1},
            stmt_id_to_status={7: status},
        )
        used_states = {
            receiver_symbol_index: {receiver_index},
            field_symbol_index: {field_state_index},
            source_symbol_index: source_states,
        }
        stmt_states.read_used_states = (
            lambda symbol_index, in_states: used_states[symbol_index]
        )
        return stmt_states, state_space, receiver_index, output_symbol, source_states

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
        stmt_states, status = self.make_global_field_merge(
            state_space, {valid_state_index}
        )
        initial_size = len(state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=status,
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
        self.assertEqual(len(state_space), initial_size)
        self.assertEqual(state_space[valid_state_index].source_symbol_id, -1)

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

        stmt_states, status = self.make_global_field_merge(
            state_space, argument_indexes
        )
        initial_size = len(state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=status,
            state_set_in_summary_field={summary_indexes[0]},
            state_set_in_arg_field={argument_indexes[0]},
            source_symbol_id=11,
            access_path=[],
        )

        resolved_index = next(iter(result))
        for depth_index in range(depth):
            self.assertNotIn(resolved_index, argument_indexes)
            if depth_index + 1 < depth:
                resolved_index = next(
                    iter(state_space[resolved_index].fields["next"])
                )
        self.assertEqual(len(state_space), initial_size + depth)
        self.assertEqual(
            state_space[argument_indexes[0]].fields,
            {"next": {argument_indexes[1]}},
        )

    def test_field_merge_preserves_self_referential_argument_field(self):
        state_space = common_structure.SymbolStateSpace()
        summary_index = state_space.add(common_structure.State(state_id=101))
        argument_index = state_space.add(common_structure.State(state_id=201))
        state_space[summary_index].fields = {"self": {summary_index}}
        state_space[argument_index].fields = {"self": {argument_index}}

        stmt_states, status = self.make_global_field_merge(
            state_space, {argument_index}
        )

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=status,
            state_set_in_summary_field={summary_index},
            state_set_in_arg_field={argument_index},
            source_symbol_id=11,
            access_path=[],
        )

        resolved_index = next(iter(result))
        self.assertNotEqual(resolved_index, argument_index)
        self.assertEqual(
            state_space[resolved_index].fields["self"], {resolved_index}
        )
        self.assertEqual(state_space[argument_index].fields["self"], {argument_index})

    def test_field_merge_preserves_mutually_recursive_argument_fields(self):
        state_space = common_structure.SymbolStateSpace()
        summary_root = state_space.add(common_structure.State(state_id=101))
        summary_child = state_space.add(common_structure.State(state_id=102))
        summary_leaf = state_space.add(
            common_structure.State(state_id=103, value="summary")
        )
        argument_root = state_space.add(common_structure.State(state_id=201))
        argument_child = state_space.add(common_structure.State(state_id=202))
        state_space[summary_root].fields = {"next": {summary_child}}
        state_space[summary_child].fields = {
            "back": {summary_root},
            "from_summary": {summary_leaf},
        }
        state_space[argument_root].fields = {"next": {argument_child}}
        state_space[argument_child].fields = {"back": {argument_root}}
        stmt_states, status = self.make_global_field_merge(
            state_space, {argument_root, argument_child}
        )

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=status,
            state_set_in_summary_field={summary_root},
            state_set_in_arg_field={argument_root},
            source_symbol_id=11,
            access_path=[],
        )

        resolved_root = next(iter(result))
        resolved_child = next(iter(state_space[resolved_root].fields["next"]))
        self.assertNotEqual(resolved_root, argument_root)
        self.assertNotEqual(resolved_child, argument_child)
        self.assertEqual(
            state_space[resolved_child].fields,
            {
                "back": {resolved_root},
                "from_summary": {summary_leaf},
            },
        )
        self.assertEqual(
            state_space[argument_root].fields, {"next": {argument_child}}
        )
        self.assertEqual(
            state_space[argument_child].fields, {"back": {argument_root}}
        )

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

        stmt_states, status = self.make_global_field_merge(
            state_space, {argument_root, argument_child}
        )
        initial_size = len(state_space)

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=status,
            state_set_in_summary_field={summary_root},
            state_set_in_arg_field={argument_root},
            source_symbol_id=11,
            access_path=[],
        )

        resolved_root = next(iter(result))
        resolved_child = next(
            iter(state_space[resolved_root].fields["shared"])
        )
        self.assertNotEqual(resolved_root, argument_root)
        self.assertNotEqual(resolved_child, argument_child)
        self.assertEqual(
            state_space[resolved_root].fields,
            {
                "shared": {resolved_child},
                "summary_only": {summary_only},
                "argument_only": {argument_only},
            },
        )
        self.assertEqual(
            state_space[resolved_child].fields,
            {
                "from_argument": {argument_leaf},
                "from_summary": {summary_leaf},
            },
        )
        self.assertEqual(
            state_space[argument_root].fields,
            {
                "shared": {argument_child},
                "argument_only": {argument_only},
            },
        )
        self.assertEqual(
            state_space[argument_child].fields,
            {"from_argument": {argument_leaf}},
        )
        self.assertEqual(len(state_space), initial_size + 2)

    def test_global_field_merge_does_not_mutate_shared_argument_states(self):
        state_space = common_structure.SymbolStateSpace()
        summary_leaf = state_space.add(
            common_structure.State(stmt_id=2, state_id=102, value="summary")
        )
        summary_root = state_space.add(
            common_structure.State(
                stmt_id=2,
                state_id=101,
                fields={"from_summary": {summary_leaf}},
            )
        )
        argument_leaf = state_space.add(
            common_structure.State(stmt_id=1, state_id=202, value="argument")
        )
        argument_root = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=201,
                fields={"from_argument": {argument_leaf}},
            )
        )
        stmt_states, status = self.make_global_field_merge(
            state_space, {argument_root}
        )

        result = stmt_states.recursively_collect_children_fields(
            stmt_id=7,
            stmt=SimpleNamespace(operation="call_stmt"),
            status=status,
            state_set_in_summary_field={summary_root},
            state_set_in_arg_field={argument_root},
            source_symbol_id=11,
            access_path=[],
        )

        resolved_root = next(iter(result))
        self.assertNotEqual(resolved_root, argument_root)
        self.assertEqual(state_space[resolved_root].stmt_id, 7)
        self.assertNotIn(argument_root, status.defined_states)
        self.assertIn(resolved_root, status.defined_states)
        self.assertEqual(
            state_space[argument_root].fields,
            {"from_argument": {argument_leaf}},
            "a shared historical state must remain immutable",
        )
        self.assertEqual(
            state_space[resolved_root].fields,
            {
                "from_argument": {argument_leaf},
                "from_summary": {summary_leaf},
            },
        )


class TestResolverStateIndexValidation(unittest.TestCase):
    def test_nested_unresolved_field_remains_symbolic(self):
        state_space = common_structure.SymbolStateSpace()
        concrete_child = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=20,
                state_type=STATE_TYPE_KIND.REGULAR,
            )
        )
        parent = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=10,
                state_type=STATE_TYPE_KIND.ANYTHING,
                source_symbol_id=99,
                access_path=[
                    common_structure.AccessPoint(),
                    common_structure.AccessPoint(),
                ],
                fields={
                    "unresolved": {-1},
                    "concrete": {concrete_child},
                },
            )
        )
        frame = SimpleNamespace(symbol_state_space=state_space)
        resolver = object.__new__(Resolver)
        resolver.ras_result_cache = {}
        target_indexes = {parent}
        processing = (
            Resolver.resolve_anything_with_same_src_symbol_in_summary_generation
            .processing_list
        )
        processing.clear()

        try:
            resolved = (
                resolver.resolve_anything_with_same_src_symbol_in_summary_generation(
                    parent,
                    frame,
                    stmt_id=7,
                    callee_id=8,
                    parameter_symbol_id=99,
                    deferred_index_updates=set(),
                    set_to_update=target_indexes,
                    arg_state_indexes=set(),
                )
            )
        finally:
            processing.clear()

        self.assertEqual(resolved, parent)
        self.assertEqual(target_indexes, {parent})
        self.assertEqual(
            state_space[parent].fields,
            {
                "unresolved": {-1},
                "concrete": {concrete_child},
            },
            "an unresolved sentinel must stay symbolic without dropping concrete siblings",
        )


class TestResolverStateGraphDepth(unittest.TestCase):
    def test_changed_deep_path_is_not_scanned_once_per_ancestor(self):
        class CountingStateSpace(common_structure.SymbolStateSpace):
            def __init__(self):
                super().__init__()
                self.read_count = 0

            def __getitem__(self, index):
                self.read_count += 1
                return super().__getitem__(index)

        depth = 200
        state_space = CountingStateSpace()
        old_indexes = [
            state_space.add(
                common_structure.State(stmt_id=1, state_id=1000 + index)
            )
            for index in range(depth)
        ]
        for index in range(depth - 1):
            state_space[old_indexes[index]].fields = {
                "next": {old_indexes[index + 1]}
            }
        latest_leaf = state_space.add(
            common_structure.State(
                stmt_id=2,
                state_id=state_space[old_indexes[-1]].state_id,
                value="latest",
            )
        )
        latest_definition = common_structure.StateDefNode(
            index=latest_leaf,
            state_id=state_space[latest_leaf].state_id,
            stmt_id=2,
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={latest_definition.state_id: {latest_definition}},
            latest_source_cache={},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )
        state_space.read_count = 0

        result = object.__new__(Resolver).retrieve_latest_states(
            frame,
            7,
            state_space,
            {old_indexes[0]},
            {latest_definition},
            {},
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(len(state_space), depth * 2)
        self.assertLess(
            state_space.read_count,
            depth * 20,
            "one changed descendant must not rescan the remaining path for every ancestor",
        )

    def test_available_definition_index_observes_same_set_mutation(self):
        state_space = common_structure.SymbolStateSpace()
        old_state = state_space.add(
            common_structure.State(stmt_id=1, state_id=20, value="old")
        )
        first_latest = state_space.add(
            common_structure.State(stmt_id=2, state_id=20, value="first")
        )
        second_latest = state_space.add(
            common_structure.State(stmt_id=3, state_id=20, value="second")
        )
        first_definition = common_structure.StateDefNode(
            index=first_latest, state_id=20, stmt_id=2
        )
        second_definition = common_structure.StateDefNode(
            index=second_latest, state_id=20, stmt_id=3
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={20: {first_definition, second_definition}},
            latest_source_cache={},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )
        available_definitions = {first_definition}
        resolver = object.__new__(Resolver)

        first_result = resolver.retrieve_latest_states(
            frame,
            7,
            state_space,
            {old_state},
            available_definitions,
            {},
        )
        available_definitions.clear()
        available_definitions.add(second_definition)
        second_result = resolver.retrieve_latest_states(
            frame,
            7,
            state_space,
            {old_state},
            available_definitions,
            {},
        )

        self.assertEqual(first_result, {first_latest})
        self.assertEqual(
            second_result,
            {second_latest},
            "a mutable definition set must not reuse an index from an older snapshot",
        )

    def test_reuses_current_structured_state_without_copying_its_graph(self):
        state_space = common_structure.SymbolStateSpace()
        child = state_space.add(
            common_structure.State(stmt_id=1, state_id=20, value="current")
        )
        root = state_space.add(
            common_structure.State(
                stmt_id=1, state_id=10, fields={"child": {child}}
            )
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={},
            latest_source_cache={},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )

        result = Resolver.retrieve_latest_states(
            object.__new__(Resolver), frame, 7, state_space, {root}, set(), {}
        )

        self.assertEqual(result, {root})
        self.assertEqual(
            len(state_space),
            2,
            "an unchanged structured state is already the precise latest graph",
        )

    def test_copies_only_the_path_to_a_newer_descendant(self):
        state_space = common_structure.SymbolStateSpace()
        old_child = state_space.add(
            common_structure.State(stmt_id=1, state_id=20, value="old")
        )
        unchanged_leaf = state_space.add(
            common_structure.State(stmt_id=1, state_id=40, value="unchanged")
        )
        unchanged_branch = state_space.add(
            common_structure.State(
                stmt_id=1, state_id=30, fields={"leaf": {unchanged_leaf}}
            )
        )
        root = state_space.add(
            common_structure.State(
                stmt_id=1,
                state_id=10,
                fields={
                    "changed": {old_child},
                    "unchanged": {unchanged_branch},
                },
            )
        )
        latest_child = state_space.add(
            common_structure.State(stmt_id=2, state_id=20, value="latest")
        )
        latest_definition = common_structure.StateDefNode(
            index=latest_child, state_id=20, stmt_id=2
        )
        frame = SimpleNamespace(
            symbol_state_space=state_space,
            defined_states={20: {latest_definition}},
            latest_source_cache={},
            stmt_id_to_status={7: common_structure.StmtStatus(stmt_id=7)},
        )
        initial_size = len(state_space)

        result = Resolver.retrieve_latest_states(
            object.__new__(Resolver),
            frame,
            7,
            state_space,
            {root},
            {latest_definition},
            {},
        )

        resolved_root = next(iter(result))
        self.assertNotEqual(resolved_root, root)
        self.assertEqual(
            state_space[resolved_root].fields,
            {
                "changed": {latest_child},
                "unchanged": {unchanged_branch},
            },
        )
        self.assertEqual(
            len(state_space),
            initial_size + 1,
            "only the ancestor edge that changed needs a new state",
        )
        self.assertEqual(
            state_space[root].fields,
            {
                "changed": {old_child},
                "unchanged": {unchanged_branch},
            },
        )

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


class TestOversizedMethodCoverage(unittest.TestCase):
    STMT_COUNT = 2001

    @classmethod
    def make_loader(cls):
        stmt_ids = list(range(1, cls.STMT_COUNT + 1))
        body = [
            SimpleNamespace(stmt_id=stmt_id, operation="return_stmt")
            for stmt_id in stmt_ids
        ]
        cfg = nx.DiGraph()
        cfg.add_nodes_from(stmt_ids)
        source_space = common_structure.SymbolStateSpace()
        source_space.add(common_structure.State(stmt_id=1, state_id=10))

        loader = MagicMock()
        loader.convert_method_id_to_unit_id.return_value = 1
        loader.convert_unit_id_to_lang_name.return_value = "c"
        loader.convert_method_id_to_method_name.return_value = "large_method"
        loader.contain_symbol_state_space_p1.return_value = True
        loader.get_method_cfg.return_value = cfg
        loader.get_splitted_method_gir.return_value = (None, [], body)
        loader.get_stmt_status_p1.return_value = {}
        loader.get_symbol_state_space_p1.return_value = source_space
        loader.get_method_internal_callees.return_value = []
        loader.get_method_def_use_summary.return_value = (
            common_structure.MethodDefUseSummary(method_id=7)
        )
        loader.get_method_defined_symbols_raw_p1.return_value = []
        loader.get_method_defined_states_p1.return_value = {}
        loader.get_method_defined_symbols_p2.return_value = {}
        loader.get_method_defined_states_p2.return_value = {}
        loader.get_stmt_status_p2.return_value = {}
        loader.get_symbol_state_space_p2.return_value = source_space
        loader.get_symbol_bit_vector_p2.return_value = (
            common_structure.BitVectorManager()
        )
        loader.get_state_bit_vector_p2.return_value = (
            common_structure.BitVectorManager()
        )
        loader.get_method_summary_template.return_value = (
            common_structure.MethodSummaryTemplate(key=7)
        )
        loader.get_symbol_state_space_summary_p2.return_value = (
            common_structure.SymbolStateSpace()
        )
        loader.get_method_symbol_graph_p2.return_value = nx.DiGraph()
        return loader, stmt_ids

    @staticmethod
    def make_frame_stack(frame):
        frame_stack = common_structure.ComputeFrameStack()
        frame_stack.add(common_structure.MetaComputeFrame())
        frame_stack.add(frame)
        return frame_stack

    def test_prelim_initializes_every_statement_beyond_old_limit(self):
        loader, stmt_ids = self.make_loader()
        frame = common_structure.ComputeFrame(method_id=7, loader=loader)
        analysis = object.__new__(P2PrelimSemanticAnalysis)
        analysis.loader = loader
        analysis.analysis_phase_id = ANALYSIS_PHASE_ID.PRELIM_SEMANTICS
        analysis.options = SimpleNamespace(quiet=True, complete_graph=False)
        analysis.event_manager = None
        analysis.resolver = object()
        analysis.call_graph = None
        analysis.analyzed_method_list = set()

        initialized = analysis.init_compute_frame(
            frame, self.make_frame_stack(frame)
        )

        self.assertIs(initialized, frame)
        self.assertEqual(set(frame.stmt_counters), set(stmt_ids))
        self.assertEqual(len(frame.stmt_worklist), self.STMT_COUNT)

    def test_global_with_p2_initializes_every_statement_beyond_old_limit(self):
        loader, stmt_ids = self.make_loader()
        frame = common_structure.ComputeFrame(method_id=7, loader=loader)
        analysis = object.__new__(P3GlobalSemanticAnalysis)
        analysis.loader = loader
        analysis.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        analysis.options = SimpleNamespace(
            enable_p2=True, quiet=True, complete_graph=False
        )
        analysis.analyzed_method_list = set()
        analysis.event_manager = None
        analysis.resolver = object()
        analysis.path_manager = common_structure.PathManager()
        analysis.caller_unknown_callee_edge = {}
        analysis.call_site_analyze_counter = {}

        initialized = analysis.init_compute_frame(
            frame,
            self.make_frame_stack(frame),
            common_structure.SymbolStateSpace(),
        )

        self.assertIs(initialized, frame)
        self.assertEqual(set(frame.stmt_counters), set(stmt_ids))
        self.assertEqual(len(frame.stmt_worklist), self.STMT_COUNT)


class TestP3IndexSpaceShift(unittest.TestCase):
    def test_frame_initialization_does_not_shift_loader_owned_p2_artifacts(self):
        source_status = {7: common_structure.StmtStatus(stmt_id=7, defined_symbol=0)}
        source_space = common_structure.SymbolStateSpace()
        source_space.add(
            common_structure.State(state_id=10, fields={"self": {0}})
        )
        source_def_use = common_structure.MethodDefUseSummary(method_id=7)
        source_summary = common_structure.MethodSummaryTemplate(
            key=7, parameter_symbols={1: {0}}
        )
        source_symbol_bits = common_structure.BitVectorManager()
        source_state_bits = common_structure.BitVectorManager()

        class Loader:
            def convert_method_id_to_unit_id(self, method_id):
                return 1

            def convert_unit_id_to_lang_name(self, unit_id):
                return "c"

            def convert_method_id_to_method_name(self, method_id):
                return "callee"

            def contain_symbol_state_space_p1(self, method_id):
                return True

            def get_method_cfg(self, method_id):
                graph = nx.DiGraph()
                graph.add_node(7)
                return graph

            def get_splitted_method_gir(self, method_id):
                return None, [], [SimpleNamespace(stmt_id=7, operation="return_stmt")]

            def get_method_defined_symbols_p2(self, method_id):
                return {}

            def get_method_defined_states_p2(self, method_id):
                return {}

            def get_stmt_status_p2(self, method_id):
                return source_status

            def get_symbol_state_space_p2(self, method_id):
                return source_space

            def get_symbol_bit_vector_p2(self, method_id):
                return source_symbol_bits

            def get_state_bit_vector_p2(self, method_id):
                return source_state_bits

            def get_method_summary_template(self, method_id):
                return source_summary

            def get_method_internal_callees(self, method_id):
                return []

            def get_method_def_use_summary(self, method_id):
                return source_def_use

            def get_symbol_state_space_summary_p2(self, method_id):
                return common_structure.SymbolStateSpace()

            def get_method_symbol_graph_p2(self, method_id):
                return nx.DiGraph()

        loader = Loader()
        frame = common_structure.ComputeFrame(method_id=7, loader=loader)
        frame_stack = common_structure.ComputeFrameStack()
        frame_stack.add(common_structure.MetaComputeFrame())
        frame_stack.add(frame)
        global_space = common_structure.SymbolStateSpace()
        global_space.add(common_structure.State(state_id=1))
        analysis = object.__new__(P3GlobalSemanticAnalysis)
        analysis.loader = loader
        analysis.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        analysis.options = SimpleNamespace(
            enable_p2=True, quiet=True, complete_graph=False
        )
        analysis.analyzed_method_list = set()
        analysis.event_manager = None
        analysis.resolver = object()
        analysis.path_manager = common_structure.PathManager()
        analysis.caller_unknown_callee_edge = {}
        analysis.call_site_analyze_counter = {}
        initialized = analysis.init_compute_frame(frame, frame_stack, global_space)

        self.assertIs(initialized, frame)
        self.assertEqual(source_status[7].defined_symbol, 0)
        self.assertEqual(source_space[0].fields, {"self": {0}})
        self.assertEqual(source_summary.parameter_symbols, {1: {0}})
        self.assertEqual(frame.stmt_id_to_status[7].defined_symbol, 1)
        self.assertEqual(frame.symbol_state_space[1].fields, {"self": {1}})
        self.assertEqual(frame.method_summary_template.parameter_symbols, {1: {1}})
        frame.method_def_use_summary.used_external_symbol_ids.add(99)
        self.assertEqual(source_def_use.used_external_symbol_ids, set())

    def test_frame_initialization_without_p2_copies_p1_artifacts_and_loads_cfg_once(self):
        source_status = {7: common_structure.StmtStatus(stmt_id=7, defined_symbol=0)}
        copy_count = [0]

        class CopyCountingSpace(common_structure.SymbolStateSpace):
            def copy(self):
                copy_count[0] += 1
                copied = CopyCountingSpace()
                for item in self.space:
                    copied.add(item.copy())
                copied.old_index_to_new_index = self.old_index_to_new_index.copy()
                copied.new_index_to_old_index = self.new_index_to_old_index.copy()
                return copied

        source_space = CopyCountingSpace()
        source_space.add(
            common_structure.State(state_id=10, fields={"self": {0}})
        )
        source_def_use = common_structure.MethodDefUseSummary(method_id=7)

        class Loader:
            def __init__(self):
                self.cfg_load_count = 0

            def convert_method_id_to_unit_id(self, method_id):
                return 1

            def convert_unit_id_to_lang_name(self, unit_id):
                return "c"

            def convert_method_id_to_method_name(self, method_id):
                return "callee"

            def contain_symbol_state_space_p1(self, method_id):
                return True

            def get_method_cfg(self, method_id):
                self.cfg_load_count += 1
                graph = nx.DiGraph()
                graph.add_node(7)
                return graph

            def get_splitted_method_gir(self, method_id):
                return None, [], [SimpleNamespace(stmt_id=7, operation="return_stmt")]

            def get_stmt_status_p1(self, method_id):
                return source_status

            def get_symbol_state_space_p1(self, method_id):
                return source_space.copy()

            def get_symbol_state_space_p1_copy(self, method_id):
                return source_space.copy()

            def get_method_internal_callees(self, method_id):
                return []

            def get_method_def_use_summary(self, method_id):
                return source_def_use

            def get_method_defined_symbols_raw_p1(self, method_id):
                return []

            def get_method_defined_states_p1(self, method_id):
                return {}

        loader = Loader()
        frame = common_structure.ComputeFrame(method_id=7, loader=loader)
        frame_stack = common_structure.ComputeFrameStack()
        frame_stack.add(common_structure.MetaComputeFrame())
        frame_stack.add(frame)
        global_space = common_structure.SymbolStateSpace()
        global_space.add(common_structure.State(state_id=1))
        analysis = object.__new__(P3GlobalSemanticAnalysis)
        analysis.loader = loader
        analysis.analysis_phase_id = ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
        analysis.options = SimpleNamespace(
            enable_p2=False, quiet=True, complete_graph=False
        )
        analysis.analyzed_method_list = set()
        analysis.event_manager = None
        analysis.resolver = object()
        analysis.path_manager = common_structure.PathManager()
        analysis.caller_unknown_callee_edge = {}
        analysis.call_site_analyze_counter = {}
        analysis.call_graph = None

        initialized = analysis.init_compute_frame(frame, frame_stack, global_space)

        self.assertIs(initialized, frame)
        self.assertEqual(source_status[7].defined_symbol, 0)
        self.assertEqual(source_space[0].fields, {"self": {0}})
        self.assertEqual(frame.stmt_id_to_status[7].defined_symbol, 1)
        self.assertEqual(frame.symbol_state_space[1].fields, {"self": {1}})
        frame.method_def_use_summary.used_external_symbol_ids.add(99)
        self.assertEqual(source_def_use.used_external_symbol_ids, set())
        self.assertEqual(loader.cfg_load_count, 1)
        self.assertEqual(copy_count[0], 1)

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


class TestSymbolStateSpaceAppend(unittest.TestCase):
    def test_remaps_every_reference_without_changing_source_elements(self):
        source_space = common_structure.SymbolStateSpace()
        source_space.add(
            common_structure.State(
                state_id=10,
                fields={"child": {1}},
                array=[{1}],
                tangping_elements={0},
            )
        )
        source_space.add(common_structure.Symbol(symbol_id=20, states={0}))
        target_space = common_structure.SymbolStateSpace()
        target_space.add(common_structure.State(state_id=1))

        target_space.append_space_copy(source_space)

        self.assertEqual(target_space[1].fields, {"child": {2}})
        self.assertEqual(target_space[1].array, [{2}])
        self.assertEqual(target_space[1].tangping_elements, {1})
        self.assertEqual(target_space[2].states, {1})
        self.assertEqual(source_space[0].fields, {"child": {1}})
        self.assertEqual(source_space[0].array, [{1}])
        self.assertEqual(source_space[0].tangping_elements, {0})
        self.assertEqual(source_space[1].states, {0})
        self.assertEqual(target_space.state_index_to_id, {0: 1, 1: 10})
        self.assertEqual(source_space.old_index_to_new_index, {0: 1, 1: 2})
        self.assertEqual(source_space.new_index_to_old_index, {1: 0, 2: 1})

    def test_rejects_dangling_reference_before_mutating_target_space(self):
        source_space = common_structure.SymbolStateSpace()
        source_space.add(common_structure.State(state_id=10))
        source_space.add(
            common_structure.State(state_id=11, fields={"missing": {2}})
        )
        target_space = common_structure.SymbolStateSpace()
        target_space.add(common_structure.State(state_id=1))

        with self.assertRaisesRegex(
            IndexError, "symbol state space reference index 2 is out of range"
        ):
            target_space.append_space_copy(source_space)

        self.assertEqual(len(target_space), 1)
        self.assertEqual(target_space.state_index_to_id, {0: 1})


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


class TestSourceCodeDecoding(unittest.TestCase):
    def test_invalid_utf8_in_c_string_does_not_skip_translation_unit(self):
        class CapturingASTParser:
            def __init__(self):
                self.source = None

            def parse(self, source):
                self.source = source
                return SimpleNamespace(root_node=object())

        class RecordingCParser:
            def __init__(self, options, unit_info):
                pass

            def parse_gir(self, root_node, statements):
                statements.append({"operation": "translation_unit"})

        ast_parser = CapturingASTParser()
        parser = GIRParser(
            SimpleNamespace(strict_parse_mode=True),
            event_manager=None,
            loader=None,
            output_path="",
        )
        language = SimpleNamespace(name="c", parser=RecordingCParser)

        with tempfile.NamedTemporaryFile(suffix=".c") as source_file:
            source_file.write(b'int main(void) { char *s = "\x82"; return 0; }')
            source_file.flush()
            with patch.object(parser, "obtain_ast_parser", return_value=ast_parser):
                statements = parser.parse(
                    SimpleNamespace(), source_file.name, "c", [language]
                )

        self.assertEqual(statements, [{"operation": "translation_unit"}])
        self.assertIn(b"int main", ast_parser.source)
        ast_parser.source.decode("utf-8")


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
