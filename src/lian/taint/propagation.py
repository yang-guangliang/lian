#!/usr/bin/env python3


# tag propagation
# - given a statement, check if we need to propagate the operands' tags to the result/target
#    * symbol level
#    * state level
import sys

from pandas.core import frame
import config1 as config
sys.path.extend([config.LIAN_DIR, config.TAINT_DIR])
# dispatch stmt -> handle (check source/ manage tag/ check sink)
import taint.apps.event_return as er

from rule_manager import RuleManager

from taint.apps.app_template import EventData
from taint.util import access_path_formatter
from taint import config1 as config
from taint.constants import EventKind
from taint.taint_structs import (MethodTaintFrame, PropagationResult)#, TagBitVectorManager, CallInfo
from taint.apps.event_manager import EventManager
from lian.util import util
from lian.util.loader import Loader

from lian.semantic.semantic_structs import (
    Symbol,
    State
)
class TaintPropagationInMethod:
    def __init__(self, frame: MethodTaintFrame):
        self.frame: MethodTaintFrame = frame
        self.stmt_id_to_stmt = frame.stmt_id_to_stmt
        self.stmt_id_to_status = frame.stmt_id_to_status
        self.stmt_id_to_taint_status = frame.stmt_id_to_taint_status
        self.event_manager = EventManager(frame.lian.options)
        self.rule_manager = RuleManager()
        self.taint_analysis_handlers = {
            "comment_stmt"                          : self.comment_stmt_taint,
            "package_stmt"                          : self.package_stmt_taint,
            "assign_stmt"                           : self.assign_stmt_taint,
            "call_stmt"                             : self.call_stmt_taint,
            "echo_stmt"                             : self.echo_stmt_taint,
            "exit_stmt"                             : self.exit_stmt_taint,
            "return_stmt"                           : self.return_stmt_taint,
            "yield_stmt"                            : self.yield_stmt_taint,
            "sync_stmt"                             : self.sync_stmt_taint,
            "label_stmt"                            : self.label_stmt_taint,
            "throw_stmt"                            : self.throw_stmt_taint,
            "try_stmt"                              : self.try_stmt_taint,
            "catch_stmt"                            : self.catch_stmt_taint,
            "asm_stmt"                              : self.asm_stmt_taint,
            "assert_stmt"                           : self.assert_stmt_taint,
            "pass_stmt"                             : self.pass_stmt_taint,
            "with_stmt"                             : self.with_stmt_taint,
            "await_stmt"                            : self.await_stmt_taint,
            "global_stmt"                           : self.global_stmt_taint,
            "nonlocal_stmt"                         : self.nonlocal_stmt_taint,
            "type_cast_stmt"                        : self.type_cast_stmt_taint,
            "type_alias_stmt"                       : self.type_alias_stmt_taint,
            "phi_stmt"                              : self.phi_stmt_taint,
            "unsafe_block"                          : self.unsafe_block_stmt_taint,
            "block"                                 : self.block_stmt_taint,
            "block_start"                           : self.block_start_stmt_taint,

            "import_stmt"                           : self.import_stmt_taint,
            "from_import_stmt"                      : self.from_import_stmt_taint,
            "export_stmt"                           : self.export_stmt_taint,
            "require_stmt"                          : self.require_stmt_taint,

            "if_stmt"                               : self.if_stmt_taint,
            "dowhile_stmt"                          : self.dowhile_stmt_taint,
            "while_stmt"                            : self.while_stmt_taint,
            "for_stmt"                              : self.for_stmt_taint,
            "forin_stmt"                            : self.forin_stmt_taint,
            "for_value_stmt"                        : self.for_value_stmt_taint,
            "switch_stmt"                           : self.switch_stmt_taint,
            "case_stmt"                             : self.case_stmt_taint,
            "default_stmt"                          : self.default_stmt_taint,
            "switch_type_stmt"                      : self.switch_type_stmt_taint,
            "break_stmt"                            : self.break_stmt_taint,
            "continue_stmt"                         : self.continue_stmt_taint,
            "goto_stmt"                             : self.goto_stmt_taint,

            "namespace_decl"                        : self.namespace_decl_taint,
            "class_decl"                            : self.class_decl_taint,
            "record_decl"                           : self.record_decl_taint,
            "interface_decl"                        : self.interface_decl_taint,
            "enum_decl"                             : self.enum_decl_taint,
            "struct_decl"                           : self.struct_decl_taint,
            "enum_constants"                        : self.enum_constants_taint,
            "annotation_type_decl"                  : self.annotation_type_decl_taint,
            "annotation_type_elements_decl"         : self.annotation_type_elements_decl_taint,

            "parameter_decl"                        : self.parameter_decl_taint,
            "variable_decl"                         : self.variable_decl_taint,
            "method_decl"                           : self.method_decl_taint,

            "new_array"                             : self.new_array_taint,
            "new_object"                            : self.new_object_taint,
            "new_record"                            : self.new_record_taint,
            "new_set"                               : self.new_set_taint,
            "new_struct"                            : self.new_struct_taint,

            "addr_of"                               : self.addr_of_taint,
            "mem_read"                              : self.mem_read_taint,
            "mem_write"                             : self.mem_write_taint,
            "array_write"                           : self.array_write_taint,
            "array_read"                            : self.array_read_taint,
            "array_insert"                          : self.array_insert_taint,
            "array_append"                          : self.array_append_taint,
            "array_extend"                          : self.array_extend_taint,
            "record_write"                          : self.record_write_taint,
            "record_extend"                         : self.record_extend_taint,
            "field_write"                           : self.field_write_taint,
            "field_read"                            : self.field_read_taint,
            "field_addr"                            : self.field_addr_taint,
            "slice_write"                           : self.slice_write_taint,
            "slice_read"                            : self.slice_read_taint,
            "del_stmt"                              : self.del_stmt_taint,
            "unset_stmt"                            : self.unset_stmt_taint,
        }

    def entry_method(self, frame):
        method_id = frame.method_id
        method_decl_stmt = frame.stmt_id_to_stmt[method_id]

    def analyze_stmt(self, stmt_id, taint_status):
        in_taint = taint_status.in_taint
        stmt = self.stmt_id_to_stmt[stmt_id]

        handler = self.taint_analysis_handlers.get(stmt.operation)
        if handler:
            return handler(stmt_id, stmt, in_taint, taint_status)

        return self.empty_stmt_taint(stmt_id, stmt, in_taint, taint_status)

    def get_symbols_tags(self, symbol_id_to_taint, *space_indexs):
        tag = config.NO_TAINT
        space = self.frame.symbol_state_space
        for index in space_indexs:
            if index > 0 and isinstance(space[index], Symbol):
                symbol_id = space[index].symbol_id
                tag |= symbol_id_to_taint.get(symbol_id, config.NO_TAINT)
        return tag

    def set_symbols_tags(self, tag, taint_status, *space_indexs):
        space = self.frame.symbol_state_space
        for index in space_indexs:
            symbol_id = space[index].symbol_id
            taint_status.out_taint[symbol_id] = tag
        print("set_symbols_tags")
        print(f"out_taint: {taint_status.out_taint}")

    def propagate_tags(self, stmt_id, in_taint, taint_status):
        """将used_symbols的tag直接传播到defined_symbol中"""
        status = self.stmt_id_to_status[stmt_id]
        tag = self.get_symbols_tags(in_taint, *status.used_symbols)
        self.set_symbols_tags(tag, taint_status, *[status.defined_symbol])

        event = EventData(
            "abc",
            EventKind.PROP_FOREACH_ITEM,
            {
                "stmt_id"           : stmt_id,
                "stmt"              : self.stmt_id_to_stmt[stmt_id],
                "operation"         : "call_stmt",
                "rules"             : self.rule_manager,
                "in_taint"          : in_taint,
                "taint_status"      : taint_status,
                "frame"             : self.frame,
                "status"            : self.stmt_id_to_status[stmt_id],
                "tag"               : tag,
            }
        )
        app_return = self.event_manager.notify(event)


    def empty_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass
    def comment_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass
    def package_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def assign_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):

        self.propagate_tags(stmt_id, in_taint, taint_status)
        # print("assign_stmt")
        # print(taint_status.out_taint)

    def call_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        print("call_stmt_taint")
        # print(stmt_id)
        status = self.frame.stmt_id_to_status[stmt_id]
        event = EventData(
                "abc",
                EventKind.CALL_BEFORE,
                {
                    "stmt_id"           : stmt_id,
                    "stmt"              : stmt,
                    "operation"         : "call_stmt",
                    "rules"             : self.rule_manager,
                    "in_taint"          : in_taint,
                    "taint_status"      : taint_status,
                    "frame"             : self.frame,
                    "taint_state_manager": self.frame.taint_state_manager,
                    "status"             : status,
                }
            )
        app_return = self.event_manager.notify(event)
        event.event = EventKind.TAINT_BEFORE
        app_return = self.event_manager.notify(event)
        event.event = EventKind.PROP_BEFORE
        app_return = self.event_manager.notify(event)
        event.event = EventKind.SINK_BEFORE
        app_return = self.event_manager.notify(event)

        if er.should_block_event_requester(app_return):
            return

        # 判断是否完全分析完了
        callee_info = PropagationResult(stmt_id)
        if stmt_id in self.frame.stmt_id_to_callees:
            for callee in self.frame.stmt_id_to_callees[stmt_id]:
                key = (self.frame.method_id, callee, stmt_id)
                if key not in self.frame.content_to_be_analyzed or self.frame.content_to_be_analyzed[key]:
                    callee_info.interruption_flag = True
                    break


        target_space = self.frame.symbol_state_space[status.defined_symbol]
        # self.propagate_tags(stmt_id, in_taint, taint_status)
        # TODO：如果这条call_stmt在call_graph上没有后继，说明静态分析解析失败，调用LLM来处理
        if stmt_id not in self.frame.stmt_id_to_callees:
            pass
        callee_info.stmt_id = stmt_id
        # 收集return symbol的tag，交给target
        if self.frame.callee_return:
            taint_status.out_taint[target_space.symbol_id] = self.frame.callee_return
            self.frame.callee_return = None
        return callee_info


    def echo_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def exit_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def return_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):

        # 收集return symbol的tag，
        status = self.frame.stmt_id_to_status[stmt_id]
        target_symbol_index = status.used_symbols[0]
        target_symbol_id = self.frame.symbol_state_space[target_symbol_index].symbol_id
        if target_symbol_id in in_taint:
            if self.frame.return_tag:
                self.frame.return_tag |= in_taint[target_symbol_id]
            else:
                self.frame.return_tag = in_taint[target_symbol_id]
        print(f"return_stmt_taint: {self.frame.return_tag}")


    def yield_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def sync_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def label_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def throw_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def try_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def catch_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def asm_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def assert_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def pass_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def with_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def await_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def global_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def nonlocal_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.global_stmt_taint(stmt_id, stmt, in_taint, taint_status)

    def type_cast_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def type_alias_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def phi_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def unsafe_block_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def block_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def block_start_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def import_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def from_import_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def export_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def require_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def if_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def dowhile_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def while_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def for_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def forin_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def for_value_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def switch_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def case_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def default_stmt_taint(self, stmt_id, stmt, in_taint, taint_status, status, space):
        pass

    def switch_type_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def break_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def continue_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def goto_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass


    def namespace_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def class_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def record_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.class_decl_taint(stmt_id, stmt, in_taint, taint_status)

    def interface_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.class_decl_taint(stmt_id, stmt, in_taint, taint_status)

    def enum_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def struct_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.class_decl_taint(stmt_id, stmt, in_taint, taint_status)

    def enum_constants_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def annotation_type_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def annotation_type_elements_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def parameter_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        # self.propagate_tags(stmt_id, in_taint, taint_status)
        pass

    def variable_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def method_decl_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass


    def new_array_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def new_object_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def new_record_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def new_set_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def new_struct_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass


    def addr_of_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def mem_read_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def mem_write_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def array_write_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def array_read_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def array_insert_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def array_append_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def array_extend_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def record_write_taint(self, stmt_id, stmt, in_taint, taint_status):
        # self.propagate_tags(stmt_id, in_taint, taint_status)
        pass

    def record_extend_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def field_write_taint(self, stmt_id, stmt, in_taint, taint_status):

        self.propagate_tags(stmt_id, in_taint, taint_status)

        taint_state_manager = self.frame.taint_state_manager
        space = self.frame.symbol_state_space
        status = self.stmt_id_to_status[stmt_id]
        defined_symbol = space[status.defined_symbol].symbol_id
        used_symbol_id = space[status.used_symbols[0]].symbol_id
        tag = in_taint.get(used_symbol_id, config.NO_TAINT)
        used_symbol = space[status.used_symbols[0]]
        field = space[status.used_symbols[1]]
        field_name = field.value
        for used_state_index in used_symbol.states:
            used_state = space[used_state_index]
            # analyzing stmt_id: 7773
            if not used_state or isinstance(used_state, Symbol) or not used_state.access_path:
                continue
            access_path = access_path_formatter(used_state.access_path)
            access_path = access_path + '.' + field_name
            taint_state_manager.add_path_to_tag(access_path, tag)

        # defined_index = status.defined_symbol
        # defined_symbol_id = space[defined_index].symbol_id
        # if stmt.operation == "field_write":
        #     for used_index in status.used_symbols:
        #         used_symbol = space[used_index]
        #         for used_state_index in used_symbol.states:
        #             used_state = space[used_state_index]
        #             defined_taint_state = self.symbol_id_to_access_path.get(defined_symbol_id, TaintState())
        #             defined_taint_state.append(used_state.access_path)
        #             self.taint_tag[used_symbol] = tag
        #             self.access_path_to_tag[used_state.access_path] |= tag

    def field_read_taint(self, stmt_id, stmt, in_taint, taint_status):
        print("field_read_before")
        print(f"out_taint: {taint_status.out_taint}")
        taint_state_manager = self.frame.taint_state_manager
        event = EventData(
            "abc",
            EventKind.TAINT_BEFORE,
            {
                "stmt_id"           : stmt_id,
                "stmt"              : stmt,
                "operation"         : "field_read",
                "rules"             : self.rule_manager,
                "in_taint"          : in_taint,
                "taint_status"      : taint_status,
                "frame"             : self.frame,
                "status"            : self.stmt_id_to_status[stmt_id],
            }
        )
        app_return1 = self.event_manager.notify(event)
        event.event = EventKind.PROP_BEFORE
        app_return2 = self.event_manager.notify(event)
        # print("field_read")
        # print(taint_status.out_taint)
        status = self.stmt_id_to_status[stmt_id]
        # 添加access_path
        defined_space = self.frame.symbol_state_space[status.defined_symbol]
        all_tag = config.NO_TAINT
        for defined_state_index in defined_space.states:
            defined_state = self.frame.symbol_state_space[defined_state_index]
            if not isinstance(defined_state, State) or not defined_state.access_path:
                continue
            access_path = access_path_formatter(defined_state.access_path)

            tag = taint_state_manager.get_path_tag(access_path)
            all_tag |= tag

        used_space = self.frame.symbol_state_space[status.used_symbols[0]]

        for used_state_index in used_space.states:
            defined_state = self.frame.symbol_state_space[used_state_index]
            if not isinstance(defined_state, State) or not defined_state.access_path:
                continue
            access_path = access_path_formatter(defined_state.access_path)

            tag = taint_state_manager.get_path_tag(access_path)
            all_tag |= tag

        if all_tag != config.NO_TAINT:
            status = self.stmt_id_to_status[stmt_id]
            self.set_symbols_tags(all_tag, taint_status, *[status.defined_symbol])
            return
        # if len(defined_space.states) == 1:
        #     (defined_state_index, ) = defined_space.states
        # elif len(defined_space.states) == 2:
        #     (defined_state_index, other_value) = defined_space.states
        # (defined_state_index, ) = defined_space.states
        # access_path = self.frame.symbol_state_space[defined_state_index].access_path
        # defined_symbol_id = defined_space.symbol_id

        # taint_state_manager = self.frame.taint_state_manager
        # taint_state_manager.add_tag_and_path_for_field_read(defined_symbol_id, access_path)
        if er.should_block_event_requester(app_return1) or er.should_block_event_requester(app_return2):
            return
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def field_addr_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def slice_write_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def slice_read_taint(self, stmt_id, stmt, in_taint, taint_status):
        self.propagate_tags(stmt_id, in_taint, taint_status)

    def del_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

    def unset_stmt_taint(self, stmt_id, stmt, in_taint, taint_status):
        pass

