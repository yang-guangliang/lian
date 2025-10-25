
def a():
    fff = tmp()
    b(fff)

def b(z):
    z1 = tmp1()
    c(z1)

def c(z):
    print()
    z2 = tmp2()
    p = f
    p(z2)
    p = d
    p(z2)

def d(z):
    print()
    z2 = tmp5()
    x(z2)

def f(z):
    print()
    z3 = tmp6()
    x(z3)

def x(z):
    print()
    sink()


def a1():
    print1()
    b1()


def b1():
    print1()
    c1()

def c1():
    print1()

    p = d
    p()
    p = f
    p()
