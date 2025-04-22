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
    a.f.g = b # 处理a.f.g = b，对应pr apply_summary1

a1 = A()
a1.f = A() 
fun(a1)


result = a1
