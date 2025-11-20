#!/usr/bin/env python3

# "lian/src/lian/externs/extern_rule.py"

# add source tag
# - interface: add_tag(tag, value)
# - .yaml config

import dataclasses
import yaml
import config as config

class Source:
    def __init__(self, name, tag, value):
        self.name = name
        self.tag = tag
        self.value = value

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
    """
    rule_id:int             = -1

    kind: int               = -1
    lang: str               = config.ANY_LANG
    name: str               = ""
    operation: str          = ""
    receiver: str           = ""
    field: list             = dataclasses.field(default_factory=list)
    target: str             = ""
    args: list              = dataclasses.field(default_factory=list)
    tag:list                = dataclasses.field(default_factory=list)
    src: list               = dataclasses.field(default_factory=list)
    dst: list               = dataclasses.field(default_factory=list)
    unset:bool              = False

    # mock_path: str          = ""
    # mock_id: int            = -1

    # model_method: object    = None

    # def __repr__(self):
    #     return f"Rule(rule_id={self.rule_id}, kind={self.kind}, lang={self.lang}, class_name={self.class_name}, method_name={self.method_name}, args={self.args}, src={self.src}, dst={self.dst}, unset={self.unset}, mock_path={self.mock_path}, mock_id={self.mock_id}, model_method={self.model_method})"

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "kind": self.kind,
            "lang": self.lang,
            "name": self.name,
            "operation": self.operation,
            "receiver": self.receiver,
            "field": self.field,
            "args": self.args,
            "tag": self.tag,
            "src": self.src,
            "dst": self.dst,
            "unset": self.unset,
        }



class RuleManager:
    def __init__(self):
        self.all_sources = []
        self.all_sinks = []
        self.all_propagations = []
        self.init()
    def init(self):
        print(config.TAINT_SOURCE)
        with open(config.TAINT_SOURCE, 'r') as file:
            data = yaml.safe_load(file)
            rule_kind = data["rule_kind"]
            lang = data["lang"]
            rules = data["rules"]
            for rule in rules:
                new_rule = Rule(kind=rule_kind, 
                                lang=lang, 
                                name=rule.get("name", None),
                                operation=rule.get("operation", None), 
                                receiver=rule.get("receiver", None), 
                                field=rule.get("field", []),
                                target=rule.get("target", None),
                                args=rule.get("args", None),
                                tag=rule.get("tag", None), 
                                src=rule.get("src", None), 
                                dst=rule.get("dst", None), 
                                unset=rule.get("unset", None))
                self.all_sources.append(new_rule)
        with open(config.TAINT_SINK, 'r') as file:
            data = yaml.safe_load(file)
            rule_kind = data["rule_kind"]
            lang = data["lang"]
            rules = data["rules"]
            
            for rule in rules:

                new_rule = Rule(kind=rule_kind, 
                                lang=lang, 
                                name=rule.get("name", None),
                                operation=rule.get("operation", None), 
                                receiver=rule.get("receiver", None),
                                field=rule.get("field", []),
                                target=rule.get("target", None),
                                args=rule.get("args", None), 
                                tag=rule.get("tag", None), 
                                src=rule.get("src", None), 
                                dst=rule.get("dst", None), 
                                unset=rule.get("unset", None))
                self.all_sinks.append(new_rule)

        with open(config.TAINT_PROPAGATION, 'r') as file:
            data = yaml.safe_load(file)
            rule_kind = data["rule_kind"]
            lang = data["lang"]
            rules = data["rules"]
            for rule in rules:
                new_rule = Rule(kind=rule_kind, 
                                lang=lang, 
                                name=rule.get("name", None),
                                operation=rule.get("operation", None), 
                                receiver=rule.get("receiver", None), 
                                field=rule.get("field", []),
                                target=rule.get("target", None),
                                args=rule.get("args", None),
                                tag=rule.get("tag", None), 
                                src=rule.get("src", None), 
                                dst=rule.get("dst", None), 
                                unset=rule.get("unset", None))
                self.all_propagations.append(new_rule)
    
    def add_rule(self, rule_type, rule):
        pass

    def delete_rule(self, rule_type, rule):
        pass
