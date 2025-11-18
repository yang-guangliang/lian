def main(e=1,f=2):
    a = A()
    b = a.g
    foo(a)
    sink(b.f)

def foo(z):
    x = z.g
    w = source()
    x.f = w

main()
