class A:
    def __init__(self):
        pass
class B:
    def __init__(self):
        pass
class C:
    def __init__(self):
        pass

b = B()

def fun(a):
    a.f = a.g # apply_summary4 a.f=a.g
a1 = A()
a1.g = C()
fun(a1)


result = a1
