#!/usr/bin/env python3

import dataclasses
from lian.config import config
from lian.config.constants import (
    RuleKind
)

@dataclasses.dataclass
class Rule:
    """
    rule_id                 : id of rule
    rule_type               : code or rule

    lang                    : language
    name                    : name of class_name.method_name
    args                    : arguments of args

    A rule:
        how to write a rule of src/dst?
            - %this         : access this
            - %arg[0-9]+    : access argument
            - %return       : access return value
            - .             : access internal field
        should unset the taint?
            - unset         : unset the taint

    A mock method:
        how to write a mock method using source code?
            - mock_path     : path of source code
            - mock_id       : stmt_id of mock method
    """
    rule_id:int             = -1

    kind: int               = RuleKind.RULE

    lang: str               = config.ANY_LANG
    class_name: str         = ""
    method_name: str        = ""
    args: str               = ""

    src: list               = dataclasses.field(default_factory=list)
    dst: list               = dataclasses.field(default_factory=list)
    unset:bool              = False

    mock_path: str          = ""
    mock_id: int            = -1

    model_method: object    = None

    def __repr__(self):
        return f"Rule(rule_id={self.rule_id}, kind={self.kind}, lang={self.lang}, class_name={self.class_name}, method_name={self.method_name}, args={self.args}, src={self.src}, dst={self.dst}, unset={self.unset}, mock_path={self.mock_path}, mock_id={self.mock_id}, model_method={self.model_method})"

    def to_dict(self):
        return {
            "rule_id"             : self.rule_id,
            "kind"                : self.kind,
            "lang"                : self.lang,
            "class_name"          : self.class_name,
            "method_name"         : self.method_name,
            "args"                : self.args,
            "src"                 : self.src,
            "dst"                 : self.dst,
            "unset"               : self.unset,
            "mock_path"           : self.mock_path,
            "mock_id"             : self.mock_id,
            "model_method"        : self.model_method
        }



