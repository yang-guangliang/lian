import dataclasses

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
        stmts = [d for stmt in stmts for d in (stmt if isinstance(stmt, list) else [stmt])]
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
                if data.lang in ["python", "abc"]:
                # if data.lang == "python" or data.lang == "abc":
                    if variable_name in available_variables:
                        to_be_deleted.append(ElementToBeDeleted(child_index, False, False))
                    else:

                        if in_block:
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

