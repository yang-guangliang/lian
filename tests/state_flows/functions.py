def helper_func(x, y=0, *args, **kwargs):
    res = x + y
    if args:  # Avoid loops as requested
        res += args[0]
    return res, kwargs.get("name", "unknown")

def functions_flow(data):
    # Standard call with default args overridden and keyword arg
    a, name_a = helper_func(10, 20, name="custom")
    
    # Call utilizing *args and **kwargs explicitly
    b, name_b = helper_func(1, 2, 3, 4, 5, name="test", extra_flag=True)
    
    # Nested function calls
    c, name_c = helper_func(helper_func(1)[0], y=a)
    
    return a, b, c
