def a():
    a1()
    a2()
    a3()
    d = 0

def a1():
    caller()
    n = 9
def a2():
    caller()
    n = 9
def a3():
    caller()
    n = 9

def caller():
    h = 3
    callee(h)

def callee(j):
    q = j
    v = 6

a()
