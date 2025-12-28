import dataclasses
import lian.events.event_return as er
from lian.util import util
from lian.events.handler_template import EventData
from lian.config.constants import LIAN_INTERNAL


@dataclasses.dataclass
class StackFrame:
    # default_factory=dict/list，防止多个StackFrame共享同一个可变默认对象。
    stmts: list
    variables: dict = dataclasses.field(default_factory=dict)
    in_block: bool = False
    hoist_collector: list = dataclasses.field(default_factory=list) # 收集需要提升位置的variable_decl，在层级遍历结束后插入到开头（Python/ABC插入到函数/类开头，其他语言插入到 block 开头）
    index: int = 0
    to_delete_indices: list = dataclasses.field(default_factory=list) 

def remove_unnecessary_tmp_variables(data: EventData):
    """
    移除不必要的临时变量。
    在UNFLATTENED_GIR_LIST_GENERATED阶段，GIR还是树状结构（未扁平化），
    因此需要通过递归遍历所有层级的列表来执行优化。
    """
    in_data = data.in_data
    recursive_remove_tmp_vars(in_data)
    data.out_data = in_data

def recursive_remove_tmp_vars(obj):
    """
    递归遍历GIR对象，在所有列表层级执行临时变量消除。
    对于列表：先处理当前层级的优化，再递归处理子元素。
    对于字典：递归处理所有值。
    """
    if isinstance(obj, list):
        # 先处理当前列表层级的消除逻辑
        remove_unnecessary_tmp_variables_in_list(obj)
        # 然后递归深入子元素
        for item in obj:
            recursive_remove_tmp_vars(item)
    elif isinstance(obj, dict):
        # 如果是字典，递归处理其所有值
        for value in obj.values():
            recursive_remove_tmp_vars(value)

def extract_stmt_info(stmt_dict):
    """
    从GIR语句字典中提取操作类型和内容。
    在UNFLATTENED阶段，GIR 格式为: {"操作类型": {内容}}
    例如: {"assign_stmt": {"target": "x", "operand": "y"}}
    Returns:
        tuple: (操作类型, 内容字典)，如果格式不正确则返回 (None, None)
    """
    if not isinstance(stmt_dict, dict) or not stmt_dict:
        return None, None
    op = list(stmt_dict.keys())[0]
    content = stmt_dict[op]
    return (op, content) if isinstance(content, dict) else (None, None)

def remove_unnecessary_tmp_variables_in_list(stmts: list):
    """
    在语句列表中消除冗余的临时变量赋值。
    
    优化目标：
      将 %v1 = expr; ...; d = %v1 合并为 d = expr; ...
    
    实现步骤为三步：
      1. 从后往前遍历语句列表，定位 d = %v1 形式的赋值语句。
      2. 锁定目标后，向回滑动搜索定义 %v1 的语句。
      3. 搜索过程中：
         - 若遇到 variable_decl，跳过（视为不影响数据流的元数据）。
         - 若找到定义 %v1 的语句且操作类型允许优化，则执行合并并删除原赋值语句。
         - 若遇到其他阻断语句（数据流不连续），停止搜索，确保语义安全。
    """
    if len(stmts) < 2:
        return
    
    # 能产生临时变量的语句类型
    CAN_OPTIMIZE_OPS = {
        "array_read", "assign_stmt", "call_stmt", "addr_of", 
        "field_read", "asm_stmt", "mem_read", "type_cast_stmt", "new_object"
    }
    
    # 从后往前遍历，这样删除元素不会影响前面的索引
    for i in range(len(stmts) - 1, 0, -1):
        curr_op, curr_content = extract_stmt_info(stmts[i])
        if (curr_op != "assign_stmt" 
            or not curr_content 
            or curr_content.get("operand2") 
            or curr_content.get("operator")):
            continue
        
        final_target = curr_content.get("target")
        temp_var = curr_content.get("operand")
        
        if (not temp_var or not temp_var.startswith(LIAN_INTERNAL.VARIABLE_DECL_PREF)):
            continue

        """
        将 %v1 = expr; ...; d = %v1 合并为 d = expr; ...
        目前通过实验发现冗余赋值语句之间都是0条语句或者1条语句隔开的，为了避免存在更复杂的情况并考虑到性能，将回溯的步数设为3。
        """
        LOOKBACK_LIMIT = 3
        search_limit = max(-1, i - 1 - LOOKBACK_LIMIT)
        found_optimization = False
        
        for k in range(i - 1, search_limit, -1):
            prev_op, prev_content = extract_stmt_info(stmts[k])
            if not prev_op:
                break 
            if prev_op == "variable_decl":
                continue
            prev_target = prev_content.get("target")
            if (prev_target == temp_var 
                and prev_op in CAN_OPTIMIZE_OPS):
                prev_content["target"] = final_target
                del stmts[i]
                found_optimization = True
                break
            break #遇到了非定义和非冗余处理的语句，说明数据流被打断了，就停止搜索。


