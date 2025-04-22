#!/usr/bin/env python3

import re
import struct
import ast
import dataclasses

from lian.apps.app_template import EventData
from lian.util import util
import lian.apps.event_return as er
from lian.config import type_table
from lian.config.constants import (
    LianInternal
)

WORD_CHARACTERS_CONFIG = {
    'php'           : r'a-zA-Z0-9_$',
    'javascript'    : r'a-zA-Z0-9_$',

    "default"       : r'a-zA-Z0-9_'
}

THIS_NAME_CONFIG = {
    "php"           : "$this",
    "default"       : "this",
}

def replace_percent_symbol_in_mock(data: EventData):
    code = data.in_data
    pattern = r'([a-zA-Z0-9])%([a-zA-Z])'
    def replacement(match):
        a = match.group(1)
        b = match.group(2)
        return f'{a}_1_{b}'
    data.out_data = re.sub(pattern, replacement, code)

    return er.EventHandlerReturnKind.SUCCESS

def remove_php_comments(data: EventData):
    code = data.in_data
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'//.*?\n', '\n', code)
    data.out_data = code
    return er.EventHandlerReturnKind.SUCCESS

def preprocess_php_namespace(data: EventData):
    code = data.in_data
    pattern = r'^(?P<indent>\s*)namespace\s+(?P<name>[^;]+);(?P<after_indent>\s*)(?P<code>.*?)(?=\n\s*namespace\s+|\Z|\?>)'

    def replacer(match):
        indent = match.group('indent')
        name = match.group('name').strip()
        after_indent = match.group('after_indent')
        code = match.group('code').strip()
        return f'{indent}namespace {name} {{\n{indent}{after_indent}{code}\n{indent}}}\n'

    modified_code = re.sub(pattern, replacer, code, flags=re.DOTALL | re.MULTILINE)
    data.out_data = modified_code
    return er.EventHandlerReturnKind.SUCCESS

def preprocess_php_namespace_2(data: EventData):
    code = data.in_data
    namespace_pattern = r'namespace\s+(\S+)\s*\{((?:(?!namespace\s+\S+\s*\{).)*)\}'

    def replacer(match):
        namespace_name = match.group(1)
        namespace_content = match.group(2).strip()

        pattern = r'\b(?<!\\)([a-zA-Z_][a-zA-Z0-9_]*(\\[a-zA-Z_][a-zA-Z0-9_]*))\b'

        def inner_replacer(match):
            name = match.group(1)
            return f'\\{namespace_name}\\{name}'

        modified_content = re.sub(pattern, inner_replacer, namespace_content, flags=re.MULTILINE | re.DOTALL)

        return f'namespace {namespace_name} {{\n{modified_content}\n}}'

    modified_code = re.sub(namespace_pattern, replacer, code, flags=re.MULTILINE | re.DOTALL)
    data.out_data = modified_code
    return er.EventHandlerReturnKind.SUCCESS

def preprocess_llvm_float_value(data: EventData):
    code = data.in_data
    matches = re.finditer(r'\b(float|bfloat|x86_fp80|fp128|ppc_fp128) 0x([0-9A-Fa-f]+)\b', code)
    for match in matches:
        float_name = match.group(1)
        hex_string = match.group(2)
        int_value = int(hex_string, 16)
        float_value = struct.unpack('>d', int_value.to_bytes(8, byteorder='big'))[0]
        formatted_float = float(format(float_value, ".4f"))
        code = code.replace(match.group(0), f"{float_name} {formatted_float}")
    data.out_data = code
    return er.EventHandlerReturnKind.SUCCESS

def preprocess_abc_loop(data: EventData):
    code = data.in_data
    label_pattern = re.compile(r"^jump_label_\d+:")
    jmp_pattern = re.compile(r"jmp\s+(jump_label_\d+)")
    print(code)
    # 用于存储已定义的 jump_label
    defined_labels = set()

    # 处理后的代码
    processed_lines = []

    # 逐行处理代码
    for line_number, line in enumerate(code.splitlines(), start=1):
        # 检查是否是 jump_label 的定义
        label_match = label_pattern.match(line.strip())
        if label_match:
            label = label_match.group(0)[:-1]  # 去掉冒号
            defined_labels.add(label)

        # 检查是否是 jmp 语句
        jmp_match = jmp_pattern.search(line)
        if jmp_match:
            target_label = jmp_match.group(1)
            if target_label in defined_labels:  # 如果目标标签已定义，说明是循环
                line = line.replace("jmp", "jmp_loop")

        # 添加到结果中
        processed_lines.append(line)

    # 输出结果
    processed_code = "\n".join(processed_lines)
    print(processed_code)

