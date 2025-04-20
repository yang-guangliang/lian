def a():
    print("2")

d = 9
a2 = 3

def func1():
    pass
arr = [a]

# call
arr[0]()

a = func1
def test(a, b = 1):
    # variable_decl a

    # call
    a()
    b = 4
    c = 3
    a = 6
    if (d > 5):
        a = b + c
        c = a + b
    else:
        b = a + c
        a = b - d
    e = a

# call
test(arr[0])

def test2():
    global a2
    a2 = 4

# call
test2()

def internal():
    i = 0

    # call
    a()
    while i < 3:
        if i % 3 == 0:
            print("8")
        elif i % 3 == 1000:
            #a = 1
            pass

        # call
        a()
        i += 1

# call
internal()
# 0 -> 1
#   -> 5 -> 6 -> 7 -> 10
