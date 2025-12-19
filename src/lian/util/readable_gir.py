from lian.util import util

class ReadableGir:
    def __init__(self):

        self.handlers = {
            "import_stmt": self.import_stmt,
            # "export_stmt": self.empty,
            "trait_decl": self.trait_decl,
            "implement_decl": self.implement_decl,
            # "record_decl": self.empty,
            # "interface_decl": self.empty,
            "yield_stmt": self.yield_stmt,
            "goto_stmt": self.goto_stmt,
            "label_stmt": self.label_stmt,
            # "record_write": self.empty,
            # "record_extend": self.empty,
            # "slice_wirte": self.empty,
            # "slice_read": self.empty,
            "new_object": self.new_object,
            "new_array": self.new_array,


            "enum_decl": self.enum_decl,
            "method_decl": self.method_decl,
            "variable_decl": self.variable_decl,
            "parameter_decl": self.parameter_decl,
            "struct_decl": self.struct_decl,
            "union_decl": self.union_decl,
            "block": self.block_stmt,
            "block_start": self.block_start,
            "block_end": self.block_end,

            "assign_stmt": self.assign_stmt,
            "while_stmt": self.while_stmt,
            "if_stmt": self.if_stmt,
            "for_stmt": self.for_stmt,
            "return_stmt": self.return_stmt,
            "call_stmt": self.call_stmt,

            "dowhile_stmt": self.dowhile_stmt,
            "forin_stmt": self.forin_stmt,
            "switch_stmt": self.switch_stmt,
            "case_stmt": self.case_stmt,
            "default_stmt": self.default_stmt,
            "break_stmt": self.break_stmt,
            "continue_stmt": self.continue_stmt,

            "assert_stmt": self.assert_stmt,
            # "asm_stmt": self.empty_stmt,
            # "del_stmt": self.empty,
            # "unset_stmt": self.empty,
            # "pass_stmt": self.pass_stmt,
            # "global_stmt": self.empty,
            # "nonlocal_stmt": self.empty,
            # "type_cast_stmt": self.empty,

            "field_write": self.field_write,
            "field_read": self.field_read,
            "mem_read": self.mem_read,
            "mem_write": self.mem_write,
            "addr_of": self.addr_of,
            "array_write": self.array_write,
            "array_read": self.array_read,
        }

    def import_stmt(self, stmt):
        expr = f"import {stmt.name}"
        return expr

    def trait_decl(self, stmt):
        trait_str = f"trait {stmt.name}"
        if util.is_available(stmt.attrs):
            trait_str = f"{stmt.attrs} {trait_str}"
        if util.is_available(stmt.type_parameters):
            trait_str = f"{trait_str}<{stmt.type_parameters}>"
        return trait_str

    def implement_decl(self, stmt):
        impl_str = ""
        if util.is_available(stmt.trait_name):
            impl_str = f"impl {stmt.trait_name} for {stmt.struct_name}"
        else:
            impl_str = f"impl {stmt.struct_name}"

        if util.is_available(stmt.type_parameters):
            impl_str = f"{impl_str}<{stmt.type_parameters}>"

        return impl_str

    def method_decl(self, stmt):
        expr = f"{stmt.data_type} {stmt.name}"
        if util.is_available(stmt.attrs):
            expr = f"{stmt.attrs} {expr}"
        
        if util.is_available(stmt.type_parameters):
            expr = f"{expr}({stmt.type_parameters})"

        return expr

    def parameter_decl(self, stmt):
        param_str = ""
        if util.is_available(stmt.default_value):
            param_str = f"{stmt.data_type} {stmt.name} = {stmt.default_value}"
        else:
            param_str = f"{stmt.data_type} {stmt.name}"
        return param_str

    def variable_decl(self, stmt):
        expr = f"{stmt.data_type} {stmt.name}"
        if util.is_available(stmt.attrs):
            expr = f"{stmt.attrs} {expr}"
        return expr

    def struct_decl(self, stmt):
        expr = f"struct {stmt.name}"
        if util.is_available(stmt.attrs):
            expr = f"{stmt.attrs} {expr}"
        if util.is_available(stmt.type_parameters):
            expr = f"{expr}<{stmt.type_parameters}>"
        return expr

    def union_decl(self, stmt):
        expr = f"struct {stmt.name}"
        if util.is_available(stmt.attrs):
            expr = f"{stmt.attrs} {expr}"
        if util.is_available(stmt.type_parameters):
            expr = f"{expr}<{stmt.type_parameters}>"
        return expr

    def enum_decl(self, stmt):
        expr = f"enum {stmt.name}"
        if util.is_available(stmt.attrs):
            expr = f"{stmt.attrs} {expr}"
        if util.is_available(stmt.type_parameters):
            expr = f"{expr}<{stmt.type_parameters}>"
        return expr


    def block_stmt(self, stmt):
        pass

    def block_start(self, stmt):
        pass

    def block_end(self, stmt):
        pass

    def assign_stmt(self, stmt):
        expr = ""
        if util.is_available(stmt.operand2):
            expr = f"{stmt.target} = {stmt.operand} {stmt.operator} {stmt.operand2}"
        elif util.is_available(stmt.operator):
            expr = f"{stmt.target} = {stmt.operator} {stmt.operand}"
        else:
            expr = f"{stmt.target} = {stmt.operand}"
        return expr

    def while_stmt(self, stmt):
        while_str = f"while {stmt.condition}"
        return while_str

    def if_stmt(self, stmt):
        if_str = ""
        if hasattr(stmt, "then_body") and stmt.then_body:
            if_str = f"if {stmt.condition}"
            
        return if_str

    def for_stmt(self, stmt):
        for_str = f"for {stmt.condition}"
        return for_str

    def return_stmt(self, stmt):
        return_str = f"return {stmt.name}"
        return return_str

    def call_stmt(self, stmt):
        args_str = ""
        if util.is_available(stmt.positional_args):
            args_str = f"{stmt.positional_args}"
        if util.is_available(stmt.named_args):
            args_str = f"{args_str} {stmt.named_args}"

        call_str = f"{stmt.target} = {stmt.name}({args_str})"

        return call_str

    def dowhile_stmt(self, stmt):
        dowhile_str = f"do_while {stmt.condition}"
        return dowhile_str

    def forin_stmt(self, stmt):
        forin_str = f"for {stmt.value} in {stmt.receiver}"
        return forin_str

    def switch_stmt(self, stmt):
        switch_str = f"switch {stmt.condition}"
        return switch_str

    def case_stmt(self, stmt):
        case_str = f"case {stmt.condition}"
        return case_str

    def default_stmt(self, stmt):
        default_str = f"default"
        return default_str

    def break_stmt(self, stmt):
        break_str = "break"
        return break_str

    def continue_stmt(self, stmt):
        continue_str = "continue"
        return continue_str

    def goto_stmt(self, stmt):
        goto_str = f"goto {stmt.name}"
        return goto_str

    def yield_stmt(self, stmt):
        yield_str = f"yield {stmt.name}"
        return yield_str

    def label_stmt(self, stmt):
        label_str = f"label {stmt.name}:"
        return label_str

    def assert_stmt(self, stmt):
        assert_str = f"assert {stmt.condition}: {stmt.message}"
        return assert_str

    def field_write(self, stmt):
        expr = f"{stmt.receiver_object}.{stmt.field} = {stmt.source}"
        return expr


    def field_read(self, stmt):
        expr = f"{stmt.target} = {stmt.receiver_object}.{stmt.field}"
        return expr

    def addr_of(self, stmt):
        expr = f"{stmt.target} = &{stmt.source}"
        return expr

    def array_write(self, stmt):
        expr = f"{stmt.array}[{stmt.index}] = {stmt.source}"
        return expr

    def array_read(self, stmt):
        expr = f"{stmt.target} = {stmt.array}[{stmt.index}]"
        return expr

    def mem_read(self, stmt):
        expr = f"{stmt.target} = *{stmt.source}"
        return expr

    def mem_write(self, stmt):
        expr = f"*{stmt.target} = {stmt.source}"
        return expr

    def new_array(self, stmt):
        expr = f"{stmt.target} = {stmt.data_type}"
        if util.is_available(stmt.attrs):
            expr = f"{stmt.target} = {stmt.attrs} {stmt.data_type}"
        return expr

    def new_object(self, stmt):
        r_expr = f"dyn {stmt.data_type}"
        if util.is_available(stmt.attrs):
            r_expr = f"{stmt.attrs} {r_expr}"

        if util.is_available(stmt.args):
            r_expr = f"{r_expr}({stmt.args})"

        expr = f"{stmt.target} = {r_expr}"

        return expr
    
    def del_stmt(self, stmt):
        expr = f"delete {stmt.target}"
        return expr

    def get_gir_str(self, stmt: object):
        op = getattr(stmt, "operation", None)
        handler = self.handlers.get(op, None)
        if handler:
            return handler(stmt)
        else:
            return f"Unknown statement: {op}"


# ---------------------------
# Module-level API (compat for existing callers)
# ---------------------------
_DEFAULT_READABLE_GIR = ReadableGir()

def get_gir_str(stmt: object) -> str:
    """
    兼容调用方式：
        from lian.util import readable_gir
        readable_gir.get_gir_str(stmt)
    """
    return _DEFAULT_READABLE_GIR.get_gir_str(stmt)