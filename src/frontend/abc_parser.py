#!/usr/bin/env python3
import sys, os

from lian.config import config
from lian.lang import common_parser
from lian.config.constants import LianInternal

class ABCParser(common_parser.Parser):

    def init(self):
        self.DECLARATION_HANDLER_MAP = {
            "function_declaration"          : self.function_declaration,
            # "variable_declaration"          : self.variable_declaration
        }

        self.STATEMENT_HANDLER_MAP = {
            "assignment_statement"          : self.assignment_statement,
            "sta_statement"                 : self.sta_statement,
            "lda_statement"                 : self.lda_statement,
            "ldastr_statement"              : self.ldastr_statement,
            "ldtrue_statement"              : self.ldtrue_statement,
            "ldlexvar_statement"            : self.ldlexvar_statement,
            "ldundefiened_statement"        : self.ldundefiened_statement,
            "ldai_statement"                : self.ldai_statement,
            "ldobjbyname_statement"         : self.ldobjbyname_statement,
            "ldexternalmodulevar_statement" : self.ldexternalmodulevar_statement,
            "ldhole_statement"              : self.ldhole_statement,
            "ldnull_statement"              : self.ldnull_statement,
            "call_statement"                : self.call_statement,
            "callthis1_statement"           : self.call_statement,
            "callthis2_statement"           : self.call_statement,
            "callthis3_statement"           : self.call_statement,
            "callarg1_statement"            : self.call_statement,
            "callargs2_statement"           : self.call_statement,
            "callargs3_statement"           : self.call_statement,
            "definefunc_statement"          : self.definefunc_statement,
            "definemethod_statement"        : self.definemethod_statement,
            "definefieldbyname_statement"   : self.definefieldbyname_statement,
            "defineclass_statement"         : self.defineclass_statement,
            "mov_statement"                 : self.mov_statement,
            "tryldglobalbyname_statement"   : self.tryldglobalbyname_statement,
            "stlexvar_statement"            : self.stlexvar_statement,
            "stmodulevar_statement"         : self.stmodulevar_statement,
            "stownbyindex_statement"        : self.stownbyindex_statement,
            "stownbyname_statement"         : self.stownbyname_statement,
            "stobjbyname_statement"         : self.stobjbyname_statement,
            "cmp_statement"                 : self.cmp_statement,
            "if_statement"                  : self.if_statement,
            "ifhole_statement"              : self.ifhole_statement,    
            "returnundefined_statement"     : self.returnundefined_statement,
            "return_statement"              : self.return_statement,
            "new_array_statement"           : self.new_array_statement,
            "newobjrange_statement"         : self.newobjrange_statement,
            "newenv_statement"              : self.newenv_statement,
            "add_statement"                 : self.add_statement,
            "tonumeric_statement"           : self.tonumeric_statement,
            "ifhole_statement"              : self.ifhole_statement,
            "condition_statement"           : self.condition_statement,
            "strictnoteq_statement"         : self.strictnoteq_statement,
            "stricteq_statement"            : self.stricteq_statement,
            "inc_statement"                 : self.inc_statement,
            "while_statement"               : self.while_statement,
            "copyrestargs_statement"        : self.copyrestargs_statement, 
            "supercallspread_statement"     : self.supercallspread_statement,
            "throwcallwrong_statement"      : self.throwcallwrong_statement,
            "neg_statement"                 : self.neg_statement,
            "asyncfunctionenter_statement"  : self.asyncfunctionenter_statement,
            "asyncfunctionawaituncaught_statement":self.asyncfunctionawaituncaught_statement,
            "asyncfunctionreject_statement" : self.asyncfunctionreject_statement,
            "asyncfunctionresolve_statement": self.asyncfunctionresolve_statement,
            "suspendgenerator_statement"    : self.suspendgenerator_statement,
            "getresumemode_statement"       : self.getresumemode_statement,
            "createemptyarray_statement"    : self.createemptyarray_statement,
            "createobjectwithbuffer_statement": self.createobjectwithbuffer_statement,
            "createemptyobject_statement"   : self.createemptyobject_statement,
            "isin_statement"                : self.isin_statement,

               
        }

        self.EXPRESSION_HANDLER_MAP = {
            "expression"                    : self.expression_wrapper,  
            "identifier"                    : self.identifier_expression,  
            "parenthesized_lvalue"          : self.parenthesized_lvalue_expression,  
            "isfalse_expression"            : self.isfalse_expression,
            
        }

    def check_expression_handler(self, node):
        return self.EXPRESSION_HANDLER_MAP.get(node.type, None)

    def check_declaration_handler(self, node):
        return self.DECLARATION_HANDLER_MAP.get(node.type, None)

    def check_statement_handler(self, node):
        return self.STATEMENT_HANDLER_MAP.get(node.type, None)
    
    def function_declaration(self, node, statements):
        header_node = self.find_child_by_type(node, "function_header")
        header_info = self.function_header(header_node)
        body_statements = []
        body_node = self.find_child_by_type(node, "function_body")
        
        body_statements = self.function_body(body_node)
       
        statements.append({
            "method_decl": {
                **header_info,
                "body": body_statements
            }
        })
            
        return

    def function_header(self, node):
        name_node = self.find_child_by_field(node, "name")
        function_name = self.read_node_text(name_node) 

        parameters = []
        params_node = self.find_child_by_field(node, "parameters")
        explicit_params_node = params_node.named_children[3:] 
        if explicit_params_node:
            for param_node in explicit_params_node:
                param_info = self.parameter(param_node)
                parameters.append(param_info)

        # return_type_node = self.find_child_by_field(node, "return_type")
        # if return_type_node:
        #     return_type = self.type_expression(return_type_node)
        # else:
        #     return_type = None

        return {
            # "data_type": return_type,
            "name": function_name,
            "parameters": parameters,
        }

    def function_body(self, node):
        body_statements = []
        for child in node.named_children:
            # if self.is_declaration(child):
            #     self.declaration(child, body_statements)
            # if self.is_statement(child):
            self.statement(child, body_statements)
    
        return body_statements

    def parameter(self, node):

        name_node = self.find_child_by_field(node, "name")
        param_name = self.read_node_text(name_node)
        type_node = self.find_child_by_field(node, "type")
        param_type = self.type_expression(type_node)

        return {
            "parameter_decl": {
                "data_type": param_type,
                "name": param_name,
            }
        }

    def type_expression(self, node):
        if node.type == "primitive_type":
            return self.read_node_text(node)
        elif node.type == "tuple_type":
            elements = [self.type_expression(child) for child in node.named_children]
            return f"({', '.join(elements)})"
        else:
            return self.read_node_text(node)


    def assignment_statement(self, node, statements):
        left_node = self.find_child_by_field(node, "left")
        right_node = self.find_child_by_field(node, "right")

        left_expr = self.lvalue(left_node, statements) if left_node else None

        if right_node:
            right_expr = self.expression(right_node, statements)
        else:
            right_expr = None

        statements.append({
            "assign_stmt": {
                "target": left_expr,
                "operand": right_expr
            }
        })

    def return_statement(self, node, statements):
        value_node = self.find_child_by_field(node, "value")
        value = self.expression(value_node, statements) if value_node else None

        statements.append({
            "return_stmt": {
                "operand": value
            }
        })

    def call_statement(self, node, statements):
        call_type = node.type

        if call_type == "callthis1_statement" or call_type == "callthis2_statement" or call_type == "callthis3_statement":
            arguments_nodes = node.named_children[2:]
        elif call_type == "callarg1_statement" or call_type == "callargs2_statement" or call_type == "callargs3_statement" :
            arguments_nodes = node.named_children[1:]
        else:
            arguments_nodes = []
        arguments = []
        for arg_node in arguments_nodes:
            arguments.append(self.read_node_text(arg_node))

        statements.append({
            "call_stmt": {
                "target": "acc",
                "name": "acc",
                "positional_args": arguments
            }
        })


    def sta_statement(self, node, statements):
        register_node = self.find_child_by_field(node, "register")
        register_name = self.read_node_text(register_node)
        statements.append({
            "variable_decl": {
                "name":register_name,
            }
        })
        statements.append({
            "assign_stmt": {
                "operand":"acc",
                "target":register_name
            }
        })

    def lda_statement(self, node, statements):
        register_node = self.find_child_by_field(node, "register")
        register_name = self.read_node_text(register_node)
        statements.append({
            "variable_decl": {
                "name":register_name,
            }
        })
        statements.append({
            "assign_stmt": {
                "operand":register_name,
                "target":"acc"
            }
        })
    
    def ldastr_statement(self, node, statements):
        string_node = node.named_children[0]
        string = self.read_node_text(string_node)
        statements.append({
            "assign_stmt": {
                "operand":f'"{string}"',
                "target":"acc"
            }
        })

    def ldai_statement(self, node, statements):
        imm_node = self.find_child_by_field(node, "imm")
        imm = self.read_node_text(imm_node)
        statements.append({
            "assign_stmt": {
                "operand":imm,
                "target":"acc"
            }
        })

    def ldhole_statement(self, node, statements):
        statements.append({
            "assign_stmt": {
                "operand":"hole",
                "target":"acc"
            }
        })
        
    def ldnull_statement(self, node, statements):
        statements.append({
            "assign_stmt": {
                "operand":"null",
                "target":"acc"
            }
        })
    
    def mov_statement(self, node, statements):
        v1_node = self.find_child_by_field(node, "v1")
        v2_node = self.find_child_by_field(node, "v2")
        v1_name = self.read_node_text(v1_node)
        v2_name = self.read_node_text(v2_node)
        statements.append({
            "assign_stmt": {
                "operand":v2_name,
                "target":v1_name
            }
        })
    def callarg0_statement(self, node, statements):
        statements.append({
            "call_stmt": {
                "name":"acc",
                "target":"acc"
            }
        })
    
    def callthis1_statement(self, node, statements):
        argument_list = []
        argument_node = self.find_child_by_field(node, "arg1")
        argument_name = self.read_node_text(argument_node)
        argument_list.append(argument_name)
        statements.append({
            "call_stmt": {
                "name":"acc",   
                "target":"acc",
                "positional_args":argument_list,
            }
        })

    def tryldglobalbyname_statement(self, node, statements):
        object_field = self.find_child_by_field(node, "object")
        object_name = self.read_node_text(object_field)
        statements.append({
            "variable_decl": {
                "name":"acc"
            }
        })
        statements.append({
            "assign_stmt": {
                "operand":object_name,
                "target":"acc"
            }
        })

    def ldlexvar_statement(self, node, statements):
        lexi_env_node = self.find_child_by_field(node, "lexi_env")
        slot_node = self.find_child_by_field(node, "slot")
        lexi_env = self.read_node_text(lexi_env_node)
        slot = self.read_node_text(slot_node)
        statements.append({
            "array_read":{
                "name":lexi_env,
                "index":slot,
                "type":"ldlex",
                "target":"acc"
            }
        })
        
    def stlexvar_statement(self, node, statements):
        lexi_env_node = self.find_child_by_field(node, "lexi_env")
        slot_node = self.find_child_by_field(node, "slot")
        lexi_env = self.read_node_text(lexi_env_node)
        slot = self.read_node_text(slot_node)
        slot_deci = int(slot, 16)
        statements.append({
            "array_write":{
                "index":str(slot_deci),
                "type":"ldlex",
                "source":"acc",
                "array":"current_env"
            }
        })
    
    def stmodulevar_statement(self, node, statements):
        pass

    def stownbyindex_statement(self, node, statements):
        object_node = self.find_child_by_field(node, "object")
        field_node = self.find_child_by_field(node, "index")
        object_name = self.read_node_text(object_node)
        field_name = self.read_node_text(field_node)
        statements.append({
            "field_write":{
                "source":"acc",
                "receiver_object":object_name,
                "field":field_name,
            }
        })