def preprocess_python_import_statements(data: EventData):
    # """
    # def a():
    #     import a.b.c, g
    #     a.b.c()
    #     g()

    # import l
    # import h.i.j, k.l.m, n
    # h.i.j.some_func()
    # k.l.m.other_func()
    # n.some_method()
    # a.b.c.e()

    # should be converted to ==============>>>>>>

    # """
    # def a():
    #     from a.b.c import a_b_c
    #     import g
    #     a_b_c()
    #     g()
    # import l
    # from h.i.j import h_i_j
    # from k.l.m import k_l_m
    # import n
    # h_i_j.some_func()
    # k_l_m.other_func()
    # n.some_method()
    # a_b_c.e()
    # """
    code = data.in_data
    lines = code.splitlines()  # Split code into lines for easier processing
    replacements = {}  # Dictionary to map original names to new names
    processed_lines = []  # To collect all processed lines of code

    # Track index where imports were originally found
    for line in lines:
        # Preserve leading spaces (indentation)
        stripped_line = line.lstrip()
        leading_spaces = line[:len(line) - len(stripped_line)]

        if stripped_line.startswith('import '):
            # Extract import names after 'import'
            import_names = re.sub(r"^import", "", stripped_line, count=1)
            import_names = import_names.split(',')
            import_names = [name.strip() for name in import_names]

            new_imports = []  # To collect new import lines

            # Process each import name
            for name in import_names:
                if '.' in name:
                    # Replace dots with underscores for names with dots
                    new_name = name.replace('.', '_')
                    replacements[name] = new_name
                    # Add new formatted import statement, preserving indentation
                    new_imports.append(f'{leading_spaces}from {name} import {new_name}')
                else:
                    # Keep original for names without dots, preserving indentation
                    new_imports.append(f'{leading_spaces}import {name}')

            # Add the transformed imports instead of the original line
            processed_lines.extend(new_imports)
        else:
            # Apply replacements for non-import lines
            for old_name, new_name in replacements.items():
                old_name = re.escape(old_name)
                # Replace old name with the new name in the current line
                if re.search(rf'\b{old_name}\b', line):
                    line = re.sub(rf'\b{old_name}\b', new_name, line)

            # Append the line after processing replacements
            processed_lines.append(line)

    # Rebuild the code from the processed lines
    data.out_data = '\n'.join(processed_lines)
    return er.EventHandlerReturnKind.SUCCESS

def replace_this(obj, this_name):
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (list, dict)):
                replace_this(item, this_name)
            elif isinstance(item, str) and item == this_name:
                obj[i] = LianInternal.THIS

    elif isinstance(obj, dict):
        for key, value in obj.items():
            if "key" == "attrs":
                continue

            if isinstance(value, (list, dict)):
                replace_this(value, this_name)
            elif isinstance(value, str) and value == this_name:
                obj[key] = LianInternal.THIS

def unify_this(data: EventData):
    code = data.in_data
    this_name = THIS_NAME_CONFIG.get(data.lang, THIS_NAME_CONFIG["default"])
    replace_this(code, this_name)
    data.out_data = code
    return er.EventHandlerReturnKind.SUCCESS

def find_python_method_first_parameter(method_decl):
    if "method_decl" in method_decl:
        method_decl = method_decl["method_decl"]
        if "parameters" in method_decl:
            parameters = method_decl["parameters"]
            counter = 0
            while counter < len(parameters):
                stmt = parameters[counter]
                if "parameter_decl" in stmt:
                    method_decl["parameters"] = parameters[counter + 1 :]
                    return stmt["parameter_decl"].get("name", "")

                counter += 1
    return ""

