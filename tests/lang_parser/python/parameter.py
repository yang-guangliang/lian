a = 4
def f (p = a):
    print(p)
a = 5
f()

a = 5
def f2(a, b = a + 4):
    print(a, b)
f2(3)