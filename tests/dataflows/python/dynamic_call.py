# def greet(name):
#     print(f"Hello, {name}!")
# say_hello = greet

# # call
# say_hello("Bob")


# def greet(name):
#     print(f"Hello, {name}!")  # direct
# def call_with_name(func, name):

#     # call
#     func(name) # dynamic <- state

# # call
# call_with_name(greet, "Charlie")


# if condition:
#     def a():
#         print("16")
# else:
#     def a():
#         print("19")


# # call
# a()

# def a():
#     return 2
# def b():
#     return 3
# c = a
# #variable_decl a
# a = b

# # call
# a()

# # call
# c()

# 0 -> 14 , 17, 19, 20
# 16: check scope-> 14/20 ; 
# 22: symbol(a)->b's state

# 14: a -> state(14)
# 16: symbol_graph a -> state(14); 

# state: dynmaic
# no state: direct -> scope

def make_multiplier(n):
    def multiplier(x):
        return x * n
    
    # call
    return multiplier

# call
doubler = make_multiplier(2)

# call
print(doubler(5))  # 输出 10


square = lambda x: x ** 2

# call
print(square(4))  # 输出 16




def add(a, b):
    return a + b
def subtract(a, b):
    return a - b
operations = {
    "add": add,
    "subtract": subtract
}
operation = "add"

# call
print(operations[operation](3, 4))  # 输出 7


class Shape:
    def draw(self):
        print("Drawing a shape")
class Circle(Shape):
    def draw(self):
        print("Drawing a circle")
shapes = [Shape(), Circle()]
for shape in shapes:

    # call
    shape.draw()
