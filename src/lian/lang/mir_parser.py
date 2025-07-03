#!/usr/bin/env python3

from lian.lang import common_parser

class Parser(common_parser.Parser):

    def function_declaration(self, node, statements):
        header_node = self.find_child_by_type(node, "function_header")
        if header_node:
            header_info = self.function_header(header_node)
        else:
            print("No function_header node found")

        body_statements = []
        body_node = self.find_child_by_type(node, "function_body")
        if body_node:
            body_statements = self.function_body(body_node)
        else:
            print("No function_body node found")

        self.append_stmts(statements, node, {
            "function_decl": {
                **header_info,
                "body": body_statements
            }
        })

        return

    def function_header(self, node):
        name_node = self.find_child_by_field(node, "name")
        function_name = self.read_node_text(name_node) if name_node else "Unknown"

        parameters = []
        params_node = self.find_child_by_field(node, "parameters")
        if params_node:
            for param_node in params_node.named_children:
                param_info = self.parameter(param_node)
                parameters.append(param_info)

        return_type_node = self.find_child_by_field(node, "return_type")
        if return_type_node:
            return_type = self.type_expression(return_type_node)
        else:
            return_type = None

        return {
            "data_type": return_type,
            "name": function_name,
            "parameters": parameters,
        }

    def function_body(self, node):
        body_statements = []
        for child in node.named_children:
            if self.is_declaration(child):
                self.declaration(child, body_statements)
            elif self.is_statement(child):
                self.statement(child, body_statements)
            else:
                print(f"unprocessed node: {child.type}")
        return body_statements

    def parameter(self, node):
        name_node = self.find_child_by_field(node, "name")
        param_name = self.read_node_text(name_node) if name_node else "unknown"
        type_node = self.find_child_by_field(node, "type")
        if type_node:
            param_type = self.type_expression(type_node)
        else:
            param_type = "unknown"

        return {
            "parameter_decl": {
                "data_type": param_type,
                "name": param_name,
            }
        }

    def type_expression(self, node):
        print(f"Processing type_expression for node type: {node.type}")
        if node.type == "primitive_type":
            return self.read_node_text(node)
        elif node.type == "tuple_type":
            elements = [self.type_expression(child) for child in node.named_children]
            return f"({', '.join(elements)})"
        elif node.type == "pointer_type":
            pointer = self.read_node_text(node.child_by_field_name("pointer"))
            referenced_type_node = node.child_by_field_name("referenced_type")
            referenced_type = self.type_expression(referenced_type_node) if referenced_type_node else "unknown_type"
            return f"{pointer} {referenced_type}"
        elif node.type == "reference_type":
            reference = "&"
            lifetime_node = node.child_by_field_name("lifetime")
            lifetime = self.read_node_text(lifetime_node) if lifetime_node else ""
            mutable = "mut " if self.has_child_with_field(node, "mutable") else ""
            referenced_type_node = node.child_by_field_name("referenced_type")
            referenced_type = self.type_expression(referenced_type_node) if referenced_type_node else "unknown_type"
            return f"{reference}{lifetime}{mutable}{referenced_type}"
        elif node.type == "array_type":
            array_type_node = node.child_by_field_name("array_type")
            array_type = self.type_expression(array_type_node) if array_type_node else "unknown_type"
            length_node = node.child_by_field_name("length")
            length = self.read_node_text(length_node) if length_node else ""
            return f"[{array_type}; {length}]"
        elif node.type == "path_type":
            return self.path_type(node)
        elif node.type == "qualified_path":
            return self.qualified_path(node)
        elif node.type == "impl_type":
            implemented_type_node = node.child_by_field_name("implemented_type")
            implemented_type = self.type_expression(implemented_type_node) if implemented_type_node else "unknown_impl_type"
            return f"impl {implemented_type}"
        elif node.type == "impl_at":
            file_location_node = node.child_by_field_name("file_location")
            file_location = self.read_node_text(file_location_node) if file_location_node else "unknown_location"
            return f"impl at {file_location}"
        elif node.type == "never_reaches":
            return "!"
        elif node.type == "region":
            lifetime_node = node.child_by_field_name("lifetime")
            lifetime = self.read_node_text(lifetime_node) if lifetime_node else "unknown_lifetime"
            referenced_type_node = node.child_by_field_name("referenced_type")
            referenced_type = self.type_expression(referenced_type_node) if referenced_type_node else "unknown_type"
            return f"'{lifetime} {referenced_type}"
        else:
            print(f"[ERROR]: Unprocessed type_expression type: {node.type}")
            return "unknown_type_expression"



    def variable_declaration(self, node, statements):
        name_node = self.find_child_by_field(node, "name")
        var_name = self.read_node_text(name_node) if name_node else "unknown"
        type_node = self.find_child_by_field(node, "type")
        if type_node:
            var_type = self.type_expression(type_node)
        else:
            var_type = "unknown"

        self.append_stmts(statements, node, {
            "variable_decl": {
                "data_type": var_type,
                "name": var_name,
            }
        })

    def const_declaration(self, node, statements):
        name_node = self.find_child_by_field(node, "name")
        const_name = self.read_node_text(name_node) if name_node else "unknown_const"

        type_node = self.find_child_by_field(node, "type")
        if type_node:
            const_type = self.type_expression(type_node)
        else:
            const_type = "unknown_type"

        value_node = self.find_child_by_field(node, "value")
        if value_node:
            const_value = self.constant_expression(value_node, statements)
        else:
            const_value = None

        self.append_stmts(statements, node, {
            "const_decl": {
                "data_type": const_type,
                "name": const_name,
                "value": const_value
            }
        })


    def basic_block(self, node, statements):
        label_node = self.find_child_by_field(node, "label")
        label = self.read_node_text(label_node) if label_node else "unknown_label"

        block_statements = []
        for child in node.named_children:
            if child == label_node:
                continue
            if self.is_declaration(child):
                self.declaration(child, block_statements)
            elif self.is_statement(child):
                self.statement(child, block_statements)
            elif child.type == "terminator":
                terminator = self.terminator(child, block_statements)
                block_self.append_stmts(statements, node, {"terminator": terminator})
            else:
                print(f"Unprocessed node in basic_block: {child.type}")

        self.append_stmts(statements, node, {
            "basic_block": {
                "label": label,
                "body": block_statements
            }
        })

    def terminator(self, node, statements):
        print(f"Processing terminator node: {node.type}")

        for child in node.named_children:
            print(f"Found terminator child: {child.type}")  # 调试语句
            if child.type in ["return_terminator", "return_statement"]:
                print(f"Handling {child.type}")  # 调试语句
                return self.handle_return_terminator(child, statements)
            elif child.type == "goto_terminator":
                print("Handling goto_terminator")  # 调试语句
                return self.handle_goto_terminator(child, statements)
            elif child.type == "panic_terminator":
                print("Handling panic_terminator")  # 调试语句
                return self.handle_panic_terminator(child, statements)
            elif child.type == "if_terminator":
                print("Handling if_terminator")  # 调试语句
                return self.handle_if_terminator(child, statements)
            elif child.type == "switchInt_terminator":
                print("Handling switchInt_terminator")  # 调试语句
                return self.handle_switchInt_terminator(child, statements)
            elif child.type == "call_terminator":
                print("Handling call_terminator")  # 调试语句
                return self.handle_call_terminator(child, statements)
            elif child.type == "drop_terminator":
                print("Handling drop_terminator")  # 调试语句
                return self.handle_drop_terminator(child, statements)
            elif child.type == "diverge_terminator":
                print("Handling diverge_terminator")  # 调试语句
                return self.handle_diverge_terminator(child, statements)
            elif child.type == "unreachable_terminator":
                print("Handling unreachable_terminator")  # 调试语句
                return self.handle_unreachable_terminator(child, statements)
            else:
                print(f"未知的 terminator 子类型: {child.type}")
                return {"unknown_terminator": {"type": child.type}}

        print("terminator 节点没有有效的子节点")
        return {"unknown_terminator": {}}

    def handle_return_terminator(self, node, statements):
        print("Handling return_terminator")  # 调试语句
        value_node = self.find_child_by_field(node, "value")
        return_value = self.expression(value_node, statements) if value_node else None

        return {
            "return_terminator": {
                "value": return_value
            }
        }

    def handle_goto_terminator(self, node, statements):
        print("Handling goto_terminator")  # 调试语句
        target_node = self.find_child_by_field(node, "target")
        target_label = self.read_node_text(target_node) if target_node else "unknown_target"
        return {
            "goto_terminator": {
                "target": target_label
            }
        }

    def handle_panic_terminator(self, node, statements):
        print("Handling panic_terminator")  # 调试语句
        target_node = self.find_child_by_field(node, "target")
        target_label = self.read_node_text(target_node) if target_node else "unknown_target"
        return {
            "panic_terminator": {
                "target": target_label
            }
        }

    def handle_if_terminator(self, node, statements):
        print("Handling if_terminator")  # 调试语句
        condition_node = self.find_child_by_field(node, "condition")
        true_target_node = self.find_child_by_field(node, "true_target")
        false_target_node = self.find_child_by_field(node, "false_target")

        condition = self.expression(condition_node, statements) if condition_node else None
        true_target = self.read_node_text(true_target_node) if true_target_node else "unknown_true_target"
        false_target = self.read_node_text(false_target_node) if false_target_node else "unknown_false_target"

        return {
            "if_terminator": {
                "condition": condition,
                "true_target": true_target,
                "false_target": false_target
            }
        }

    def handle_call_terminator(self, node, statements):
        print("Handling call_terminator")  # 调试语句
        result_node = self.find_child_by_field(node, "result")
        function_node = self.find_child_by_field(node, "function")
        arguments_node = self.find_child_by_field(node, "arguments")
        true_target_node = self.find_child_by_field(node, "true_target")
        false_target_node = self.find_child_by_field(node, "false_target")

        result = self.lvalue(result_node, statements) if result_node else "unknown_result"
        function_name = self.read_node_text(function_node) if function_node else "unknown_function"

        arguments = []
        if arguments_node:
            for arg_node in arguments_node.named_children:
                arg_expr = self.expression(arg_node, statements)
                arguments.append(arg_expr)

        true_target = self.read_node_text(true_target_node) if true_target_node else "unknown_true_target"
        false_target = self.read_node_text(false_target_node) if false_target_node else "unknown_false_target"

        return {
            "call_terminator": {
                "result": result,
                "function": function_name,
                "arguments": arguments,
                "true_target": true_target,
                "false_target": false_target
            }
        }

    def handle_drop_terminator(self, node, statements):
        print("Handling drop_terminator")  # 调试语句
        value_node = self.find_child_by_field(node, "value")
        value = self.lvalue(value_node, statements) if value_node else "unknown_value"

        jump_targets_node = self.find_child_by_field(node, "jump_targets")
        jump_targets = self.jump_targets(jump_targets_node, statements) if jump_targets_node else []

        return {
            "drop_terminator": {
                "value": value,
                "jump_targets": jump_targets
            }
        }

    def handle_diverge_terminator(self, node, statements):
        print("Handling diverge_terminator")  # 调试语句
        return {
            "diverge_terminator": {}
        }

    def handle_unreachable_terminator(self, node, statements):
        print("Handling unreachable_terminator")  # 调试语句
        return {
            "unreachable_terminator": {}
        }

    def handle_switchInt_terminator(self, node, statements):
        print("Handling switchInt_terminator")  # 调试语句
        expression_node = self.find_child_by_field(node, "expression")
        expression = self.expression(expression_node, statements) if expression_node else "unknown_expression"

        # 解析 jump_targets 部分
        jump_targets_node = self.find_child_by_field(node, "jump_targets")
        jump_targets = self.jump_targets(jump_targets_node, statements) if jump_targets_node else []

        # 创建 switchInt_terminator 语句
        switch_stmt = {
            "switchInt_terminator": {
                "expression": expression,
                "jump_targets": jump_targets
            }
        }
        self.append_stmts(statements, node, switch_stmt)

    def assignment_statement(self, node, statements):
        left_node = self.find_child_by_field(node, "left")
        right_node = self.find_child_by_field(node, "right")

        left_expr = self.lvalue(left_node, statements) if left_node else None

        if right_node:
            right_expr = self.expression(right_node, statements)
        else:
            right_expr = None

        self.append_stmts(statements, node, {
            "assign_stmt": {
                "target": left_expr,
                "operand": right_expr
            }
        })

    def return_statement(self, node, statements):
        value_node = self.find_child_by_field(node, "value")
        value = self.expression(value_node, statements) if value_node else None

        self.append_stmts(statements, node, {
            "return_stmt": {
                "operand": value
            }
        })

    def drop_statement(self, node, statements):
        kind_node = self.find_child_by_field(node, "kind")
        kind = self.read_node_text(kind_node) if kind_node else "unknown_kind"

        value_node = self.find_child_by_field(node, "value")
        value = self.lvalue(value_node, statements) if value_node else "unknown_value"

        self.append_stmts(statements, node, {
            "drop_stmt": {
                "kind": kind,
                "value": value
            }
        })

    def scope(self, node, statements):
        scope_label_node = self.find_child_by_field(node, "scope_label")
        scope_label = self.read_node_text(scope_label_node) if scope_label_node else "unknown_scope_label"

        scope_statements = []
        for child in node.named_children:
            if child == scope_label_node:
                continue
            if self.is_declaration(child):
                self.declaration(child, scope_statements)
            elif self.is_statement(child):
                self.statement(child, scope_statements)
            else:
                print(f"Unprocessed node in scope: {child.type}")

        self.append_stmts(statements, node, {
            "scope": {
                "label": scope_label,
                "body": scope_statements
            }
        })

    def debug_statement(self, node, statements):
        variable_node = self.find_child_by_field(node, "variable")
        variable = self.read_node_text(variable_node) if variable_node else "unknown_variable"

        debug_node = self.find_child_by_field(node, "debug_value")

        if debug_node:
            value_node = self.find_child_by_field(debug_node, "value")
            value = self.debug_value(value_node, statements) if value_node else "unknown_value"
        else:
            value = "unknown_value"

        self.append_stmts(statements, node, {
            "debug_stmt": {
                "variable": variable,
                "value": value
            }
        })

    def debug_value(self, node, statements):
        if node.type == "const_expression":
            return self.const_expression(node, statements)
        elif node.type == "identifier":
            return self.read_node_text(node)
        else:
            print(f"Unprocessed debug_value type: {node.type}")
            return "unknown_debug_value"

    def assert_statement(self, node, statements):
        negate = False
        condition_node = None
        message_node = None
        expressions_nodes = []

        children = node.named_children
        for child in children:
            if child.type == "!":
                negate = True
            elif child.field_name == "condition":
                condition_node = child
            elif child.field_name == "message":
                message_node = child
            elif child.field_name == "expressions":
                expressions_nodes.append(child)

        condition = self.expression(condition_node, statements) if condition_node else None
        message = self.read_node_text(message_node) if message_node else None
        expressions = [self.expression(expr, statements) for expr in expressions_nodes]

        self.append_stmts(statements, node, {
            "assert_stmt": {
                "negate": negate,
                "condition": condition,
                "message": message,
                "expressions": expressions
            }
        })

    def unreach_statement(self, node, statements):
        self.append_stmts(statements, node, {
            "unreach_stmt": "unreachable"
        })

    def resume_statement(self, node, statements):
        self.append_stmts(statements, node, {
            "resume_stmt": "resume"
        })

    def function_call_expression(self, node, statements):
        function_node = self.find_child_by_field(node, "function")
        function_name = self.read_node_text(function_node) if function_node else "unknown_function"

        arguments = []
        arguments_nodes = self.find_children_by_field(node, "arguments")
        for arguments_node in arguments_nodes:
            for arg_node in arguments_node.named_children:
                arg_expr = self.expression(arg_node, statements)
                arguments.append(arg_expr)

        # 获取 '->' 后的部分（basic_block_label 或 unwind_expression）
        basic_block_label = None
        unwind_expression = None
        basic_block_label_node = self.find_child_by_field(node, "basic_block_label")
        unwind_expression_node = self.find_child_by_field(node, "unwind_expression")

        if basic_block_label_node:
            basic_block_label = self.read_node_text(basic_block_label_node)
        elif unwind_expression_node:
            unwind_expression = self.unwind_expression(unwind_expression_node, statements)

        # 获取 'jump_targets' 部分
        jump_targets = []
        jump_targets_node = self.find_child_by_field(node, "jump_targets")
        if jump_targets_node:
            jump_targets = self.jump_targets(jump_targets_node, statements)

        temp_var = self.tmp_variable(node)

        call_stmt = {
            "call_stmt": {
                "target": temp_var,
                "name": function_name,
                "arguments": arguments
            }
        }

        if basic_block_label:
            call_stmt["call_stmt"]["basic_block_label"] = basic_block_label
        if unwind_expression:
            call_stmt["call_stmt"]["unwind_expression"] = unwind_expression
        if jump_targets:
            call_stmt["call_stmt"]["jump_targets"] = jump_targets
        self.append_stmts(statements, node, call_stmt)

        return temp_var


    def basic_block_label(self, node, statements):
        label = self.read_node_text(node)
        return label

    def unwind_expression(self, node, statements):
        value_node = self.find_child_by_field(node, "value")
        if value_node.type == "identifier":
            value = self.read_node_text(value_node)
        elif value_node.type == "continue":
            value = "continue"
        elif value_node.type == "terminate":
            cleanup_node = self.find_child_by_field(value_node, "cleanup")
            if cleanup_node:
                value = f"terminate(cleanup)"
            else:
                value = "terminate"
        else:
            value = self.read_node_text(value_node)

        return value

    def jump_targets(self, node, statements):
        targets = []
        for child in node.named_children:
            key_node = self.find_child_by_field(child, "key")
            value_node = self.find_child_by_field(child, "value")

            key = self.read_node_text(key_node) if key_node else "unknown_key"
            if value_node:
                if value_node.type == "basic_block_label":
                    value = self.read_node_text(value_node)
                elif value_node.type == "unwind_expression":
                    value = self.unwind_expression(value_node, statements)
                elif value_node.type == "return":
                    value = "return"
                elif value_node.type == "continue":
                    value = "continue"
                elif value_node.type == "terminate":
                    value = "terminate"
                elif value_node.type == "unreachable":
                    value = "unreachable"
                else:
                    value = self.read_node_text(value_node)
            else:
                value = "unknown_value"

            targets.append({"key": key, "value": value})

        return targets


    def move_expression(self, node, statements):
        value_node = self.find_child_by_field(node, "value")
        value_expr = self.expression(value_node, statements) if value_node else None
        return value_expr

    def copy_expression(self, node, statements):
        value_node = self.find_child_by_field(node, "value")
        value_expr = self.expression(value_node, statements) if value_node else None
        return value_expr

    def unary_expression(self, node, statements):
        operator_node = self.find_child_by_field(node, "operator")
        argument_node = self.find_child_by_field(node, "argument")

        operator = self.read_node_text(operator_node) if operator_node else "unknown_operator"
        argument_expr = self.expression(argument_node, statements) if argument_node else None

        temp_var = self.tmp_variable(node)

        self.append_stmts(statements, node, {
            "unary_expr": {
                "target": temp_var,
                "operator": operator,
                "operand": argument_expr
            }
        })

        return temp_var

    def struct_initialization_expression(self, node, statements):
        struct_type_node = self.find_child_by_field(node, "struct_type")
        fields_node = self.find_child_by_field(node, "fields")

        struct_type = self.type_expression(struct_type_node) if struct_type_node else "unknown_struct"
        fields = {}
        if fields_node:
            for field_init in fields_node.named_children:
                field_name_node = self.find_child_by_field(field_init, "field_name")
                field_value_node = self.find_child_by_field(field_init, "value")
                field_name = self.read_node_text(field_name_node) if field_name_node else "unknown_field"
                field_value = self.expression(field_value_node, statements) if field_value_node else None
                fields[field_name] = field_value

        temp_var = self.tmp_variable(node)

        self.append_stmts(statements, node, {
            "struct_init": {
                "target": temp_var,
                "struct_type": struct_type,
                "fields": fields
            }
        })

        return temp_var

    def as_expression(self, node, statements):
        expr_node = self.find_child_by_field(node, "expression")
        type_node = self.find_child_by_field(node, "type")

        expr = self.expression(expr_node, statements) if expr_node else None
        target_type = self.type_expression(type_node) if type_node else "unknown_type"

        temp_var = self.tmp_variable(node)

        self.append_stmts(statements, node, {
            "as_expr": {
                "target": temp_var,
                "expression": expr,
                "type": target_type
            }
        })

        return temp_var

    def cast_annotation(self, node, statements):
        annotation_node = self.find_child_by_field(node, "annotation")
        inner_annotation_node = self.find_child_by_field(node, "inner_annotation")

        annotation = self.read_node_text(annotation_node) if annotation_node else "unknown_annotation"
        inner_annotation = self.read_node_text(inner_annotation_node) if inner_annotation_node else None

        return {
            "cast_annotation": {
                "annotation": annotation,
                "inner_annotation": inner_annotation
            }
        }


    def const_expression(self, node, statements):

        if len(node.children) < 2 or node.children[0].type != 'const':
            print("[ERROR]: Invalid const_expression syntax")
            return "unknown"

        value_node = node.children[1]

        if value_node.type == 'constant_with_type':
            const_expr = self.constant_with_type(value_node, statements)
        elif value_node.type == 'path_type':
            path_type = self.path_type(value_node)
            const_expr = {
                "type": "path_type",
                "value": path_type
            }
        elif value_node.type == 'qualified_path':
            qualified_path = self.qualified_path(value_node)
            const_expr = {
                "type": "qualified_path",
                "value": qualified_path
            }
        else:
            print(f"[ERROR]: Unknown type in const_expression: {value_node.type}")
            const_expr = {"type": "unknown", "value": self.read_node_text(value_node)}

        temp_var = self.tmp_variable(node)

        const_stmt = {
            "const_expr": {
                "target": temp_var,
                "type": const_expr["type"],
                "value": const_expr["value"]
            }
        }

        self.append_stmts(statements, node, const_stmt)

        return temp_var


    def constant_with_type(self, node, statements):

        constant_node = self.find_child_by_field(node, "constant")
        value = self.constant(constant_node, statements) if constant_node else "unknown"

        type_suffix_node = self.find_child_by_field(node, "type_suffix")
        type_suffix = self.read_node_text(type_suffix_node).lstrip('_') if type_suffix_node else "unknown"

        return {
            "type": type_suffix,
            "value": value
        }

    def path_type(self, node):
        print("Handling path_type")  # 调试语句
        segments = []
        for segment_node in node.named_children:
            if segment_node.type == 'path_segment':
                segment = self.path_segment(segment_node)
                segments.append(segment)

        path = "::".join(segments)
        print(f"Parsed path_type: {path}")  # 调试语句
        return path


    def qualified_path(self, node, statements):
        # 解析 `<Type as Trait>::method`
        type_node = self.find_child_by_field(node, "type")
        trait_node = self.find_child_by_field(node, "trait")
        method_node = self.find_child_by_field(node, "method")

        type_str = self.type_expression(type_node, statements) if type_node else "UnknownType"
        trait_str = self.read_node_text(trait_node) if trait_node else "UnknownTrait"
        method_str = self.read_node_text(method_node) if method_node else "unknown_method"

        return f"<{type_str} as {trait_str}>::{method_str}"


    def path_segment(self, node):
        identifier_node = self.find_child_by_field(node, "identifier")
        generic_args_node = self.find_child_by_field(node, "generic_arguments")

        identifier = self.read_node_text(identifier_node) if identifier_node else "unknown_identifier"

        if generic_args_node:
            generic_args = []
            for arg_node in generic_args_node.named_children:
                arg = self.type_expression(arg_node)
                generic_args.append(arg)

            return f"{identifier}<{', '.join(generic_args)}>"
        else:
            return identifier


    #lvalue
    def lvalue(self, node, statements):
        if node.type == "identifier":
            return self.read_node_text(node)
        elif node.type == "type_cast_lvalue":
            return self.type_cast_lvalue(node, statements)
        elif node.type == "field_access_lvalue":
            return self.field_access(node, statements)
        elif node.type == "array_access_lvalue":
            return self.array_access_lvalue(node, statements)
        elif node.type == "dereference_lvalue":
            return self.dereference_lvalue(node, statements)
        elif node.type == "parenthesized_lvalue":
            return self.parenthesized_lvalue(node, statements)
        elif node.type == "annotated_lvalue":
            return self.annotated_lvalue(node, statements)
        else:
            print(f"Unprocessed lvalue type: {node.type}")
            return {"unknown_lvalue": self.read_node_text(node)}

    def type_cast_lvalue(self, node, statements):
        identifier_node = self.find_child_by_field(node, "identifier")
        type_node = self.find_child_by_field(node, "type")

        identifier = self.read_node_text(identifier_node) if identifier_node else "unknown_identifier"
        var_type = self.type_expression(type_node) if type_node else "unknown_type"

        return {
            "type_cast_lvalue": {
                "data_type": var_type,
                "name": identifier,
            }
        }

    def array_access_lvalue(self, node, statements):
        object_node = self.find_child_by_field(node, "object")
        index_node = self.find_child_by_field(node, "index")

        obj = self.lvalue(object_node, statements) if object_node else "unknown_object"
        index = self.expression(index_node, statements) if index_node else "unknown_index"

        return {
            "array_access_lvalue": {
                "object": obj,
                "index": index
            }
        }

    def field_access(self, node, statements):
        object_node = self.find_child_by_field(node, "object")
        field_node = self.find_child_by_field(node, "field")

        obj = self.parse(object_node, statements) if object_node else None
        field = self.read_node_text(field_node) if field_node else "unknown_field"

        temp_var = self.tmp_variable(node)

        self.append_stmts(statements, node, {
            "field_access_expr": {
                "target": temp_var,
                "obj": obj,
                "field": field,
            }
        })

        return temp_var

    def complex_value(self, node, statements):
        # 获取 'path' 和 'index' 节点
        path_node = self.find_child_by_field(node, "path")
        index_node = self.find_child_by_field(node, "index")

        # 解析 'path'
        path = self.path_type(path_node) if path_node else "unknown_path"

        # 解析 'index'
        if index_node.type == "int":
            index = self.read_node_text(index_node)
        elif index_node.type == "identifier":
            index = self.read_node_text(index_node)
        else:
            index = "unknown_index"

        # 返回字符串表示，例如 "path[index]"
        complex_value_str = f"{path}[{index}]"
        print(f"Generated complex_value string: {complex_value_str}")  # 调试语句
        return complex_value_str

    def tuple_expression(self, node, statements):
        elements = [self.expression(child, statements) for child in node.named_children]
        tuple_str = f"({', '.join(elements)})"
        print(f"Generated tuple string: {tuple_str}")  # 调试语句
        return tuple_str


    def annotated_lvalue(self, node, statements):
        lvalue_node = self.find_child_by_field(node, "lvalue")
        lvalue = self.lvalue(lvalue_node, statements) if lvalue_node else None
        return lvalue

    def dereference_lvalue(self, node, statements):
        operand_node = self.find_child_by_field(node, "operand")
        operand = self.lvalue(operand_node, statements) if operand_node else "unknown_operand"

        return {
            "dereference_lvalue": {
                "operand": operand
            }
        }

    def parenthesized_lvalue(self, node, statements):
        lvalue_node = self.find_child_by_field(node, "lvalue")
        if not lvalue_node and node.named_children:
            lvalue_node = node.named_children[0]
        lvalue = self.lvalue(lvalue_node, statements) if lvalue_node else None
        return lvalue

    def parenthesized_expression(self, node, statements):
        expr_node = self.find_child_by_field(node, "expression")
        expr = self.expression(expr_node, statements) if expr_node else None

        return {
            "parenthesized_expression": expr
        }

    #rvalue
    def use_rvalue(self, node, statements):
        lvalue_node = self.find_child_by_field(node, "lvalue")
        lvalue = self.lvalue(lvalue_node, statements) if lvalue_node else "unknown_lvalue"

        return {
            "use_rvalue": lvalue
        }

    def repeat_rvalue(self, node, statements):
        expr1_node = self.find_child_by_field(node, "lvalue1")
        expr2_node = self.find_child_by_field(node, "lvalue2")

        expr1 = self.lvalue(expr1_node, statements) if expr1_node else "unknown_expr1"
        expr2 = self.lvalue(expr2_node, statements) if expr2_node else "unknown_expr2"

        return {
            "repeat_rvalue": {
                "expr": expr1,
                "count": expr2
            }
        }

    def list_rvalue(self, node, statements):
        elements = []
        for child in node.named_children:
            if child.type != ",":
                elem = self.expression(child, statements)
                elements.append(elem)

        return {
            "list_rvalue": elements
        }

    def length_rvalue(self, node, statements):
        expr_node = self.find_child_by_field(node, "lvalue")
        expr = self.lvalue(expr_node, statements) if expr_node else "unknown_expr"

        return {
            "length_rvalue": expr
        }

    def indexed_rvalue(self, node, statements):
        identifier_node = self.find_child_by_field(node, "identifier")
        index_node = self.find_child_by_field(node, "index")

        identifier = self.read_node_text(identifier_node) if identifier_node else "unknown_identifier"
        index = self.expression(index_node, statements) if index_node else "unknown_index"

        return {
            "indexed_rvalue": {
                "identifier": identifier,
                "index": index
            }
        }

    def box_rvalue(self, node, statements):
        return {
            "box_rvalue": "box"
        }

    def constant_rvalue(self, node, statements):
        return self.constant(node, statements)

    def expression_wrapper(self, node, statements):
        if len(node.named_children) == 1:
            return self.expression(node.named_children[0], statements)
        else:
            print("Unexpected expression node with multiple children")
            return {"unknown_expression": self.read_node_text(node)}

    def identifier_expression(self, node, statements):
        return self.read_node_text(node)

    def parenthesized_lvalue_expression(self, node, statements):
        lvalue = self.lvalue(node, statements)
        return lvalue

    def is_comment(self, node):
        return node.type in ["line_comment", "block_comment"]

    def is_identifier(self, node):
        return node.type == "identifier"

    def is_literal(self, node):
        return self.obtain_literal_handler(node) is not None

    def is_expression(self, node):
        return self.check_expression_handler(node) is not None

    def is_statement(self, node):
        return self.check_statement_handler(node) is not None

    def is_declaration(self, node):
        return self.check_declaration_handler(node) is not None


    def obtain_literal_handler(self, node):
        LITERAL_MAP = {
        }

        return LITERAL_MAP.get(node.type, None)

    def check_expression_handler(self, node):
        EXPRESSION_HANDLER_MAP = {
        "function_call_expression": self.function_call_expression,
        "move_expression": self.move_expression,
        "copy_expression": self.copy_expression,
        "type_cast_lvalue": self.type_cast_lvalue,
        "parenthesized_expression": self.parenthesized_expression,
        "expression": self.expression_wrapper,
        "identifier": self.identifier_expression,
        "parenthesized_lvalue": self.parenthesized_lvalue_expression,
        "field_access_expression": self.field_access,
        "unary_expression": self.unary_expression,
        "struct_initialization_expression": self.struct_initialization_expression,
        "as_expression": self.as_expression,
        "cast_annotation": self.cast_annotation,
        "const_expression": self.const_expression,
        "use_rvalue": self.use_rvalue,
        "repeat_rvalue": self.repeat_rvalue,
        "list_rvalue": self.list_rvalue,
        "length_rvalue": self.length_rvalue,
        "indexed_rvalue": self.indexed_rvalue,
        "box_rvalue": self.box_rvalue,
        "constant_rvalue": self.constant_rvalue,
        "complex_value" : self.complex_value,
        "tuple_expression" : self.tuple_expression,
        }

        return EXPRESSION_HANDLER_MAP.get(node.type, None)

    def check_declaration_handler(self, node):
        DECLARATION_HANDLER_MAP = {
            "function_declaration": self.function_declaration,
            "variable_declaration": self.variable_declaration
        }

        return DECLARATION_HANDLER_MAP.get(node.type, None)

    def check_statement_handler(self, node):
        STATEMENT_HANDLER_MAP = {
            "assignment_statement": self.assignment_statement,
            "return_statement": self.return_statement,
            "basic_block": self.basic_block,
            "drop_statement": self.drop_statement,
            "scope": self.scope,
            "debug_statement": self.debug_statement,
            "assert_statement": self.assert_statement,
            "unreach_statement": self.unreach_statement,
            "resume_statement": self.resume_statement,
        }

        return STATEMENT_HANDLER_MAP.get(node.type, None)

    def literal(self, node, statements, replacement):
        handler = self.obtain_literal_handler(node)
        return handler(node, statements, replacement)

    def expression(self, node, statements):
        handler = self.check_expression_handler(node)
        if handler:
            return handler(node, statements)
        else:
            print(f"Unprocessed expression type: {node.type}")
            return {"unknown_expression": self.read_node_text(node)}

    def declaration(self, node, statements):
        handler = self.check_declaration_handler(node)
        return handler(node, statements)

    def statement(self, node, statements):
        handler = self.check_statement_handler(node)
        return handler(node, statements)

    def constant(self, node, statements):
        if node.type == "constant":
            child_node = node.named_children[0] if node.named_children else None
            if child_node:
                return self.constant(child_node, statements)
            else:
                return "unknown"
        elif node.type in ["int", "uint", "float", "bool", "bytes", "static_string", "trait_projection"]:
            return self.read_node_text(node)
        elif node.type == "constant_aggregate":
            aggregate = {}
            for field_init in node.named_children:
                field_name_node = self.find_child_by_field(field_init, "field_name")
                field_value_node = self.find_child_by_field(field_init, "value")
                field_name = self.read_node_text(field_name_node) if field_name_node else "unknown_field"
                field_value = self.constant(field_value_node, statements) if field_value_node else "unknown_value"
                aggregate[field_name] = field_value
            return aggregate
        elif node.type == "cast_expression":
            return self.read_node_text(node)
        elif node.type == "(":
            constants = [self.constant(child, statements) for child in node.named_children]
            return constants
        elif node.type == "[":
            constants = [self.constant(child, statements) for child in node.named_children]
            return constants
        else:
            print(f"[ERROR]: Unprocessed constant type: {node.type}")
            return "unknown"

    def has_child_with_field(self, node, field_name):
        for child in node.named_children:
            if getattr(child, 'field_name', None) == field_name:
                return True
        return False
