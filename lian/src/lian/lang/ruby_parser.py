#!/usr/bin/env python3

from lian.lang import common_parser

from collections import defaultdict

class Parser(common_parser.Parser):
    def is_comment(self, node):
        return node.type == "comment"

    def is_identifier(self, node):
        return node.type == "identifier"

    def obtain_literal_handler(self, node):
        LITERAL_MAP = {
            "integer": self.regular_number,
            "float": self.regular_number,
            # "complex": self.complex,
            # "rational": self.rational,
            "constant": self.constant,
            "string": self.string_literal,
            "true": self.regular_literal,
            "false": self.regular_literal,
            "array": self.array,
            "hash": self.hash,
        }

        return LITERAL_MAP.get(node.type, None)

    def is_literal(self, node):
        return self.obtain_literal_handler(node) is not None

    def literal(self, node, statements, replacement):
        handler = self.obtain_literal_handler(node)
        return handler(node, statements, replacement)

    def regular_number(self, node, statements, replacement):
        value = self.read_node_text(node)
        value = self.common_eval(value)
        return str(value)

    def constant(self, node, statements, replacement):
        value = self.read_node_text(node)
        return value

    def string_literal(self, node, statements, replacement):
        replacement = []
        for child in node.named_children:
            self.parse(child, statements, replacement)

        ret = self.read_node_text(node)
        return self.escape_string(ret)

    def regular_literal(self, node, statements, replacement):
        return self.read_node_text(node)

    def array(self, node, statements, replacement):
        tmp_var = self.tmp_variable()
        statements.append({"new_array": {"type": "", "target": tmp_var}})

        index = 0
        for child in node.named_children:
            if self.is_comment(child):
                continue

            shadow_child = self.parse(child, statements)
            statements.append({"array_write": {"array": tmp_var, "index": str(index), "source": shadow_child}})
            index += 1

        return tmp_var

    def hash(self, node, statements, replacement):
        tmp_var = self.tmp_variable()
        statements.append({"new_map": {"type": "", "target": tmp_var}})

        for child in node.named_children:
            if self.is_comment(child):
                continue
            key = self.find_child_by_field(child, "key")
            shadow_key = self.parse(key, statements)

            value = self.find_child_by_field(child, "value")
            shadow_value = self.parse(value, statements)

            statements.append({"map_write": {"map": tmp_var, "key": shadow_key, "value": shadow_value}})

        return tmp_var

    def check_declaration_handler(self, node):
        DECLARATION_HANDLER_MAP = {
            "method": self.method_declaration,
            "lambda": self.lambda_declaration,
            "class": self.class_declaration,
            "singleton_class": self.singleton_class_declaration,
            "module": self.module_declaration,
        }
        return DECLARATION_HANDLER_MAP.get(node.type, None)

    def is_declaration(self, node):
        return self.check_declaration_handler(node) is not None

    def declaration(self, node, statements):
        handler = self.check_declaration_handler(node)
        return handler(node, statements)

    def method_declaration(self, node, statements):
        name = self.find_child_by_field(node, "name")
        shadow_name = self.read_node_text(name)

        parameters = self.find_child_by_field(node, "parameters")
        new_parameters = []
        init = []

        if parameters:
            # need to deal with parameters
            for parameter in parameters.named_children:
                if parameter.type == 'identifier':
                    shadow_parameter = self.read_node_text(parameter)
                    new_parameters.append(shadow_parameter)
                elif parameter.type == 'optional_parameter':
                    parameter_name = self.find_child_by_field(parameter, 'name')
                    shadow_parameter = self.read_node_text(parameter_name)
                    new_parameters.append(shadow_parameter)

                    new_init = []

                    value = self.find_child_by_field(parameter, 'value')
                    shadow_value = self.parse(value, new_init)

                    new_init.append({ 'assign_stmt': { 'target': shadow_parameter, 'operand': shadow_value }})

                    init.extend(new_init)


        new_body = []
        child = self.find_child_by_field(node, "body")
        if child:
            for stmt in child.named_children:
                if self.is_comment(stmt):
                    continue

                self.parse(stmt, new_body)

        statements.append({"method_decl": {"attrs": [], "data_type": "", "name": shadow_name,
                             "parameters": new_parameters, "init": init, "body": new_body}})

    def lambda_declaration(self, node, statements):
        tmp_method = self.tmp_method()

        parameters = self.find_child_by_field(node, "parameters")
        new_parameters = []
        init = []

        if parameters:
            # need to deal with parameters
            for parameter in parameters.named_children:
                if parameter.type == 'identifier':
                    shadow_parameter = self.read_node_text(parameter)
                    new_parameters.append(shadow_parameter)
                elif parameter.type == 'optional_parameter':
                    parameter_name = self.find_child_by_field(parameter, 'name')
                    shadow_parameter = self.read_node_text(parameter_name)
                    new_parameters.append(shadow_parameter)

                    new_init = []

                    value = self.find_child_by_field(parameter, 'value')
                    shadow_value = self.parse(value, new_init)

                    new_init.append({ 'assign_stmt': { 'target': shadow_parameter, 'operand': shadow_value }})

                    init.extend(new_init)


        new_body = []
        child = self.find_child_by_field(node, "body")
        if child:
            for stmt in child.named_children:
                if self.is_comment(stmt):
                    continue

                self.parse(stmt, new_body)

        statements.append({"method_decl": {"attrs": [], "data_type": "", "name": tmp_method,
                             "parameters": new_parameters, "init": init, "body": new_body}})


    def class_declaration(self, node, statements):
        gir_node = defaultdict(list)

        name = self.find_child_by_field(node, 'name')
        shadow_name = self.parse(name)

        gir_node['name'] = shadow_name

        superclass = self.find_child_by_field(node, 'superclass')
        if superclass:
            superclass = superclass.children[1]
            shadow_superclass = self.read_node_text(superclass)
            gir_node['supers'].append(shadow_superclass)

        body = self.find_child_by_field(node, 'body')

        for child in body.named_children:
            if child.type == 'method':
                method = []
                self.method_declaration(child, method)
                gir_node['member_methods'].append(method.pop())
            if child.type == 'assignment':
                left = self.find_child_by_field(child, 'left')

                right = self.find_child_by_field(child, 'right')
                shadow_right = self.parse(right)

                if left.type == 'instance_variable':
                    shadow_left = self.read_node_text(left)[1:]
                    gir_node['fields'].append({ 'variable_decl': { 'name': shadow_left }})
                    gir_node['init'].append({ 'field_write': { 'receiver_object': self.global_self(), 'field': shadow_left, 'source': shadow_right }})
                elif left.type == 'class_variable':
                    shadow_left = self.read_node_text(left)[2:]
                    gir_node['static_init'].append({ 'assign_stmt': { 'target': shadow_left, 'operand': shadow_right }})

        statements.append({ 'class_decl': dict(gir_node) })

    def singleton_class_declaration(self, node, statements):
        self.class_declaration(node, statements)
        statements[-1]['class_decl']['attrs'] = ['singleton']

    def module_declaration(self, node, statements):
        body = self.find_child_by_field(node, 'body')
        new_body = []
        self.parse(body, new_body)
        statements.append({ 'namespace_decl': { 'body': new_body }})

    def check_expression_handler(self, node):
        EXPRESSION_HANDLER_MAP = {
            "binary": self.binary_expression,
            "unary": self.unary_expression,
            "conditional": self.conditional_expression,
            "assignment": self.assignment_expression,
            "operator_assignment": self.operator_assignment_expression,
            "call": self.call_expression,
            "element_reference": self.element_reference_expression,
            "argument_list": self.argument_list_expression,
            "instance_variable": self.instance_variable_expression,
        }

        return EXPRESSION_HANDLER_MAP.get(node.type, None)

    def is_expression(self, node):
        return self.check_expression_handler(node) is not None

    def expression(self, node, statements):
        handler = self.check_expression_handler(node)
        return handler(node, statements)

    def binary_expression(self, node, statements):
        left = self.find_child_by_field(node, "left")
        right = self.find_child_by_field(node, "right")
        operator = self.find_child_by_field(node, "operator")

        shadow_operator = self.read_node_text(operator)

        shadow_left = self.parse(left, statements)
        shadow_right = self.parse(right, statements)

        tmp_var = self.tmp_variable()
        statements.append({"assign_stmt": {"target": tmp_var, "operator": shadow_operator, "operand": shadow_left,
                                           "operand2": shadow_right}})

        return tmp_var

    def unary_expression(self, node, statements):
        operand = self.find_child_by_field(node, "operand")
        shadow_operand = self.parse(operand, statements)
        operator = self.find_child_by_field(node, "operator")
        shadow_operator = self.read_node_text(operator)

        tmp_var = self.tmp_variable()

        statements.append({"assign_stmt": {"target": tmp_var, "operator": shadow_operator, "operand": shadow_operand}})

        return tmp_var

    def conditional_expression(self, node, statements):
        condition = self.find_child_by_field(node, "condition")
        consequence = self.find_child_by_field(node, "consequence")
        alternative = self.find_child_by_field(node, "alternative")

        condition = self.parse(condition, statements)

        body = []
        elsebody = []
        tmp_var = self.tmp_variable()

        expr1 = self.parse(consequence, body)
        body.append({"assign_stmt": {"target": tmp_var, "operand": expr1}})

        expr2 = self.parse(alternative, elsebody)
        elsebody.append({"assign_stmt": {"target": tmp_var, "operand": expr2}})

        statements.append({"if_stmt": {"condition": condition, "body": body, "elsebody": elsebody}})

        return tmp_var

    def assignment_expression(self, node, statements):
        left = self.find_child_by_field(node, "left")
        right = self.find_child_by_field(node, "right")

        if right.type == 'right_assignment_list':
            shadow_right = self.argument_list_expression(right, statements)
        else:
            shadow_right = self.parse(right, statements)

        if left.type == "element_reference":
            shadow_map, shadow_key = self.parse_element_reference(left, statements)
            statements.append({"map_write": {"map": shadow_map, "key": shadow_key, "value": shadow_right}})
            return shadow_right

        if left.type == "call":
            name = self.find_child_by_field(left, "method")
            shadow_name = self.parse(name)

            myobject = self.find_child_by_field(left, "receiver")
            shadow_object = self.parse(myobject, statements)

            statements.append({"field_write": {"receiver_object": shadow_object, "field": shadow_name, "source": shadow_right}})

            return shadow_right

        if left.type == 'instance_variable':
            shadow_name = self.read_node_text(left)[1:]
            statements.append({"field_write": { "receiver_object": self.global_self(), "field": shadow_name, "source": shadow_right }}
            )
            return shadow_right

        if right.type == 'right_assignment_list':
            for index, shadow_left in enumerate(self.read_node_text(left).split(',')):
                shadow_left = shadow_left.strip()
                tmp_var = self.tmp_variable()
                statements.append({ "array_read": { "target": tmp_var, "array": shadow_right, "index": str(index) }})
                statements.append({ "assign_stmt": { "target": shadow_left, "operand": tmp_var }})
        else:
            shadow_left = self.read_node_text(left)
            statements.append({ "assign_stmt": { "target": shadow_left, "operand": shadow_right }})

        return shadow_left

    def operator_assignment_expression(self, node, statements):
        operator = self.find_child_by_field(node, 'operator')
        shadow_operator = self.read_node_text(operator).replace("=", "")
        shadow_left = self.assignment_expression(node, statements)

        statements[-1][list(statements[-1].keys()).pop()]['operator'] = shadow_operator
        return shadow_left

    def call_expression(self, node, statements):
        name = self.find_child_by_field(node, "method")
        shadow_name = self.parse(name, statements)

        myobject = self.find_child_by_field(node, "receiver")

        if myobject:
            shadow_object = self.parse(myobject, statements)
            tmp_var = self.tmp_variable()
            shadow_name = tmp_var

        args = self.find_child_by_field(node, "arguments")
        args_list = []

        if args:
            for child in args.named_children:
                if self.is_comment(child):
                    continue

                shadow_variable = self.parse(child, statements)
                if shadow_variable:
                    args_list.append(shadow_variable)

        tmp_return = self.tmp_variable()
        statements.append({"call_stmt": {"target": tmp_return, "name": shadow_name, "type_parameters": '', "args": args_list}})

        return self.global_return()

    def element_reference_expression(self, node, statements):
        tmp_var = self.tmp_variable()
        shadow_map, shadow_key = self.parse_element_reference(node, statements)
        statements.append({"map_read": {"target": tmp_var, "map": shadow_map, "key": shadow_key}})
        return tmp_var

    def argument_list_expression(self, node, statements):
        tmp_var = self.tmp_variable()
        statements.append({"new_array": {"type": "", "target": tmp_var}})

        index = 0
        for child in node.named_children:
            if self.is_comment(child):
                continue

            shadow_child = self.parse(child, statements)
            statements.append({"array_write": {"array": tmp_var, "index": str(index), "source": shadow_child}})
            index += 1

        return tmp_var

    def instance_variable_expression(self, node, statements):
        shadow_name = self.read_node_text(node)[1:]
        tmp_var = self.tmp_variable()
        statements.append({ "field_read": { "target": tmp_var, "receiver_object": self.global_this(), "field": shadow_name }})
        return tmp_var

    def check_statement_handler(self, node):
        STATEMENT_HANDLER_MAP = {
            "if": self.if_statement,
            "if_modifier": self.if_modifier_statement,
            "unless": self.unless_statement,
            "unless_modifier": self.unless_modifier_statement,
            "for": self.for_statement,
            "while": self.while_statement,
            "while_modifier": self.while_statement,
            "until": self.until_statement,
            "until_modifier": self.until_statement,
            "break": self.break_statement,
            "next": self.next_statement,
            "begin": self.begin_statement,
            "do": self.do_statement,
            "rescue_modifier": self.rescue_modifier_statement,
            "case": self.case_statement,
            "when": self.when_statement,
            "then": self.then_statement,
            "else": self.else_statement,
            "return": self.return_statement,
            "yield": self.yield_statement,
            "undef": self.undef_statement,
        }
        return STATEMENT_HANDLER_MAP.get(node.type, None)

    def is_statement(self, node):
        return self.check_statement_handler(node) is not None

    def statement(self, node, statements):
        handler = self.check_statement_handler(node)
        return handler(node, statements)

    def if_statement(self, node, statements):
        condition_part = self.find_child_by_field(node, "condition")
        true_part = self.find_child_by_field(node, "consequence")
        false_part = self.find_child_by_field(node, "alternative")

        true_body = []

        shadow_condition = self.parse(condition_part, statements)
        self.parse(true_part, true_body)
        if false_part:
            false_body = []
            self.parse(false_part, false_body)
            statements.append({"if_stmt": {"condition": shadow_condition, "then_body": true_body, "else_body": false_body}})
        else:
            statements.append({"if_stmt": {"condition": shadow_condition, "then_body": true_body}})

    def if_modifier_statement(self, node, statements):
        condition = self.find_child_by_field(node, "condition")
        shadow_condition = self.parse(condition)

        body = self.find_child_by_field(node, "body")
        new_body = []

        self.parse(body, new_body)

        statements.append({"if_stmt": {"condition": shadow_condition, "then_body": new_body }})

    def unless_statement(self, node, statements):
        condition_part = self.find_child_by_field(node, "condition")
        true_part = self.find_child_by_field(node, "consequence")
        false_part = self.find_child_by_field(node, "alternative")

        true_body = []

        shadow_condition = self.parse(condition_part, statements)
        self.parse(true_part, true_body)

        if false_part:
            false_body = []
            self.parse(false_part, false_body)
            statements.append({"if_stmt": {"condition": shadow_condition, "then_body": false_body, "else_body": true_body}})
        else:
            statements.append({"if_stmt": {"condition": shadow_condition, "then_body": [], "else_body": true_body}})

    def unless_modifier_statement(self, node, statements):
        condition = self.find_child_by_field(node, "condition")
        shadow_condition = self.parse(condition)

        body = self.find_child_by_field(node, "body")
        new_body = []

        self.parse(body, new_body)

        statements.append({"if_stmt": {"condition": shadow_condition, "then_body": [], "else_body": new_body }})

    def for_statement(self, node, statements):
        pattern = self.find_child_by_field(node, "pattern")

        shadow_names = []
        if pattern.named_child_count == 0:
            shadow_name = self.parse(pattern)
            shadow_names.append(shadow_name)
        else:
            for child in pattern.named_children:
                shadow_name = self.parse(child)
                shadow_names.append(shadow_name)

        tmp_var = self.tmp_variable()

        value = self.find_child_by_field(node, "value")
        shadow_value = self.parse(value, statements)

        for_body = []

        for index, shadow_name in enumerate(shadow_names):
            tmp_var2 = self.tmp_variable()
            statements.append({ "array_read": { "target": tmp_var2, "array": tmp_var, "index": str(index) }})
            statements.append({ "assign_stmt": {"target": shadow_name, "operand": tmp_var2 }})

        body = self.find_child_by_field(node, "body")
        self.parse(body, for_body)

        statements.append({"forin_stmt":
                               {"attrs": [],
                                "data_type": "",
                                "name": tmp_var,
                                "receiver": shadow_value,
                                "body": for_body}})

    def break_statement(self, node, statements):
        statements.append({ 'break_stmt': {}} )

    def next_statement(self, node, statements):
        statements.append({ 'continue_stmt': {}} )

    def while_statement(self, node, statements):
        condition = self.find_child_by_field(node, "condition")
        body = self.find_child_by_field(node, "body")

        new_condition_init = []

        shadow_condition = self.parse(condition, new_condition_init)

        new_while_body = []
        self.parse(body, new_while_body)

        statements.extend(new_condition_init)
        new_while_body.extend(new_condition_init)

        statements.append({"while_stmt": {"condition": shadow_condition, "body": new_while_body}})

    def until_statement(self, node, statements):
        self.while_statement(node, statements)

        tmp_var = self.tmp_variable()
        statement = statements.pop()

        statements.append({ 'assign_stmt':
            { 'target': tmp_var, 'operator': '!', 'operand': statement['while_stmt']['condition']} })

        statement['while_stmt']['body'].append({ 'assign_stmt':
            { 'target': tmp_var, 'operator': '!', 'operand': statement['while_stmt']['condition']} })

        statement['while_stmt']['condition'] = tmp_var

        statements.append(statement)

    def do_statement(self, node, statements):
        body = []
        for child in node.named_children:
            self.parse(child, body)
        statements.append({ 'block': { 'body': body }})

    def begin_statement(self, node, statements):
        body = []

        rescue_nodes = []
        else_node = None
        ensure_node = None

        for child in node.named_children:
            if child.type == 'rescue':
                rescue_nodes.append(child)
                continue

            if child.type == 'else':
                else_node = child
                continue

            if child.type == 'ensure':
                ensure_node = child
                continue

            self.parse(child, body)

        if rescue_nodes or else_node or ensure_node:
            try_stmt_opt = { "body": body }

            catch_body = []

            for rescue_node in rescue_nodes:
                new_clause_body = []
                clause_body = self.find_child_by_field(rescue_node, 'body')

                self.parse(clause_body, new_clause_body)

                exceptions = self.find_child_by_field(rescue_node, 'exceptions')
                for exception in self.read_node_text(exceptions).split(','):
                    catch_body.append({ 'catch_stmt': { 'exception': exception.strip(), 'body': new_clause_body }})

            try_stmt_opt['catch_body'] = catch_body

            if else_node is not None:
                new_clause_body = []

                for child in else_node.named_children:
                    self.parse(clause_body, new_clause_body)

                try_stmt_opt['else_body'] = new_clause_body

            if ensure_node is not None:
                new_clause_body = []

                for child in ensure_node.named_children:
                    self.parse(clause_body, new_clause_body)

                try_stmt_opt['final_body'] = new_clause_body

            return statements.append({"block": { "body": [{ 'try_stmt': try_stmt_opt }] }})

        statements.append({"block": { "body": body }})

    def rescue_modifier_statement(self, node, statements):
        body = self.find_child_by_field(node, 'body')
        try_body = []

        self.parse(body, try_body)

        catch = self.find_child_by_field(node, 'handler')
        catch_body = []

        self.parse(catch, catch_body)

        statements.append({ 'try_stmt': { 'body': try_body, 'catch_body': [{ 'catch_stmt': { 'body': catch_body } }]}})

    def case_statement(self, node, statements):
        condition = self.find_child_by_field(node, 'value')
        shadow_condition = self.parse(condition, statements)

        new_body = []

        for child in node.named_children:
            self.parse(child, new_body)

        statements.append({ 'switch_stmt': { 'condition': shadow_condition, 'body': new_body }})

    def when_statement(self, node, statements):
        condition = self.find_child_by_field(node, 'pattern')
        shadow_condition = self.parse(condition, statements)

        body = self.find_child_by_field(node, 'body')
        new_body = []

        self.parse(body, new_body)

        statements.append({ 'case_stmt': { 'condition': shadow_condition, 'body': new_body }})

    def then_statement(self, node, statements):
        for child in node.named_children:
            self.parse(child, statements)

    def else_statement(self, node, statements):
        new_body = []
        for child in node.named_children:
            self.parse(child, new_body)
        statements.append({ 'default_stmt': { 'body': new_body }})

    def return_statement(self, node, statements):
        shadow_name = ""
        if node.named_child_count > 0:
            name = node.named_children[0]
            shadow_name = self.parse(name, statements)

        statements.append({"return_stmt": {"name": shadow_name}})
        return shadow_name

    def yield_statement(self, node, statements):
        shadow_name = ""
        if node.named_child_count > 0:
            name = node.named_children[0]
            shadow_name = self.parse(name, statements)

        statements.append({"return_stmt": {"name": shadow_name}})
        return shadow_name

    def undef_statement(self, node, statements):
        for child in self.read_node_text(node).split(','):
            statements.append({ 'del_stmt': { 'name': child }})

    def parse_call_receiver(self, node, statements):
        receiver = self.find_child_by_field(node, 'receiver')
        remaining_content = self.read_node_text(node).split('.')

        receiver_object = remaining_content[0]
        remaining_content = remaining_content[1:]

        for shadow_name in remaining_content:
            tmp_var = self.tmp_variable()
            statements.append({"field_read": {"target": tmp_var, "receiver_object": receiver_object , "field": shadow_name}})
            receiver_object = tmp_var

        return receiver_object

    def parse_element_reference(self, node, statements):
        myobject = self.find_child_by_field(node, "object")
        shadow_object = self.parse(myobject, statements)

        # Ruby grammar.js doesn't put a named field for index
        # TODO: make this work for multikeys reference
        key = node.children[2:-1][0]
        shadow_key = self.parse(key, statements)

        return shadow_object, shadow_key
