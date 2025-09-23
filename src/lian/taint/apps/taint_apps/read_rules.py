import re
import struct
import ast
import dataclasses
import taint.apps.event_return as er
from taint import config1 as config
from taint.apps.app_template import EventData
from taint.taint_structs import TagBitVectorManager,TaintEnv
from taint.constants import TAG_KEYWORD
from taint import util
from lian.semantic.semantic_structs import (
    Symbol,
    State
)

class RuleApply:
    def __init__(self) :
        self.status = None
        self.taint_env = None
        self.frame = None
        self.stmt = None
        self.stmt_id = None
        self.space = None

    def read_rules(self, operation, source_rules):
        """从src.yaml文件中获取field_read语句类型的规则, 并根据每条规则创建taint_bv"""
        rules = []

        for rule in source_rules:
            if rule.operation == operation:
                rules.append(rule)
        return rules

    def read_and_apply_source_rules(self, data:EventData):
        data = data.in_data
        source_rules: list[dict] = data.rules.all_sources
        operation = data.operation
        # in_taint是个字典{symbol_name: tag_bv}
        in_taint = data.in_taint
        stmt = data.stmt
        frame = data.frame
        taint_env = frame.taint_env
        taint_status = data.taint_status
        
        rules = self.read_rules(operation, source_rules)
        app_result = None

        if operation == "field_read":
            app_result = self.apply_field_read_source_rules(rules, taint_status, stmt, frame)
        elif operation == "call_stmt":
            app_result = self.apply_call_stmt_source_rules(rules, taint_status, stmt, frame)

        data.out_data = in_taint
        return app_result

    def apply_field_read_source_rules(self, rules:list[dict], taint_status, stmt, frame):
        """根据规则为source添加和更新taint_bv"""
        taint_env = frame.taint_env
        status = frame.stmt_id_to_status[stmt.stmt_id]
        space = frame.symbol_state_space
        in_taint = taint_status.in_taint
        target_symbol = space[status.defined_symbol]
        target_state = space[next(iter(target_symbol.states))]
        print(target_state)
        if target_state.symbol_or_state == 0:
            return er.config_event_unprocessed()
        target_access_path = target_state.access_path
        target_access_path = util.access_path_formatter(target_access_path)
        app_result = er.config_event_unprocessed()
        
        for rule in rules:
            # print(target_access_path)
            # print(rule.target)
            # print(888888888888888888)
            if rule.receiver == stmt.receiver_object or target_access_path == rule.target:
                app_result = er.config_block_event_requester(app_result)
                tag_info = rule
                for tag in rule.tag:
                    tag_info.tag = [tag]
                    if tag == TAG_KEYWORD.TARGET:
                        tag_space_id = space[status.defined_symbol].symbol_id
                    if tag == TAG_KEYWORD.RECEIVER:
                        tag_space_id = space[status.used_symbols[0]].symbol_id
                    tag = in_taint.get(tag_space_id, 0)
                    # 遍历该规则对应的tags，并添加和更新tag_bv
                    new_tag = taint_env.add_and_update_tag_bv(tag_info = tag_info, current_taint = tag)
                    # print(99999999999999999999999999)
                    # print(new_tag)
                    # print(tag_space_id)
                    taint_status.out_taint[tag_space_id] = new_tag
                    print("taint here")
        print(taint_status.out_taint)
        return app_result


    def apply_call_stmt_source_rules(self, rules, taint_status, stmt, frame):
        taint_env = frame.taint_env
        status = frame.stmt_id_to_status[stmt.stmt_id]
        space = frame.symbol_state_space
        in_taint = taint_status.in_taint
        method_symbol = space[status.used_symbols[0]]
        tag_space_id = space[status.defined_symbol].symbol_id
        method_states = method_symbol.states

        app_result = er.EventHandlerReturnKind.UNPROCESSED
        for rule in rules:
            tag_info = rule
            name = tag_info.name
            for state_index in method_states:
                if not space[state_index] or space[state_index].symbol_or_state == 0:
                    continue
                state_access_path = space[state_index].access_path
                if isinstance(state_access_path, str):
                    continue
                access_path = util.access_path_formatter(state_access_path)

                if len(access_path) == 0:
                    access_path = stmt.name
                if access_path == name:
                    tag = in_taint.get(tag_space_id, 0)
                    new_tag = taint_env.add_and_update_tag_bv(tag_info = tag_info, current_taint = tag)
                    taint_status.out_taint[tag_space_id] = new_tag
                    app_result = er.config_block_event_requester(app_result)
        
        return app_result
                
    def read_and_apply_sink_rules(self, data:EventData):
        data = data.in_data
        sink_rules: list[dict] = data.rules.all_sinks
        operation = data.operation
        # in_taint是个字典{symbol_name: tag_bv}
        self.in_taint = data.in_taint
        self.stmt = data.stmt
        self.stmt_id = data.stmt_id
        frame = data.frame
        self.taint_env = frame.taint_env
        taint_status = data.taint_status
        space = frame.symbol_state_space
        taint_state_manager = frame.taint_state_manager

        rules = self.read_rules(operation, sink_rules)
        if operation == "call_stmt":
            app_result = self.apply_call_stmt_sink_rules(rules, taint_status, frame, space, taint_state_manager)

    def apply_call_stmt_sink_rules(self, rules, taint_status, frame, space, taint_state_manager):
        status = frame.stmt_id_to_status[self.stmt_id]
        method_symbol = space[status.used_symbols[0]]
        used_symbols = status.used_symbols
        method_index = used_symbols[0]
        method_symbol = space[method_index]

        for rule in rules:
            # todo 当规则较长时，则应该切成数组，倒序与state_access_path匹配
            # rule_access_path = rule.name.split('.')
            for state in method_symbol.states:
                # 检查函数名是否符合规则
                if self.check_method_name(rule.name, state, space):
                    # 检查参数是否携带tag
                    self.check_tag(rule.target, used_symbols, space, taint_state_manager)


    def check_method_name(self, rule_name, method_state, space):
        apply_flag = True
        if not isinstance(space[method_state], State):
            return False
        
        state_access_path = space[method_state].access_path
        access_path = util.access_path_formatter(state_access_path)
        access_path = access_path.split('.')
        rule_name = rule_name.split('.')
        if len(access_path) < len(rule_name):
            return False
        # name匹配上
        for i, item in enumerate(reversed(rule_name)):
            if item == TAG_KEYWORD.ANYNAME:
                continue
            if item != access_path[-i-1]:
                apply_flag = False
                break
        
        return apply_flag

    def check_tag(self, rule_tag, used_symbols, space, taint_state_manager):
        # 暂时检测taint_env中的tag,且只考虑positional_args
        if len(rule_tag) == 0:
            return
        for target_arg in rule_tag:

            arg_index = int(target_arg[-1])
            if arg_index + 1 >= len(used_symbols):
                continue
            arg_symbol = space[used_symbols[arg_index + 1]]
            arg_states = arg_symbol.states

            for state_index in arg_states:
                self.check_state_tag(state_index, space, taint_state_manager)

    def check_state_tag(self, state_index, space, taint_state_manager):
        if space[state_index].symbol_or_state == 0:
            return
        state_id = space[state_index].state_id
        access_path_tag = config.NO_TAINT
        if space[state_index].access_path:
            access_path = util.access_path_formatter(space[state_index].access_path)
            access_path_tag = taint_state_manager.get_access_path_tag_in_sink(access_path)

        tag = self.taint_env.get_state_tag(state_id)
        if tag != config.NO_TAINT :
            # 报告sink
            print(space[state_index])
            print(f"sink in {self.stmt_id}, tag: {tag}")
        if access_path_tag != config.NO_TAINT:
            # 报告sink
            print(f"access_path sink in {self.stmt_id}, tag: {access_path_tag}")
        print(space[state_index].fields)
        for value in space[state_index].fields.values():
            for field_state_index in value:
                self.check_state_tag(field_state_index, space, taint_state_manager)

    def read_and_apply_prop_rules(self, data:EventData):
        data = data.in_data
        source_rules: list[dict] = data.rules.all_propagations
        operation = data.operation
        # in_taint是个字典{symbol_name: tag_bv}
        in_taint = data.in_taint
        stmt = data.stmt
        frame = data.frame
        taint_env = frame.taint_env
        taint_status = data.taint_status
        rules = self.read_rules(operation, source_rules)
        app_result = er.config_event_unprocessed()
        if operation == "field_read":
            app_result = self.apply_field_read_prop_rules(rules, taint_status, stmt, frame)
        elif operation == "call_stmt":
            
            app_result = self.apply_call_stmt_prop_rules(rules, taint_status, stmt, frame)

        data.out_data = in_taint
        return app_result
    
    def apply_field_read_prop_rules(self, rules, taint_status, stmt, frame):
        taint_env = frame.taint_env
        status = frame.stmt_id_to_status[stmt.stmt_id]
        space = frame.symbol_state_space
        in_taint = taint_status.in_taint
        receiver_symbol = space[status.used_symbols[0]]
        target_space_id = space[status.defined_symbol].symbol_id
        receiver_states = receiver_symbol.states
        app_result = er.config_event_unprocessed()
        field_symbol = space[status.used_symbols[1]]
        field_name = field_symbol.value
        receiver_tag = in_taint.get(receiver_symbol.symbol_id, config.NO_TAINT)

        for rule in rules:
            if field_name in rule.field and receiver_tag != config.NO_TAINT:
                taint_status.out_taint[target_space_id] = receiver_tag
                app_result = er.config_block_event_requester(app_result)
                continue
        print(taint_status.out_taint)
        return app_result
    
    def apply_call_stmt_prop_rules(self, rules, taint_status, stmt, frame):
        taint_env = frame.taint_env
        status = frame.stmt_id_to_status[stmt.stmt_id]
        space = frame.symbol_state_space
        in_taint = taint_status.in_taint
        method_symbol = space[status.used_symbols[0]]
        method_states = method_symbol.states

        app_result = er.config_event_unprocessed()
        for rule in rules:
            # if rule.dst == TAG_KEYWORD.TARGET:
            target_symbol_id = space[status.defined_symbol].symbol_id
            # tag来自函数name
            for method_state in method_states:
                if rule.src == "name" and self.check_method_name(rule.name, method_state, space):
                    method_tag = taint_status.get_in_taint_tag(method_symbol.symbol_id)
                    taint_status.set_out_taint_tag(target_symbol_id, method_tag)
                elif rule.src == TAG_KEYWORD.ARG0 and self.check_method_name(rule.src, method_state, space):
                    arg0_symbol_id = space[status.used_symbols[1]].symbol_id
                    arg_tag = taint_status.get_in_taint_tag(arg0_symbol_id)
                    taint_status.set_out_taint_tag(target_symbol_id, arg_tag)


