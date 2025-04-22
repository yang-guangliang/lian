#assert
x = "hello"
assert x == "hello" 
assert x == "goodbye", "x should be 'hello'"


#print
print("Hello, World!")

a = 5
b = 10
print(a, b)

print("Hello", "World", sep=", ")

name = "Alice"
age = 30
print(f"{name} is {age} years old")


# del
my_list = [1, 2, 3, 4, 5]
del my_list[1], my_list[3]

x = 42
del x


# global
global global_var


# type_alias_statement
type Point = tuple[float, float]

type A = tuple[B, C, D]
type B = int
type C = str
type D = list[str]
# type LinkedList[T] = T | tuple[T, LinkedList[T]]
type E = A.B


# raise
raise TypeError("x must be an integer"), TypeError("x must be an integer")


# exec
def minus(num):
    return -num
exec("print(minus(5))", {"minus": minus})
# prog = 'print("The sum of 5 and 10 is", (5+10))'
# exec(prog)
