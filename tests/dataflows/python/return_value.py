class A:
    def __init__(self, a: list):
        self.ddddd = "ssssssssssssss"
        a[0] = self.ddddd
        # self.ddddd = a

def fun():
    m = ['first']
    obj = A(m)
    obj.f = m
    return obj

o = fun()
a = o.f
b = o.ddddd