import dataclasses
import lian.events.event_return as er
from lian import util



@dataclasses.dataclass
class Frame:
    stmts: list
    variables: dict 
    in_block: bool  
    hoist_collector: list = None 
    index: int = 0
    to_delete_indices: list = dataclasses.field(default_factory=list)

def adjust_variable_decls(data: EventData):
    out_data = data.in_data
    is_python_like = data.lang in ["python", "abc"] # 特殊处理 Python 和 ABC 语言
    global_stmts_to_insert = []

    initial_hoist_collector = []
    stack = [Frame(
        stmts=out_data, 
        variables={}, 
        in_block=False, 
        hoist_collector=initial_hoist_collector
    )]

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
        
        if key in ("class_decl", "interface_decl", "record_decl", "annotation_type_decl", "enum_decl", "struct_decl"):
            if key == "struct_decl" and "fields" in value:
                sub_frames.append(Frame(value["fields"], {}, False, []))
            else:
                for sub_key in ["methods", "fields", "nested"]:
                    if sub_key in value and value[sub_key]:
                        sub_frames.append(Frame(value[sub_key], {}, False, []))

        elif key == "method_decl":
            method_vars = {}
            if "parameters" in value:
                for param in value["parameters"]:
                    if isinstance(param, dict):
                        p_key = list(param.keys())[0]
                        if p_key == "parameter_decl":
                            method_vars[param[p_key]["name"]] = True
            
            if "body" in value and value["body"]:
                sub_frames.append(Frame(value["body"], method_vars, False, []))

 
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
                    next_collector = frame.hoist_collector if is_python_like else []
                    
                    sub_frames.append(Frame(
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

    # 最后插入全局变量
    for stmt in global_stmts_to_insert:
        out_data.insert(0, stmt)

    data.out_data = out_data
    return er.EventHandlerReturnKind.SUCCESS


def process_variable_decl(frame: Frame, value: dict, index: int, is_python_like: bool, global_stmts: list):
    """处理变量声明的核心逻辑：判断是否重复、是否需要提升、是否删除"""
    name = value.get("name")
    attrs = value.get("attrs", [])
    
    if is_python_like:
        if name in frame.variables:
            frame.to_delete_indices.append(index)
        else:
            frame.variables[name] = True
            if frame.in_block:
                frame.to_delete_indices.append(index)
                if frame.hoist_collector is not None:
                    frame.hoist_collector.append({"variable_decl": value})
    else:
        if "var" in attrs:
            if name in frame.variables:
                frame.to_delete_indices.append(index)
            else:
                frame.variables[name] = True
                if frame.in_block:
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


def finalize_frame(frame: Frame, is_python_like: bool):
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