def adjust_python_self(obj, first_parameter_name = "", new_name = LianInternal.THIS, under_class_decl = False):
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (list, dict)):
                adjust_python_self(item, first_parameter_name, new_name, under_class_decl)
            elif under_class_decl and isinstance(item, str) and item == first_parameter_name:
                obj[i] = LianInternal.THIS

    elif isinstance(obj, dict):
        if "class_decl" in obj:
            current_class = obj["class_decl"]
            if "methods" in current_class:
                for each_method in current_class["methods"]:
                    first_one = find_python_method_first_parameter(each_method)
                    if first_one and "body" in each_method["method_decl"]:
                        adjust_python_self(each_method["method_decl"]["body"], first_one, under_class_decl = True)

        elif "method_decl" in obj:
            if "body" in obj["method_decl"]:
                adjust_python_self(obj["method_decl"]["body"])
        else:
            for key, value in obj.items():
                if key == "attrs":
                    continue
                if isinstance(value, (list, dict)):
                    adjust_python_self(value, first_parameter_name, new_name, under_class_decl)
                elif first_parameter_name and isinstance(value, str) and value == first_parameter_name:
                    obj[key] = LianInternal.THIS

def unify_python_self(data: EventData):
    code  = data.in_data
    adjust_python_self(code)
    data.out_data = code
    return er.EventHandlerReturnKind.SUCCESS

def add_main_func(data: EventData):
    in_data = data.in_data
    out_data = []
    top_stmts = []
    regular_stmts = []
    last_stmt_id = -1
    length = len(in_data)
    index = 0
    exclude_stmts = ("import_stmt", "from_import_stmt", "export_stmt")

    while index < length:
        stmt = in_data[index]
        last_stmt_id = max(last_stmt_id, stmt["stmt_id"])
        if stmt["parent_stmt_id"] == 0:
            if stmt["operation"].endswith("_decl") or stmt["operation"] in exclude_stmts:
                # if stmt["operation"] == "method_decl":
                #     top_stmts.append(stmt)
                regular_stmts.append(stmt)
                index += 1
            else:
                top_stmts.append(stmt)
                index += 1
                while index < length and in_data[index]["parent_stmt_id"] != 0:
                    cur_top_stmt = in_data[index]
                    top_stmts.append(cur_top_stmt)
                    last_stmt_id = max(last_stmt_id, cur_top_stmt["stmt_id"])
                    index += 1
        else:
            regular_stmts.append(stmt)
            index += 1
    out_data = regular_stmts

    if len(top_stmts) == 0:
        return

    main_method_stmt_id = last_stmt_id + 1
    main_method_body_id = last_stmt_id + 2
    out_data.append({
        'operation': 'method_decl',
        'parent_stmt_id': 0,
        'stmt_id': main_method_stmt_id,
        'name': LianInternal.UNIT_INIT,
        'body': main_method_body_id
    })

    out_data.append({
        'operation': 'block_start',
        'stmt_id': main_method_body_id,
        'parent_stmt_id': main_method_stmt_id
    })

    for stmt in top_stmts:
        if stmt["parent_stmt_id"] == 0:
            stmt["parent_stmt_id"] = main_method_body_id
        out_data.append(stmt)

    out_data.append({
        'operation': 'block_end',
        'stmt_id': main_method_body_id,
        'parent_stmt_id': main_method_stmt_id
    })

    data.out_data = out_data
    return er.EventHandlerReturnKind.SUCCESS

def remove_unnecessary_tmp_variables(data: EventData):
    in_data = data.in_data
    i = 1
    length = len(in_data)

    key_stmts = (
        "array_read",
        "assign_stmt",
        "call_stmt",
        "addr_of",
        "field_read",
        "asm_stmt",
        "mem_read",
        "type_cast_stmt",
        "new_object"
    )

    while i < length:
        pre_stmt = in_data[i - 1]
        stmt = in_data[i]
        if (
            stmt["operation"] == "assign_stmt"
            and not stmt.get("operand2", "")
            and pre_stmt.get("target")
            and pre_stmt["operation"] in key_stmts
            and pre_stmt["target"].startswith(LianInternal.VARIABLE_DECL_PREF)
            and (stmt["operand"] == pre_stmt["target"])
        ):
            pre_stmt["target"] = stmt["target"]
            del in_data[i]
            length -= 1

        i += 1

    data.out_data = in_data

