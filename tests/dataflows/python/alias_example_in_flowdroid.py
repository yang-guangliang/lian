def main():
    a = A()
    b = a.g
    b()
    foo(a)
    sink(b.f)

def foo(z):
    x = z.g
    w = source()
    x.f = w
