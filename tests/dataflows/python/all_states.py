#!/usr/bin/env python3

validators = {
    "a": lambda x, y: x + y
}

def f(p):
    for x in validators:
        p[x] = validators[x]

target = {}
f(target)
print(target["a"]("b", "c"))
