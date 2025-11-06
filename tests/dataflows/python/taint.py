def f1():
    p = f2()
    return p

def f2():
    s = source()
    return s

def f3(x):
    f4(x)

def f4(x):
    sink(x)

def main():
    a = f1()
    f3(a)

main()
