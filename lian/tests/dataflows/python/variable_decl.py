def cfg_for(a: int = 2, b: int = 3):
    if 1:
        b = 1
    else:
        b = 2
    c = a
    d = b + c
    
    """
    stmt_id  defined_symbol(state_id_1,state_id_2) all_states: state1_value,state2_value...(field/array)
    """