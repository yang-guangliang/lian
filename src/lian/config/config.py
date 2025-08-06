
import os
import platform

EMPTY                                       = 0
START_INDEX                                 = 100
DEBUG_FLAG                                  = False
STRING_MAX_LEN                              = 200
MAX_PRIORITY                                = 100
MIN_ID_INTERVAL                             = 10
BUILTIN_SYMBOL_START_ID                     = -101
BUILTIN_THIS_SYMBOL_ID                      = -9
BUILTIN_OBJECT_SYMBOL_ID                    = -8

RULE_START_ID                               = 10

MAX_ROWS                                    = 40 * 10000
MAX_BENCHMARK_TARGET                        = 10_000
MAX_STMT_STATE_ANALYSIS_ROUND               = 4

FIRST_ROUND                                 = 0
FIRST_GLOBAL_ROUND                          = 1

ANY_LANG                                    = "%"

DEFAULT_WORKSPACE                           = "lian_workspace"
MODULE_SYMBOLS_FILE                         = "module_symbols"
SOURCE_CODE_DIR                             = "src"
EXTERNS_DIR                                 = "externs"
BASIC_DIR                                   = "basic"
SEMANTIC_DIR_P1                             = "semantic_p1"
SEMANTIC_DIR_P2                             = "semantic_p2"
SEMANTIC_DIR_P3                             = "semantic_p3"

ROOT_DIR                                    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

DEFAULT_SO_PATH         = "lib/langs_linux.so"
# if platform.system() == 'Darwin':
#     if platform.machine() == 'arm64':
#         DEFAULT_SO_PATH = ""
LANG_SO_PATH            = os.path.join(ROOT_DIR, DEFAULT_SO_PATH)

SRC_LIAN_DIR                                = os.path.join(ROOT_DIR, "src/lian")
EXTERNS_MOCK_CODE_DIR                       = os.path.join(SRC_LIAN_DIR, "externs/mock")
EXTERN_RULES_DIR                            = os.path.join(SRC_LIAN_DIR, "externs/rules")
EXTERN_MODEL_CODE_DIR                       = os.path.join(SRC_LIAN_DIR, "externs/modeling")
MOCK_METHOD_NAME_SEPARATOR                  = "_1_"

BUNDLE_CACHE_CAPACITY                       = 10
LRU_CACHE_CAPACITY                          = 10000
GIR_CACHE_CAPACITY                          = LRU_CACHE_CAPACITY / 2

METHOD_HEADER_CACHE_CAPABILITY              = 10000
METHOD_BODY_CACHE_CAPABILITY                = 1000
STMT_SCOPE_CACHE_CAPABILITY                 = 1000

MODULE_SYMBOLS_PATH                         = "module_symbols"
LOADER_INDEXING_PATH                        = "indexing"
GIR_BUNDLE_PATH                             = "gir"
CFG_BUNDLE_PATH                             = "cfg"
SCOPE_HIERARCHY_BUNDLE_PATH                 = "scope_hierarchy"
METHOD_INTERNAL_CALLEES_PATH                = "method_internal_callees"
SYMBOL_NAME_TO_SCOPE_IDS_PATH               = "symbol_name_to_scope_ids"
SCOPE_ID_TO_SYMBOL_INFO_PATH                = "scope_to_symbol_info"
SCOPE_ID_TO_AVAILABLE_SCOPE_IDS_PATH        = "scope_to_available_scope_ids"

EXTERNAL_SYMBOL_ID_COLLECTION_PATH          = "external_symbol_id_collection"
UNIQUE_SYMBOL_IDS_PATH                      = "unique_symbol_ids"

CALL_STMT_ID_TO_INFO_PATH                   = "call_stmt_id_to_info"
CALL_STMT_ID_TO_CALL_FORMAT_INFO_PATH       = "call_stmt_format"
METHOD_ID_TO_METHOD_DECL_FORMAT_PATH        = "method_decl_format"

