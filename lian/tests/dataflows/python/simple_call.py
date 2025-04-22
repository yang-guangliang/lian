# !/usr/bin/env python3

import os,sys as s

# def f(a = [5 + 6], b):
#     b = 3
#     a = b + 4
#     return a

def f2():
    f(1, 2)


t = 3
def f(a, b):
    b = a
    e = "123"
    a = b + 4
    return a

e = 4
g = 5
t = f(e, g)
f2 = f
t = f2(e, b = g)
t2 = t
t3 = t2
t4 = t3
t5 = t4
print(t)


