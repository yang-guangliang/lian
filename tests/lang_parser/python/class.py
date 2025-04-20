a = 1
def myfunc():
    global a
    b: int = 2
    c = 3
    a = b
    b = a + c
    def closure():
        b = c
        print(b)
    closure()
    print(b)

myfunc()

# class MyClass:
#     def fun1():
#         pass

#     def func2():
#         a = 1
#         b = 2
#         return a + b