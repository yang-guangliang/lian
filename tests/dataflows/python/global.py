global_number = 10

def print_global_number(factor):
    print(global_number)
    global global_number
    global_number += 5
    global_number *= factor
