#!/usr/bin/env python3

import os,sys
import numpy as np

scope_space_schema = [
    "unit_id",
    "stmt_id",
    "parent_stmt_id",
    "scope_kind",
    "package_stmt",
    "import_stmt",
    "variable_decl",
    "method_decl",
    "class_decl",
    "calls"
]

stmt_id_to_scope_id_schema = [
    "stmt_id",
    "scope_id"
]

class_id_to_name_schema = [
    "class_id",
    "name"
]

method_id_to_unit_id_schema = [
    "method_id",
    "unit_id"
]

unit_id_to_stmt_id_schema = [
    "unit_id",
    "min_stmt_id",
    "max_stmt_id"
]

one_to_many_schema = [
    "one",
    "many"
]

unit_id_to_method_id_schema = [
    "unit_id",
    "method_ids"
]

class_id_to_class_name_schema = [
    "class_id",
    "class_name"
]

method_id_to_method_name_schema = [
    "method_name",
    "method_id",
]

class_id_to_method_id_schema = [
    "class_id",
    "method_ids"
]

class_id_to_field_id_schema = [
    "class_id",
    "field_ids"
]

unit_id_to_class_id_schema = [
    "unit_id",
    "class_ids"
]

unit_id_to_namespace_id_schema = [
    "unit_id",
    "namespace_ids"
]

unit_id_to_variable_ids_schema = [
    "unit_id",
    "variable_ids"
]

unit_id_to_import_stmt_id_schema = [
    "unit_id",
    "import_stmt_ids"
]

method_id_to_parameter_id_schema = [
    "method_id",
    "parameter_ids"
]

class_id_to_methods_schema = [
    "unit_id",
    "class_id",
    "name",
    "stmt_id",
]

control_flow_graph_schema = {
    "method_id"                     : 0,
    "src_stmt_id"                   : 0,
    "dst_stmt_id"                   : 0,
    "control_flow_type"             : 0
}



basic_call_graph_schema = [
    "method_id",
    "callee",
    "call_type"
]

symbol_graph_schema_p2 = [
    "method_id",
	"used_symbol_stmt_id",
	"used_symbol_index",
	"used_symbol_id",
	"stmt_id",
	"defined_symbol_stmt_id",
	"defined_symbol_index",
	"defined_symbol_id",
    "edge_type"
]

state_flow_graph_schema_p2 = [
    "method_id",
    "source_id",
    "edge_type",
    "edge_stmt_id",
    "dest_id"
]



call_graph_schema = {
    "src_method_id"                 : 0,
    "src_stmt_id"                   : 0,
    "dst_method_id"                 : 0,
    "call_type"                     : 0
}

call_path_schema = [
    "index",
    "call_path"
]

method_summary_schema = [
    'method_id',
    'parameter_symbols',
    'defined_external_symbols',
    'used_external_symbols',
    'return_symbols'
]

abstract_method_graph_schema = [
    "unit_id",
    "method_id",
    "is_init",
    "operation",
    "in1",
    "id1",
    "state1",
    "in2",
    "id2",
    "state2",
    "out",
    "out_id",
    "out_state"
]


stmt_status_schema = [
    "method_id",
    "callees",
    "stmt_id",
    "defined_symbol",
    "used_symbols",
    "field",
    "operation",
    "in_bits",
    "out_bits",
]

symbol_state_space_schema = [
    "method_id",
    # "callees",
    "stmt_id",
    "index",
    "symbol_or_state",
    "source_unit_id",
    "symbol_id",
    "name",
    "states",
    "default_data_type",
    "state_id",
    "state_type",
    "data_type",
    "array",
    "array_tangping_flag",
    "fields",
    "value" # 少这一行，dataframe中打印不出value
]

call_graph_schema = [
    "caller",
    "callee",
    "call_site" # at which stmt_id caller calls callee
]

loader_indexing_schema = [
    "item_id",
    "bundle_id"
]


