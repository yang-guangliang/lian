def operations(a, b, z):
    # Binary and complex expressions with precedence
    c = a + (b * 5) - (~a)
    
    # Boolean logic and short-circuit evaluation
    is_valid = (a > 0) and (not z) or (b == 1)
    
    # Ternary operator
    result = c if is_valid else b
    
    return result
