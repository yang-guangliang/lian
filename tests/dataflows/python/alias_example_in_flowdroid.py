
# def a():
#     t = source()
#
#     b(t)
# def b(p):
#     g = p
#     sink(g)
# def c(p, p1):
#     sink(p)
#     send(p1)
# a()

def main():
    a = A()
    b = a.g
    foo(a)
    sink(b.f)

def foo(z):
    x = z.g
    w = source()
    x.f = w

main()

