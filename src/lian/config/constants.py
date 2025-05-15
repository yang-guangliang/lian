#!/usr/bin/env python3

from lian.util import util

LANG_EXTENSIONS = {
    "c"             : [".c", ".h", ".i"],
    "cpp"           : [".cpp", ".cxx", ".cc", ".h", ".hh", ".hpp", ".ii"],
    "csharp"        : [".cs"],
    "rust"          : [".rs"],
    "mir"           : [".mir"],
    "go"            : [".go"],
    "java"          : [".java"],
    "javascript"    : [".js"],
    "typescript"    : [".ts"],
    "kotlin"        : [".kt"],
    "scala"         : [".scala"],
    "llvm"          : [".ll"],
    "python"        : [".py"],
    "ruby"          : [".rb"],
    "smali"         : [".smali"],
    "swift"         : [".swift"],
    "php"           : [".php"],
    "codeql"        : [".ql"],
    "ql"            : [".ql"],
    "abc"           : [".txt"],
    "safe"          : [".safe"], 
    "arkts"         : [".ets"],
}

EXTENSIONS_LANG = {}

def update_lang_extensions(lang_list):
    global LANG_EXTENSIONS
    global EXTENSIONS_LANG

    # Adjust the attribution of .h files
    if "c" in lang_list:
        if ".h" in LANG_EXTENSIONS["cpp"]:
            LANG_EXTENSIONS["cpp"].remove(".h")
    elif "cpp" in lang_list:
        if ".h" in LANG_EXTENSIONS["c"]:
            LANG_EXTENSIONS["c"].remove(".h")

    for lang, exts in LANG_EXTENSIONS.items():
        for each_ext in exts:
            if each_ext not in EXTENSIONS_LANG:
                EXTENSIONS_LANG[each_ext] = lang

CLASS_DECL_OPERATION = {
    "class_decl",
    "record_decl",
    "interface_decl",
    "enum_decl",
    "struct_decl",
}

NAMESPACE_DECL_OPERATION = {
    "namespace_decl"
}

IMPORT_OPERATION = {
    "import_stmt",
    "from_import_stmt"
}

METHOD_DECL_OPERATION = {
    "method_decl"
}

FOR_STMT_OPERATION = {
    "for_stmt"
}

VARIABLE_DECL_OPERATION = {
    "variable_decl"
}

PARAMETER_DECL_OPERATION = {
    "parameter_decl"
}

BLOCK_OPERATION = {
    "for_stmt",
    "forin_stmt",
}

CALL_OPERATION = {
    "call_stmt"
}

EXPORT_STMT_OPERATION = {
    "export_stmt"
}

RETURN_STMT_OPERATION = {
    "return_stmt"
}

SUMMARY_GENERAL_SYMBOL_ID = util.SimpleEnum({
    "RETURN_SYMBOL_ID" : -28,
})

EventKind = util.SimpleEnum({
    "NONE"                                          : 0,
    "MOCK_SOURCE_CODE_READY"                        : 1,
    "ORIGINAL_SOURCE_CODE_READY"                    : 2,
    "UNFLATTENED_GIR_LIST_GENERATED"              : 3,
    "GIR_LIST_GENERATED"                          : 4,
    "GIR_DATA_MODEL_GENERATED"                    : 5,
    "ENTRY_POINT_ANALYSIS_BEFORE"                   : 6,
    "ENTRY_POINT_ANALYSIS_AFTER"                    : 7,
    "UNIT_SCOPE_HIERARCHY_GENERATED"                : 8,
    "CONTROL_FLOW_GRAPH_GENERATED"                  : 9,

    "P1STMT_DEF_USE_ANALYSIS_BEFORE"                : 20,
    "P1STMT_DEF_USE_ANALYSIS_AFTER"                 : 21,
    "P1METHOD_DEF_USE_SUMMARY_GENERATED"            : 22,

    "P2STATE_FIELD_READ_BEFORE"                     : 40,
    "P2STATE_FIELD_READ_AFTER"                      : 41,
    "P2STATE_GENERATE_EXTERNAL_STATES"              : 42,
    "P2STATE_NEW_OBJECT_BEFORE"                     : 43,
    "P2STATE_BUILTIN_FUNCTION_BEFORE"               : 44,
    "P2STATE_NEW_OBJECT_AFTER"                      : 45,
    "P2STATE_EXTERN_CALLEE"                         : 46,
})

ConfigurationItemKind = util.SimpleEnum({
    "ARG"               : 0,
    "RETURN"            : 1,
    "THIS"              : 2,
})

LangKind = util.SimpleEnum({
    "C"                 : 0,
    "CPP"               : 1,
    "CSHARP"            : 2,
    "RUST"              : 3,
    "GO"                : 4,
    "JAVA"              : 5,
    "JAVASCRIPT"        : 6,
    "TYPESCRIPT"        : 7,
    "KOTLIN"            : 8,
    "SCALA"             : 9,
    "LLVM"              : 10,
    "PYTHON"            : 11,
    "RUBY"              : 12,
    "SMALI"             : 13,
    "SWIFT"             : 14,
    "PHP"               : 15,
    "CODEQL"            : 16,
    "QL"                : 17,
    "ABC"               : 18,
})

