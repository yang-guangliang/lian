a()
def a():
    t = b()
    m = t
    n = m.l
    sink(n)

def b():
    k = source()
    j = k.p
    return j
