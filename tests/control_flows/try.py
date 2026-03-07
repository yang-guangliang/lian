def cfg_try():
    try:
        number = int(input("Enter a number: "))
        result = 10 / number
    except ValueError as VE:
        print("Please enter a valid integer.")
    except ValueError as VE:
        print("Please enter a valid integer.")
    except:
        print("Cannot divide by zero!")
    else:
        print("Result:", result)
    finally:
        print("This block is executed no matter what.")

def run(code, globals_env=None, locals_env=None):
    try:
        tmp_code = ""
        for line in code.split("\n"):
            if not line.startswith("```"):
                tmp_code += line + "\n"

        exec(tmp_code, globals_env, locals_env)
    except Exception as e:
        return str(e)
    return None