UNIT_ID_TO_STMT_ID_PATH                     = "unit_to_stmt_id"
UNIT_ID_TO_METHOD_ID_PATH                   = "unit_to_method_id"
UNIT_ID_TO_CLASS_ID_PATH                    = "unit_to_class_id"
UNIT_ID_TO_NAMESPACE_ID_PATH                = "unit_to_namespace_id"
UNIT_ID_TO_VARIABLE_ID_PATH                 = "unit_to_variable_id"
UNIT_ID_TO_IMPORT_STMT_ID_PATH              = "unit_to_import_stmt"
METHOD_ID_TO_PARAMETER_ID_PATH              = "method_to_parameter_id"
CLASS_ID_TO_METHOD_ID_PATH                  = "class_to_method_id"
CLASS_ID_TO_FIELD_ID_PATH                   = "class_to_field_id"
CLASS_METHODS_PATH                          = "class_methods"
CLASS_ID_TO_CLASS_NAME_PATH                 = "class_id_to_name"
METHOD_ID_TO_METHOD_NAME_PATH               = "method_id_to_name"

CALL_GRAPH_BUNDLE_PATH_P1                   = "call_graph_p1"
CALL_GRAPH_BUNDLE_PATH_P2                   = "call_graph_p2"
CALL_PATH_BUNDLE_PATH_P3                    = "call_path_p3"

ENTRY_POINTS_PATH                           = "entry_points"
SYMBOL_BIT_VECTOR_MANAGER_BUNDLE_PATH_P1    = "symbol_bit_vector_p1"
SYMBOL_BIT_VECTOR_MANAGER_BUNDLE_PATH_P2    = "symbol_bit_vector_p2"
SYMBOL_BIT_VECTOR_MANAGER_BUNDLE_PATH_P3    = "symbol_bit_vector_p3"
STATE_BIT_VECTOR_MANAGER_BUNDLE_PATH_P1     = "state_bit_vector_p1"
STATE_BIT_VECTOR_MANAGER_BUNDLE_PATH_P2     = "state_bit_vector_p2"
STATE_BIT_VECTOR_MANAGER_BUNDLE_PATH_P3     = "state_bit_vector_p3"
STMT_STATUS_BUNDLE_PATH_P1                  = "stmt_status_p1"
STMT_STATUS_BUNDLE_PATH_P2                  = "stmt_status_p2"
STMT_STATUS_BUNDLE_PATH_P3                  = "stmt_status_p3"
SYMBOL_STATE_SPACE_BUNDLE_PATH_P1           = "s2space_p1"
SYMBOL_STATE_SPACE_BUNDLE_PATH_P2           = "s2space_p2"
SYMBOL_STATE_SPACE_BUNDLE_PATH_P3           = "s2space_p3"
SYMBOL_STATE_SPACE_SUMMARY_BUNDLE_PATH_P2   = "space_summary_p2"
SYMBOL_STATE_SPACE_SUMMARY_BUNDLE_PATH_P3   = "space_summary_p3"
SYMBOL_TO_DEFINE_PATH                       = "symbol_to_define"
SYMBOL_TO_DEFINE_PATH_P2                    = "symbol_to_define_p2"
SYMBOL_TO_DEFINE_PATH_P3                    = "symbol_to_define_p3"
STATE_TO_DEFINE_PATH_P1                     = "state_to_define_p1"
STATE_TO_DEFINE_PATH_P2                     = "state_to_define_p2"
SYMBOL_TO_USE_PATH                          = "symbol_to_use"
GROUPED_METHODS_PATH                        = "grouped_methods"

UNIT_EXPORT_PATH                            = "unit_export_symbols"
IMPORT_GRAPH_PATH                           = "import_graph"

TYPE_GRAPH_PATH                             = "type_graph"

SYMBOL_GRAPH_BUNDLE_PATH                    = "symbol_graph"
SYMBOL_GRAPH_BUNDLE_PATH_P3                 = "symbol_graph_p3"
CALLEE_PARAMETER_MAPPING_BUNDLE_PATH_P2     = "callee_parameter_mapping_p2"
CALLEE_PARAMETER_MAPPING_BUNDLE_PATH_P3     = "callee_parameter_mapping_p3"

METHOD_DEF_USE_SUMMARY_PATH                 = "method_def_use_summary"
METHOD_SUMMARY_TEMPLATE_PATH                = "method_summary_template"
METHOD_SUMMARY_INSTANCE_PATH                = "method_summary_instance"

UNSOLVED_SYMBOL_NAME                        = "%%%%unsolved_symbols"
POSITIVE_GIR_INTERVAL                       = 10000
DEFAULT_MAX_GIR_ID                          = 100000000