def unify_data_type(data: EventData):
    code = data.in_data

    type_info = type_table.get_lang_type_table(data.lang)
    if type_info:
        for row in code:
            if "data_type" not in row or not row["data_type"]:
                continue

            dt = row["data_type"]
            if "*" in dt or "[" in dt:
                for i in range(len(dt) - 1, -1, -1):
                    if dt[i] == '*':
                        row["data_type"] = dt[:i]
                        if "attrs" not in row:
                            attrs = []
                        else:
                            attrs = ast.literal_eval(row["attrs"])
                        util.add_to_dict_with_default_list(row, "attrs", LianInternal.POINTER)
                        break
                    elif dt[i] == '[':
                        row["data_type"] = dt[:i]
                        if "attrs" not in row:
                            attrs = []
                        else:
                            attrs = ast.literal_eval(row["attrs"])
                        attrs.append(LianInternal.ARRAY)
                        row["attrs"] = str(attrs)
                        break

            dt = row["data_type"]
            if dt in type_info:
                row["data_type"] = type_info[dt]

    data.out_data = code
    return er.EventHandlerReturnKind.SUCCESS


@dataclasses.dataclass
class ElementToBeDeleted:
    index: int = -1
    need_hoist: bool = False
    is_global: bool = False

@dataclasses.dataclass
class StackFrame:
    stmts: list = dataclasses.field(default_factory=list)
    index: int = -1
    variables: list = dataclasses.field(default_factory=list)
    to_be_deleted: list = dataclasses.field(default_factory=list)
    in_block: bool = False

