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

def fun(a): # 用于处理a.f=a，右边是a自己，带有循环依赖。对应pr apply_summary3
    a.f = a

a1 = A()
a1.h = 444
fun(a1)

result = a1
