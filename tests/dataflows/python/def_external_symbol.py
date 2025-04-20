a = 1
b = 2
def external():
    global a, b
    c = a + b
    a = 5
    b = 2
external()# def a, b
print(a)
print(b)