
def a():
    fff = tmp()
    b(fff)

def b(z):
    z1 = tmp1()
    c(z1)

def c(z):
    print()
    p = None
    if n == 1:
        p = d
    else:
        p = f
    z2 = tmp2()
    p(z2)

def d(z):
    print()
    x(z)

def f(z):
    print()
    x(z)

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
    p = None
    if n == 1:
        p = d
    else:
        p = f
    p()
