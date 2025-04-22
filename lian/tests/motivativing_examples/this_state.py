class A:
    def __init__(self) -> None:
        self.x = 1

    def b(self):
        self.x = 3

def k(f):
    f()

a = A()
a.b() # 1

a2 = A()
a2.b() #2 # 0x781014e57fd0
a2.x = 2
c = A()
c.x = a2

a21 = c.x.b
x1 = a2.x
a21() #3
x2 = a2.x
# k(a21) #4 # 0x781014e57fd0
# print(a2.x)  # 3


# a = {
#     "x": 1,
#     "y": 3
# }

# o = {
#     "a": a,
#     "b": 2,
#     "c": 3
# }

# o["a"] = a
# o["a"].append(1)
# print(a)

# b = {
#     "a": o["a"],
#     "b": 2,
#     "c": 3
# }

# v1 = o["a"]
# v1["x"] = 2


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