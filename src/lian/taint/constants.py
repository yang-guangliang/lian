import sys
import taint.config1 as config

sys.path.extend([config.LIAN_DIR, config.TAINT_DIR])

from lian.util import util

TAG_KEYWORD = util.SimpleEnum({
    "RETURN"     : r"\%return",
    "ARG0"       : r"\%arg0",
    "ARG1"       : r"\%arg1",
    "ARG2"       : r"\%arg2",
    "ARG3"       : r"\%arg3",
    "ARG4"       : r"\%arg4",
    "TARGET"     : r"\%target",
    "RECEIVER"   : r"\%receiver",
    "FIELD"      : r"\%field",
    "THIS"       : r"\%this",   
    "ANYNAME"    : r"\%anyname",
})
EventKind = util.SimpleEnum({
    "TAINT_BEFORE"                                          : 0,
    "SINK_BEFORE"                                           : 1,
    "PROP_BEFORE"                                           : 2,
    "PROP_AFTER"                                            : 3,
    "PROP_FOREACH_ITEM"                                     : 4,
    "CALL_BEFORE"                                           : 5,
})