def adjust_variable_decls(data: EventData):
    """
    调整变量声明：先清理临时变量，再处理变量声明的提升和去重。
    """
    # 第一步：先执行临时变量清理，优化 GIR 结构
    remove_unnecessary_tmp_variables(data)
    
    out_data = data.in_data
    is_python_like = data.lang in ["python", "abc"] # 特殊处理 Python 和 ABC 语言
    global_stmts_to_insert = []

    stack = [StackFrame(stmts=out_data)]

    while stack:
        frame = stack[-1] 

        # === 阶段 1: 检查当前帧是否处理完毕 ===
        if frame.index >= len(frame.stmts):
            stack.pop() # 移除当前帧
            finalize_frame(frame, is_python_like)
            continue

        # === 阶段 2: 获取当前语句并下移游标 ===
        stmt = frame.stmts[frame.index]
        current_stmt_index = frame.index
        frame.index += 1 

        if not isinstance(stmt, dict):
            continue
        
        key = list(stmt.keys())[0]
        value = stmt[key]

        # === 阶段 3: 处理语句逻辑 (生成子任务或处理变量) ===
        sub_frames = []
        
        '''       
         处理类型声明节点（class/interface/record/enum/struct...）时，由于这些节点本身不是一组可直接线性遍历的语句列表，
         真正需要继续往下扫描的，是它们内部存放成员的几个列表字段，如methods/fields/nested。
         这段代码的目的就是：把这些子列表变成新的 StackFrame(stmts=...) 压栈。
         '''
        if key in ("class_decl", "interface_decl", "record_decl", "annotation_type_decl", "enum_decl", "struct_decl"):
            for sub_key in ["methods", "fields", "nested"]:
                if sub_key in value and value[sub_key]:
                    sub_frames.append(StackFrame(stmts=value[sub_key]))

        elif key == "method_decl":
            # method_vars 用于把 形参名 当作已声明变量，避免在函数体里重复声明。
            method_vars: dict = {}
            if "parameters" in value:
                for param in value["parameters"]:
                    if isinstance(param, dict):
                        p_key = list(param.keys())[0]
                        if p_key == "parameter_decl":
                            method_vars[param[p_key]["name"]] = True
            
            if "body" in value and value["body"]:
                sub_frames.append(StackFrame(stmts=value["body"], variables=method_vars))
 
        elif key == "variable_decl":
            process_variable_decl(frame, value, current_stmt_index, is_python_like, global_stmts_to_insert)

        elif key in ("global_stmt", "nonlocal_stmt"):
            name = value.get("name")
            if name in frame.variables:
                util.error(f"global or nonlocal variable <{name}> has defined!")
            else:
                frame.variables[name] = True

        elif key.endswith("_stmt"):
            for sub_key, sub_val in value.items():
                if sub_key.endswith("body") and isinstance(sub_val, list) and sub_val:
                    # Python/ABC: block内声明最终要提升到“函数/类顶层”，因此复用同一个collector；
                    # 其他语言: 每个block单独提升到该block的开头，因此新建collector。
                    next_collector = frame.hoist_collector if is_python_like else []
                    sub_frames.append(StackFrame(
                        stmts=sub_val, 
                        variables=frame.variables, 
                        in_block=True, 
                        hoist_collector=next_collector
                    ))

        # === 阶段 4: 将子任务压栈 ===
        if sub_frames:
            # 倒序压栈，确保先处理第一个子任务
            for sub_frame in reversed(sub_frames):
                stack.append(sub_frame)

    # 插入全局变量
    for stmt in global_stmts_to_insert:
        out_data.insert(0, stmt)

    data.out_data = out_data
    return er.EventHandlerReturnKind.SUCCESS


def process_variable_decl(frame: StackFrame, value: dict, index: int, is_python_like: bool, global_stmts: list):
    """处理变量声明的核心逻辑：判断是否重复、是否需要提升、是否删除"""
    name = value.get("name")
    attrs = value.get("attrs", [])
    
    if is_python_like:
        if name in frame.variables:
            frame.to_delete_indices.append(index)
        else:
            frame.variables[name] = True
            # Python/ABC: 总是提升变量声明 (包括 block 外)
            frame.to_delete_indices.append(index)
            if frame.hoist_collector is not None:
                frame.hoist_collector.append({"variable_decl": value})
    else:
        if "var" in attrs:
            if name in frame.variables:
                frame.to_delete_indices.append(index)
            else:
                frame.variables[name] = True
                frame.to_delete_indices.append(index)
                if frame.hoist_collector is not None:
                    frame.hoist_collector.append({"variable_decl": value})
        
        elif "global" in attrs:
            if name in frame.variables:
                frame.to_delete_indices.append(index)
            else:
                frame.variables[name] = True
                frame.to_delete_indices.append(index)
                global_stmts.append({"variable_decl": value})
                
        elif "let" in attrs or "const" in attrs:
            if name in frame.variables and frame.variables.get(name) is False:
                frame.to_delete_indices.append(index)
            else:
                frame.variables[name] = False


def finalize_frame(frame: StackFrame, is_python_like: bool):
    """当前层级遍历结束后调用的清理函数"""
    stmts = frame.stmts
    
    # 1. 执行删除
    for idx in sorted(frame.to_delete_indices, reverse=True):
        if idx < len(stmts):
            stmts.pop(idx)

    # 2. 变量提升
    if is_python_like:
        # Python/ABC: 只有回到非 block 状态 (函数/类顶层) 才插入
        if not frame.in_block and frame.hoist_collector:
            for stmt in frame.hoist_collector:
                stmts.insert(0, stmt)
            frame.hoist_collector.clear()
    else:
        # Other: 每层结束都插入 (实现 Block 内置顶)
        if frame.hoist_collector:
            for stmt in frame.hoist_collector:
                stmts.insert(0, stmt)
    
    # 3. block 结束，清理 let/const 变量
    if not is_python_like and frame.in_block:
        vars_to_remove = [k for k, v in frame.variables.items() if v is False]
        for k in vars_to_remove:
            del frame.variables[k]