# 将acc中的值存放到对象B的键值为索引A对应的字符串的属性上。
    def stownbyname_statement(self, node, statements):
        object_node = self.find_child_by_field(node, "object")
        field_node = self.find_child_by_field(node, "name")
        object_name = self.read_node_text(object_node)
        field_name = self.read_node_text(field_node)
        statements.append({
            "record_write":{
                "value":"acc",
                "receiver_record":object_name,
                "key":field_name,
            }
        })
# 将acc中的值存放到对象B的键值为索引A对应的字符串的属性上。
    def stobjbyname_statement(self, node, statements):
        object_node = self.find_child_by_field(node, "object")
        field_node = self.find_child_by_field(node, "name")
        object_name = self.read_node_text(object_node)
        field_name = self.read_node_text(field_node)
        statements.append({
            "record_write":{
                "value":"acc",
                "receiver_record":object_name,
                "key":field_name,
            }
        })
    
    def cmp_statement(self, node, statements):
        pass

    # 根据名称查找对象语句
    def ldobjbyname_statement(self, node, statements):
        field_node = self.find_child_by_field(node, "object")
        field_name = self.read_node_text(field_node)
        statements.append({
            "field_read":{
                "receiver_object":"acc",
                "field":field_name,
                "target":"acc"
            }
        })
        
