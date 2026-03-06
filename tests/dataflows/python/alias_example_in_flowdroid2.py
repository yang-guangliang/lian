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
    a.k = source()
    b = a.g
    foo(a)
    sink(b.f)

def foo(z):
    x = z.g
    w = z.k
    x.f = w
main()
