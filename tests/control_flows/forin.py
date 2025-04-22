a = [1,2,3]
b = 2
def cfg_for(a: list = [x for x in a], b = {y:y for y in a}, c = a + b):
    a = 1
    for i in range(10):
        if i % 2 == 0:
            continue  # Skip this iteration
        elif i % 3 == 0:
            break
        else:
            a = i + 1
            print(a)
        b = a
    c = b + a
    pass