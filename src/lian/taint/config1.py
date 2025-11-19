import os



# from lian.util import util
ROOT_DIR    = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
LIAN_DIR    = ROOT_DIR
TAINT_DIR   = os.path.join(ROOT_DIR, "lian/taintv2")

#DEFAULT_WORKSPACE       = os.path.join(ROOT_DIR, "tests/taint_workspace")

MAX_METHOD_CALL_COUNT   = 30
TAINT_SOURCE            = os.path.join(TAINT_DIR, "rules/src.yaml")
TAINT_SINK            = os.path.join(TAINT_DIR, "rules/sink.yaml")
TAINT_PROPAGATION            = os.path.join(TAINT_DIR, "rules/prop.yaml")


NO_TAINT                = 0
MAX_STMT_TAINT_ANALYSIS_COUNT = 3
ANY_LANG                                    = "%"

# RULE_KIND = util.SimpleEnum({
#     "SOURCE": 1,
#     "SINK": 2,
#     "propagation": 3,
# })
