def main():
    a = A()
    a.k = source
    b = a.g
    foo(a)
    sink(b.f)

def foo(z):
    x = z.g
    f = z.k
    w = f()
    x.f = w