def adjust_variable_decls(data: EventData):
    out_data = data.in_data

    stack = []
    global_variable = []
    python_variable_hoist = []

    def add_stack(stmts, index, variables, to_be_deleted, in_block):
        stack.append(StackFrame(stmts, index, variables, to_be_deleted, in_block))

    add_stack(stmts = out_data, index = 0, variables = {}, to_be_deleted = [], in_block = False)

    while stack:
        frame: StackFrame = stack.pop()
        stmts = frame.stmts
        index = frame.index
        available_variables = frame.variables
        to_be_deleted = frame.to_be_deleted
        in_block = frame.in_block
        has_done = True
        for child_index in range(index, len(stmts)):
            stmt = stmts[child_index]
            key = list(stmt.keys())[0]
            value = stmt[key]

            if key == "variable_decl":
                variable_name = value["name"]
                if data.lang in ["python", "abc", "safe"]:
                # if data.lang == "python" or data.lang == "abc":
                    if variable_name in available_variables:
                        to_be_deleted.append(ElementToBeDeleted(child_index, False, False))
                    else:
                        # if data.lang == "safe" and child_index < len(stmts) - 1:
                        #     next_stmt = stmts[child_index + 1]
                        #     next_key = list(next_stmt.keys())[0]
                        #     if next_key == "assign_stmt":
                        #         assign_body = next_stmt[next_key]
                        #         print(f"assign_body: {assign_body}")
                        #         assign_stmt_id = assign_body["stmt_id"]
                        #         value["from"] = assign_stmt_id

                        if in_block:
                            if data.lang != "safe":
                                to_be_deleted.append(ElementToBeDeleted(child_index, True, False))
                        available_variables[variable_name] = True

                        # to_be_deleted.append(ElementToBeDeleted(child_index, True, False))
                        # available_variables[variable_name] = True
                else:
                    attrs = value["attrs"]
                    if "var" in attrs:
                        if variable_name in available_variables:
                            to_be_deleted.append(ElementToBeDeleted(child_index, True, False))
                        else:
                            available_variables[variable_name] = True
                            to_be_deleted.append(ElementToBeDeleted(child_index, True, False))
                    elif "global" in attrs:
                        if variable_name in available_variables:
                            to_be_deleted.append(ElementToBeDeleted(child_index, False, False))
                        else:
                            available_variables[variable_name] = True
                            to_be_deleted.append(ElementToBeDeleted(child_index, False, True))
                    elif "let" in attrs or "const" in attrs:
                        if variable_name in available_variables:
                            to_be_deleted.append(ElementToBeDeleted(child_index, False, False))
                        else:
                            available_variables[variable_name] = False

            elif key in ("global_stmt", "nonlocal_stmt"):
                if "name" in value:
                    variable_name = value["name"]
                    if variable_name in available_variables:
                        util.error("global or nonlocal variable <%s> has defined!" % variable_name)
                    else:
                        available_variables[variable_name] = True

            elif key in ("class_decl", "interface_decl", "record_decl", "annotation_type_decl", "enum_decl", "struct_decl"):
                has_save_breakpoints = False
                if "methods" in value and value["methods"]:
                    if not has_save_breakpoints:
                        has_save_breakpoints = True
                        add_stack(stmts, child_index + 1, available_variables, to_be_deleted, in_block)
                    add_stack(value["methods"], 0, {}, [], False)
                    has_done = False

                if "fields" in value and value["fields"]:
                    if not has_save_breakpoints:
                        has_save_breakpoints = True
                        add_stack(stmts, child_index + 1, available_variables, to_be_deleted, in_block)
                    add_stack(value["fields"], 0, {}, [], False)
                    has_done = False

                if "nested" in value and value["nested"]:
                    if not has_save_breakpoints:
                        has_save_breakpoints = True
                        add_stack(stmts, child_index + 1, available_variables, to_be_deleted, in_block)
                    add_stack(value["nested"], 0, {}, [], False)
                    has_done = False

                if has_save_breakpoints:
                    break

            elif key == "struct_decl":
                body = value["fields"]
                if not body:
                    continue
                add_stack(stmts, child_index + 1, available_variables, to_be_deleted, in_block)
                add_stack(body, 0, {}, [], False)
                has_done = False
                break

            elif key == "method_decl":
                available_variables[value["name"]] = True
                parameters = []
                if "parameters" in value:
                    parameters = value["parameters"]
                method_available_variable_name_list = {}
                if parameters:
                    for parameter_stmt in parameters:
                        parameter_key = list(parameter_stmt.keys())[0]
                        parameter_value = parameter_stmt[parameter_key]
                        if parameter_key == "parameter_decl":
                            variable_name = parameter_value["name"]
                            method_available_variable_name_list[variable_name] = True

                body = value["body"]
                if not body:
                    continue

                add_stack(stmts, child_index + 1, available_variables, to_be_deleted, in_block)
                add_stack(body, 0, method_available_variable_name_list, [], False)
                has_done = False
                break

            elif key.endswith("_stmt"):
                has_save_breakpoints = False
                for stmt_key, stmt_value in value.items():
                    if stmt_key.endswith("body"):
                        if not has_save_breakpoints:
                            has_save_breakpoints = True
                            add_stack(stmts, child_index + 1, available_variables, to_be_deleted, in_block)
                        if data.lang == "safe":
                            add_stack(stmt_value, 0, {}, [], True)
                        else:
                            add_stack(stmt_value, 0, available_variables, [], True)
                        has_done = False
                if has_save_breakpoints:
                    break

        if has_done:
            to_be_delete_index_sorted = sorted(to_be_deleted, key=lambda x: x.index, reverse=True)
            if data.lang == "python":
                for element in to_be_delete_index_sorted:
                    if element.need_hoist:
                        python_variable_hoist.append(stmts.pop(element.index))
                    else:
                        stmts.pop(element.index)

                if not in_block:
                    for stmt in python_variable_hoist:
                        stmts.insert(0, stmt)
                    python_variable_hoist = []
            else:
                variable_hositing = []
                for element in to_be_delete_index_sorted:
                    if element.need_hoist:
                        variable_hositing.append(stmts.pop(element.index))
                    else:
                        if element.is_global:
                            global_variable.append(stmts.pop(element.index))
                        else:
                            stmts.pop(element.index)
                for stmt in variable_hositing:
                    stmts.insert(0, stmt)

                keys = list(available_variables.keys())
                for key in keys:
                    if not available_variables[key]:
                        del available_variables[key]

    for stmt in global_variable:
        out_data.insert(0, stmt)

    data.out_data = out_data
    return er.EventHandlerReturnKind.SUCCESS