SymbolKind = util.SimpleEnum({
    'MODULE'                : 0,
    'UNIT_SYMBOL'           : 1,
    'PARENT_MODULE'         : 2,
    'IMPORT'                : 3,
    'VARIABLE'              : 4,
    'METHOD'                : 5,
    'CLASS'                 : 6,
    'PARENT_CLASS'          : 7,
    'FIELD'                 : 8,
    'CLASS_METHOD'          : 9,
    'PACKAGE'               : 10,
    'MEMBER_METHOD'         : 11,
    'MODULE_SYMBOL'         : 12,
})

MethodSummarySymbolKind = util.SimpleEnum({
    'PARARMETER_SYMBOL'             : 1,
    'DEFINED_EXTERNAL_SYMBOL'       : 2,
    'USED_EXTERNAL_SYMBOL'          : 3,
    'RETRUN_SYMBOL'                 : 4,
    'DYNAMIC_CALL'                  : 5,
    'DIRECT_CALL'                   : 6
})


ControlFlowKind = util.SimpleEnum({
    "EMPTY"                 : 0,
    "IF_TRUE"               : 1,
    "IF_FALSE"              : 2,
    "FOR_CONDITION"         : 3,
    "LOOP_TRUE"             : 4,
    "LOOP_FALSE"            : 5,
    "LOOP_BACK"             : 6,
    "BREAK"                 : 7,
    "CONTINUE"              : 8,
    "RETURN"                : 9,
    "CATCH_TRUE"            : 10,
    "CATCH_FALSE"           : 11,
    "CATCH_FINALLY"         : 12,
    "PARAMETER_UNINIT"      : 13,
    "PARAMETER_INIT"        : 14,

    "EXIT"                  : 15,
    "YIELD"                 : 16,
})

SymbolDependencyKind = util.SimpleEnum({
    "REGULAR"               : 0,
    "EXPLICITLY_DEFINED"    : 1,
    "EXPLICITLY_USED"       : 2,
    "IMPLICITLY_DEFINED"    : 3,
    "IMPLICITLY_USED"       : 4
})

# """A class that represents the possible value types for a state.
# """
StateTypeKind = util.SimpleEnum({
    "EMPTY"                 : 0,
    "REGULAR"               : 1,
    "UNSOLVED"              : 2,
    "UNINIT"                : 3,
    "ANYTHING"              : 4,
})

ExternalKeyStateType = util.SimpleEnum({
    "CALL"                  : 0,
    "ADDR"                  : 1,
    "ARRAY"                 : 2,
    "FIELD"                 : 3,
    "EMPTY"                 : 4,
})

BuiltinOrCustomDataType = util.SimpleEnum({
    "BUILTIN"               : 0,
    "CUSTOM"                : 1,
})

ScopeKind = util.SimpleEnum({
    "PACKAGE_STMT"                  : 0,
    "IMPORT_STMT"                   : 1,
    "INCLUDE_STMT"                  : 2,
    "VARIABLE_DECL"                 : 3,
    "PARAMETER_DECL"                : 4,
    "CALL_STMT"                     : 5,
    "EXPORT_STMT"                   : 6,

    "BLOCK_SCOPE"                   : 10,
    "METHOD_SCOPE"                  : 11,
    "CLASS_SCOPE"                   : 12,
    "NAMESPACE_SCOPE"               : 13,
    "UNIT_SCOPE"                    : 14,
    "BUILTIN_SCOPE"                 : 15,
    "FOR_SCOPE"                     : 16
})

AnalysisPhaseName = util.SimpleEnum({
    "ScopeHierarchy"            : "scope_hierarchy",
    "TypeHierarchy"             : "type_hierarchy",
    "ControlFlowGraph"          : "control_flow",
    "SymbolFlowGraph"           : "symbol_flow",
    "StateFlowGraph"            : "state_flow",
    "MethodSummary"             : "method_summary",
    "AbstractCompute"           : "abstract_compute",
    "CallGraph"                 : "call_graph",
    "SemanticSummaryGeneration" : "semantic_summary_generation",
    "GlobalAnalysis"            : "global_analysis",
})

BasicCallGraphNodeKind = util.SimpleEnum({
    "DYNAMIC_METHOD"      : -1,
    "ERROR_METHOD"        : -2,
})



DataTypeCorrelationKind = util.SimpleEnum({
    "alias"               : 0,
    "inherit"             : 1,
})

SymbolOrState = util.SimpleEnum({
    "SYMBOL"                : 0,
    "STATE"                 : 1,
    "EXTERNAL_KEY_STATE"    : 2,
    "UNKNOWN"               : 3,
})

