import os



# from lian.util import util
ROOT_DIR    = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
LIAN_DIR    = os.path.join(ROOT_DIR, "lian/src")
TAINT_DIR   = os.path.join(ROOT_DIR, "src")

#DEFAULT_WORKSPACE       = os.path.join(ROOT_DIR, "tests/taint_workspace")

MAX_METHOD_CALL_COUNT   = 30
TAINT_SOURCE            = os.path.join(ROOT_DIR, "rules/hongmeng/src.yaml")
TAINT_SINK            = os.path.join(ROOT_DIR, "rules/hongmeng/sink.yaml")
TAINT_PROPAGATION            = os.path.join(ROOT_DIR, "rules/hongmeng/prop.yaml")


NO_TAINT                = 0
MAX_STMT_TAINT_ANALYSIS_COUNT = 3
ANY_LANG                                    = "%"

# RULE_KIND = util.SimpleEnum({
#     "SOURCE": 1,
#     "SINK": 2,
#     "propagation": 3,
# })