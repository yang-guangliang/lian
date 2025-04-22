class A():
    def __init__(self) -> None:
        pass

def func(x):
    a = A()
    a.f = 1
    a1 = a
    a1.f = A()
    b = a1.f
    b.f = 3
    b1 = b
    b1.f = 4
    x.y = 999
    return a
