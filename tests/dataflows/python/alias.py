
a = new A()
b = a.g
foo(a)
sink(b.f)
# bar(b)
def foo(z):
    x = z.g
    w = source()
    x.f = w
    # c = x.f
    # if g:
    #     c1 = x.y
    # else:
    #     c1 = h.j
    # t = c1.b()

# def bar(z):
#     pass