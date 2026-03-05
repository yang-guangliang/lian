def exceptions_flow(a, b):
    val = 0
    result = [1, 2, 3]

    # Try/except/finally exception handling state flow
    try:
        val = result[0] / b
    except ZeroDivisionError as e:
        val = -1
    except Exception as e:
        val = -2
    finally:
        val = val * 2
        result.clear()
        
    return val, result