AccessPointKind = util.SimpleEnum({
    "TOP_LEVEL"                     : 0,
    "ADDR_OF"                       : 1,
    "MEM_READ"                      : 2,
    "FORIN_ELEMENT"                 : 3,
    "ELEMENT_OF"                    : 4,
    "NEW_OBJECT"                    : 5,
    "BINARY_ASSIGN"                 : 8,
    "FIELD_NAME"                    : 9,
    "FIELD_ELEMENT"                 : 10,
    "ARRAY_INDEX"                   : 11,
    "ARRAY_ELEMENT"                 : 12,
    "CALL_RETURN"                   : 13,
    "EXTERNAL"                      : 14,
    "REQUIRED_MODULE"               : 15,
    "BUILTIN_METHOD"                : 18,
    "NAMESPACE"                     : 19,
})

RuleKind = util.SimpleEnum({
    "RULE"                       : 0,
    "CODE"                       : 1,
    "MODEL"                      : 2,
})

ConditionStmtPathFlag = util.SimpleEnum({
    "NO_PATH"                       : 0,  # 00
    "TRUE_PATH"                     : 1,  # 01
    "FALSE_PATH"                    : 2,  # 10
    "ANY_PATH"                      : 3,  # 11
})

LoaderQueryEntry = util.SimpleEnum({
    'control_flow_graph'            : 1,
    'symbol_dependency_graph'       : 2,
    'stmt_status'                   : 3,
    'symbols_states_space'          : 4,
    'method_summary'                : 5,
    'gir_ir'                      : 6,
    'scope_space'                   : 7,
})

CalleeType = util.SimpleEnum({
    "DIRECT_CALLEE"                 : 0,
    "DYNAMIC_CALLEE"                : 1,
    "ERROR_CALLEE"                  : 2,
})

ExportNodeType = util.SimpleEnum({
    "MODULE_UNIT"                   : 0,
    "MODULE_DIR"                    : 1,
    "REGULAR_SYMBOL"                : 2,
    "UNKNOWN_IMPORT"                : 3,
})

LianInternal = util.SimpleEnum({
    # Constants
    "TRUE"                          : "true",
    "FALSE"                         : "false",
    "NULL"                          : "null",
    "UNDEFINED"                     : "undefined",

    "I8"                            : "i8",
    "I16"                           : "i16",
    "I32"                           : "i32",
    "I64"                           : "i64",
    "U8"                            : "u8",
    "U16"                           : "u16",
    "U32"                           : "u32",
    "U64"                           : "u64",
    "F32"                           : "f32",
    "F64"                           : "f64",
    "F128"                          : "f128",

    # Data Types
    "BOOL"                          : "%bool",
    "INT"                           : "%int",
    "FLOAT"                         : "%float",
    "POINTER"                       : "%pointer",
    "STRING"                        : "%string",
    "ARRAY"                         : "%array",
    "TUPLE"                         : "%tuple",
    "RECORD"                        : "%record",
    "OBJECT"                        : "%object",
    "REQUIRED_MODULE"               : "%require",

    # Prefixes
    "VARIABLE_DECL_PREF"            : "%vv",
    "DEFAULT_VALUE_PREF"            : "%dvv",
    "METHOD_DECL_PREF"              : "%mm",
    "CLASS_DECL_PREF"               : "%cc",

    # Builtin Keywords
    "THIS"                          : "%this",
    "SELF"                          : "%this",
    "PARENT"                        : "%parent",
    "SUPER"                         : "%parent",
    "CLASS"                         : "%class",

    # Data Types
    "PARAMETER_DECL"                : "%parameter_decl",
    "METHOD_DECL"                   : "%method_decl",
    "GENERATOR_DECL"                : "%generator_decl",
    "VARIABLE_DECL"                 : "%variable_decl",
    "CLASS_DECL"                    : "%class_decl",
    "UNIT"                          : "%unit",
    "DIR"                           : "%dir",

    # Builtin Methods
    "UNIT_INIT"                     : "%unit_init",
    "CLASS_INIT"                    : "%class_init",
    "CLASS_STATIC_INIT"             : "%class_sinit",

    # Builtin Parameters and Args Types
    "PACKED_POSITIONAL_PARAMETER"   : "%packed_pos_pmt",
    "PACKED_NAMED_PARAMETER"        : "%packed_named_pmt",
    "POSITIONAL_ONLY_PARAMETER"     : "%pos_pmt",
    "KEYWORLD_ONLY_PARAMETER"       : "%keyword_pmt",
    "PACKED_POSTIONAL_ARGUMENT"     : "%pos_arg",
    "PACKED_NAMED_ARGUMENT"         : "%named_arg",

    #Prototype
    "PROTOTYPE"                     : "%prototype",
    "PROTO"                          : "%__proto__",
})

JsPrototype = util.SimpleEnum({
    "PROTOTYPE"                      : "prototype",
    "PROTO"                          : "__proto__",
    "CONSTRUCTOR"                     : "constructor",

})

IncrementalBackupType = util.SimpleEnum({
    "EMPTY"                       : -1,
    "GIR"                           : 0,
    "SEMANTIC_P1"                   : 1,
    "SEMANTIC_P2"                   : 2,
    "SEMANTIC_P3"                   : 3
})
