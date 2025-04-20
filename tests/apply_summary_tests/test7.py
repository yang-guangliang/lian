class A:
    def __init__(self):
        pass
class B:
    def __init__(self):
        pass
class C:
    def __init__(self):
        pass



def fun(a,b):
    a.f.g = b.c # pr apply_summary7

a1 = A()
a1.f = A() 
b1 = B()
b1.c = C()
fun(a1,b1)


result = a1