# 如果acc中的值是hole，则抛出异常：A的值是undefined。
    def ifhole_statement(self, node, statements):
        pass

    def ldundefiened_statement(self, node, statements):
        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": "undefined"
            }
        })

    def returnundefined_statement(self, node, statements):
        statements.append({
            "return_stmt": {
                "operand": "undefined"
            }
        })

    def return_statement(self, node, statements):
        statements.append({
            "return": {
                "name": "acc"
            }
        })

    def definefunc_statement(self, node, statements):
        name_node = self.find_child_by_field(node, "name")
        name = self.read_node_text(name_node)
        statements.append({
            "variable_decl": {
                "name":"acc"
            }
        })
        statements.append({
            "assign_stmt": {
                "target":"acc",
                "operand":name
            }
        })

    def definemethod_statement(self, node, statements):
        pass
    
    def definefieldbyname_statement(self, node, statements):
        field_node = self.find_child_by_field(node, "field")
        object_node = self.find_child_by_field(node, "object")
        field = self.read_node_text(field_node)
        object = self.read_node_text(object_node)
        statements.append({
            "field_write": {
                "receiver_object"   : object,
                "field"             : field,
                "source"            : "acc"}
        })

# this instruction has not finished yet
    def defineclass_statement(self, node, statements):
        self.print_tree(node)
        parent_node = self.find_child_by_field(node, "super")
        method_node = self.find_child_by_type(node, "literal")
        constructor_node = self.find_child_by_field(node, "class_name")
        prefix_name_node = self.find_child_by_type(constructor_node, "dot_separated_identifiers")
        path_node = prefix_name_node.named_children[-1]
        print("prefix_name_node", path_node)
        name_node = path_node
        class_name = self.read_node_text(name_node)
        gir_node = {}
        statements.append({
            "class_decl": {
                "methods": gir_node,
                "fields": gir_node,
                "nested":gir_node,
            }
        })

    def new_array_statement(self, node, statements):
        array_node = self.find_child_by_type(node, "literal")
        length_node = self.find_child_by_field(array_node, "length")
        length = self.read_node_text(length_node)
        print(array_node.named_children[0])
        tmp_var = self.tmp_variable()
        statements.append({"new_array": {"target": tmp_var}})
        for index, element_node in enumerate(array_node.named_children):
            if index > 0:
                value_node = element_node.named_children[1]
                value = self.read_node_text(value_node)
                statements.append({
                    "array_write": {
                        "array": tmp_var, 
                        "index": str(index), 
                        "source": value
                    }
                })
        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": tmp_var
            }
        })

    def newobjrange_statement(self, node, statements):
        pass

    def newenv_statement(self, node, statements):
        statements.append({
            "new_array": {
                "name":"current_env",
            }
        })
        children = node.named_children
        # for i in range(3, len(children), 2):
        #     literal_children = children[i].named_children
        #     literal = self.read_node_text(literal_children[1])
        #     statements.append({
        #         "record_write":{
        #             "receiver_record":"current_env",
        #             "key":literal,
        #             "value":"uninit"
        #         }
        #     })

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
    
    def jnez_statement(self, node, statements):
        pass

    def jmp_statement(self, node, statements):
        pass

    def isfalse_expression(self, node, statements):
        ACC = "acc"
        statements.append({
            "assign_stmt": {
                "target": ACC,
                "operand": "false",
                "operand2": ACC,
                "operator": "=="
            }
        })
        return ACC
    
    def add_statement(self, node, statements):
        register_node = self.find_child_by_field(node, "register")
        register_name = self.read_node_text(register_node)

        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": "acc",
                "operand2": register_name,
                "operator": "+"
            }
        })
        return "acc"
    
    def tonumeric_statement(self, node, statements):
        pass

    def ifhole_statement(self, node, statements):
        pass

    def condition_statement(self, node, statements):
        register_node = self.find_child_by_field(node, "register")
        register_name = self.read_node_text(register_node)
        
        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": "acc",
                "operand2": "register_name",
                "operator": "!="
            }
        })
    def stricteq_statement(self, node, statements):
        register_node = self.find_child_by_field(node, "register")
        register_name = self.read_node_text(register_node)
        
        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": "acc",
                "operand2": register_name,
                "operator": "=="
            }
        })
    def strictnoteq_statement(self, node, statements):
        pass

    def inc_statement(self, node, statements):
        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": "acc",
                "operand2": "1",
                "operator": "+"
            }
        })

    def while_statement(self, node, statements):
        pass

    def copyrestargs_statement(self, node, statements):
        statements.append({
            "assign_stmt": {
                "target": "acc",
            }
        })

    def supercallspread_statement(self, node, statements):
        statements.append({
            "call_stmt": {
                
            }
        })

    def throwcallwrong_statement(self, node, statements):
        pass

    def asyncfunctionenter_statement(self, node, statements):
        pass

    def neg_statement(self, node, statements):
        pass

    def asyncfunctionawaituncaught_statement(self, node, statements):
        pass

    def asyncfunctionreject_statement(self, node, statements):
        pass

    def asyncfunctionresolve_statement(self, node, statements):
        pass

    def suspendgenerator_statement(self, node, statements):
        pass

    def getresumemode_statement(self, node, statements):
        pass

    def createemptyarray_statement(self, node, statements):
        statements.append({
            "new_array": {
                "target":"acc",
            }
        })

    def createobjectwithbuffer_statement(self, node, statements):
        pass

    def createemptyobject_statement(self, node, statements):
        pass

    def isin_statement(self, node, statements):
        pass

    def ldexternalmodulevar_statement(self, node, statements):
        slot_node = self.find_child_by_field(node, "slot")
        slot_name = self.read_node_text(slot_node)
        statements.append({
            "array_read":{
                "array":"current_env",
                "index":slot_name,
                "target":"acc"
            }
        })

    def ldtrue_statement(self, node, statements):
        statements.append({
            "assign_stmt": {
                "target": "acc",
                "operand": "true"
            }
        })
        

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

    def literal(self, node, statements, replacement):
        handler = self.obtain_literal_handler(node)
        return handler(node, statements, replacement)

    def expression(self, node, statements):
        handler = self.check_expression_handler(node)

        return handler(node, statements)
     

    def declaration(self, node, statements):
        handler = self.check_declaration_handler(node)
        return handler(node, statements)

    def statement(self, node, statements):
        # self.print_tree(node)
        if (node.type == "statement"):
            node = node.children[0]

        handler = self.check_statement_handler(node)
        return handler(node, statements)

