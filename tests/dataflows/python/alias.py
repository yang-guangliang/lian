
# a = new A()
# b = a.g
# uuu = 8
# b.f = source()
# c = a.g.f
# foo(a)
# sink(b.f)
# # bar(b)
# def foo(z):
#     vvv = z
#     x = z.g
#     w = source()
#     x.f = w
#     sink(x.f)
#     sink(z.g.f)
#     v = z
    # c = x.f
    # if g:
    #     c1 = x.y
    # else:
    #     c1 = h.j
    # t = c1.b()

# def bar(z):
#     pass

# a = new A()
# b = a.g

# a1 = r1.f1
# b1 = a1.g1


# foo(z)
# sink(b.f)

# def foo(z):
#     x = z.g
#     w = source()
#     x.f = w


a = deviceInfo.default.brand

send_brand(a)


def send_brand(brand):

    b = brand
    sink(b)