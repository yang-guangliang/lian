# def cfg_try():
#     try:
#         number = int(input("Enter a number: "))
#         result = 10 / number
#     except ValueError as VE:
#         print("Please enter a valid integer.")
#     except ValueError as VE:
#         print("Please enter a valid integer.")
#     except:
#         print("Cannot divide by zero!")
#     else:
#         print("Result:", result)
#     finally:
#         print("This block is executed no matter what.")

def run(code, globals_env=None, locals_env=None):
    try: #118
        tmp_code = "" # 120
        for line in code.split("\n"): # 121 for 122
            if not line.startswith("```"): # 124 125 if 126
                tmp_code += line + "\n" # 128 129
                # tmp1= line # 128

        exec(tmp_code, globals_env, locals_env) # 129
    except Exception as e:# 131
        return str(e) # 134
    return None # 135
