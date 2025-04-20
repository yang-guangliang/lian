class A:
    def __init__(self) -> None:
        self.x = 1

    def b(self):
        print(self)
        self.x = 3

def k(f):
    # call
    f()

# call
a = A()

# call
a.b()

# call
a2 = A()

# call
a2.b() ## 0x781014e57fd0
a2.x = 2

# call
c = A()
c.x = a2

a21 = c.x.b

# call
a21()

# call
k(a21) ## 0x781014e57fd0
print(a2.x)  # 3


a = {
    "x": 1,
    "y": 3
}

o = {
    "a": a,
    "b": 2,
    "c": 3
}

o["a"] = a
print(a)

b = {
    "a": o["a"],
    "b": 2,
    "c": 3
}

v1 = o["a"]
v1["x"] = 2


"""
symbol a2 states{ (fields: { x: 1, b: <function A.b>}) }

field_write(a2, 'x', 2)
symbol a2 states{ (fields: { x: 2, b: <function A.b>}) }

symbol c states{ (fields: { x: 1, b: <function A.b>}) }

field_write(c, 'x', a2)
symbol c states{ (fields: { x: a2, b: <function A.b>}) }

field_read(v0, c, 'x')
symbol v0 states{ (fields: { x: 2, b: <function A.b>}) }

field_read(v1, v0, 'b')
symbol v1 states{ (<function A.b>) }

assign_stmt (v1, a21)
symbol a21 states{ (<function A.b>)}

call_stmt (a21, ())
"""