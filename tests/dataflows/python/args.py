# # #!/usr/bin/env python3

# def my_function(a, /, b, *, c):
#     return a + b + c
# my_function(1, 2, c=3)
# my_function(1, b=2, c=3)

# def my_function2(*args):
#     sum = 0
#     for arg in args:
#         sum += arg
#     return sum
# my_function2(1, 2, 3)

# def my_function3(**kwargs):
#     sum = 0
#     for key, value in kwargs.items():
#         if key in ["b", "c"]:
#             sum += value
#     return sum

# my_function3(a=1, b=2, c=3)

def my_function4(a, *args, **kwargs):
    print(a)
    print(args)
    print(kwargs)
    sum = 0
    for arg in args:
        sum += arg
    for key, value in kwargs.items():
        if key in ["b", "c"]:
            sum += value
    return sum

l = [4, 5, 6]
d = {"d": 7, "e": 8}
l2 = [9, 8, *l, 2]
d2 = {"g": 7, "h": 9, **d, "c": 6}
my_function4(*l, 1, 2, 3, *l, **d2)

# def my_function5(a, b, c):
#     # do something with a, b, and c
#     return a + b + c
 
# args = [1, 2, 3]
# kwargs = {'a': 1, 'b': 2, 'c': 3}
# my_function5(*args)
# my_function5(**kwargs)

# default = 3
# def my_function5(a, b = default, c = 2, *args, d, e, **kwargs):
#     print(f"a: {a}, b: {b}, c: {c}, d: {d}, e: {e}, args: {args}, kwargs: {kwargs}")
# my_function5(1,b = 2, d = 2,e = 3)
# my_function5(1,2,3,4,5,d = 2,e = 3)
# my_function5(1,2,d = 2,e = 3)
# my_function5(1,*[2,3],d = 2,e = 3)

# default_value = 4

# def my_function6(a, b, c = default_value):
#     a = 5
#     b = 6

# x = 1
# y = 2
# z = 3
# my_function6(x, y, z)
# l = [1, 2, 3]
# my_function6(*l)