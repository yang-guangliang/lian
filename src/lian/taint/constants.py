from lian.util import util

SFG_EDGE_KIND = util.SimpleEnum({
    "REGULAR"                   : 0,
    "SYMBOL_IS_DEFINED"         : 1,
    "SYMBOL_IS_USED"            : 2,
    "SYMBOL_FLOW"               : 3,
    "INDIRECT_SYMBOL_FLOW"      : 4,
    "SYMBOL_STATE"              : 5,
    "INDIRECT_SYMBOL_STATE"     : 6,
    "STATE_INCLUSION"           : 7,
    "INDIRECT_STATE_INCLUSION"  : 8,
    "CALL_RETURN"               : 9,
    "STATE_COPY"                : 10,
    "STATE_IS_USED"             : 11,
})

SFG_NODE_KIND = util.SimpleEnum({
    "REGULAR"                   : 0,
    "STMT"                      : 1,
    "SYMBOL"                    : 2,
    "STATE"                     : 3,
})

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
