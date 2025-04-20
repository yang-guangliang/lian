#!/usr/bin/env python3

import os,sys

# Same module 'math_functions'

from lib1.math import math_functions
from lib1 import math
import lib1.math.math_functions
from lib1.math.math_functions import *

result_sqrt = sqrt(16)
result_cube = cube(3)

def f():
    a = 3
    if (True):
        a = 4 # D
        if (True):
            a = 5 # D

    def f1():
        a = 4

    class C():
        a = 10
        def f2(self):
            a = 12

    a = 18 # D

    c = C()
    print(c.a)
    c.f2()
    print(c.a)
    c.a = 11
    print(c.a)
    c2 = C()

    f1()
    print(a)
    print(c2.a)
    

# f()
