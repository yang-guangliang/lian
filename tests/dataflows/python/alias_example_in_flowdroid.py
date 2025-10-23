def main():
    a = A()
    b = a.g
    foo(a)
    sink(b.f)

def foo(z):
    x = z.g
    w = source()
    x.f = w

#main()