# 定义f1函数
def f1():
    print("f1")
    # 直接通过函数名调用f2
    exec_update = self.db_client.update_execution_status()
    self.db_client.send_execution_update(exec_update.model_dump())
    f2()


# 定义f2函数
def f2():
    print("f2")
    # 间接通过函数指针调用f3
    func_pointer = f3  # 将函数赋值给变量作为指针
    func_pointer()  # 通过指针调用函数


# 定义f3函数
def f3():
    print("f3")

    # 通过参数调用f4的辅助函数
    def call_function(func):
        func()  # 调用传入的函数参数

    call_function(f4)  # 将f4作为参数传递并调用

# 定义f4函数
def f4():
    print("f4")
    # 导入并调用f5
    from module_f5 import f5
    f5()


# 程序入口
# if __name__ == "__main__":
a= f1
a()  # 启动调用链



# c = Controller()
# a = c.b
# def get_call_chain():
#     callee_symbol: Symbol = data.in_data.callee_symbol
#         callee_name = callee_symbol.name
#         # TODO：直到a.f的a不是%vv
#         def resolve_real_callee_name(_callee_name:str):
#             while _callee_name.startswith("%vv"):
#                 tmp_symbol_name = _callee_name.split('.')[0]
#                 # def_stmt_ids = resolver.resolve_symbol_name_to_def_stmt_in_method(frame,unit_id,stmt_id,tmp_symbol_name)
#                 # def_stmt_ids["nearest_def_stmt_ids"]
#
#         if callee_name.startswith("%vv"):
#             unsolved_callee_name = set()
#             callee_states = callee_symbol.states
#             for state_index in callee_states:
#                 callee_state: State = frame.symbol_state_space[state_index]
#                 if isinstance(callee_state, State):
#                     each_callee_name = callee_state.recover_access_path_str()
#                     unsolved_callee_name.add(each_callee_name)
#             callee_name = unsolved_callee_name
#         else:
#             callee_name = {callee_name}
#         callee_name = ','.join(callee_name)



