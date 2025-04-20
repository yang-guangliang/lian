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

def fun(a,c): # 处理a.f = 另一个参数，对应pr apply_summary2
    c.f = 3
    a.f = c

a1 = A()
c1 = C()
fun(a1,c1)

result = a1
