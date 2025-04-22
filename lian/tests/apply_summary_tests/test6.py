class A:
    def __init__(self):
        pass

class F:
    def __init__(self) -> None:
        pass

class G:
    def __init__(self):
        pass

def fun(a):
    a.f.g.h = a # pr apply_summary7
a1 = A()
a1.f = F()
a1.f.g = G()
fun(a1)


result = a1
