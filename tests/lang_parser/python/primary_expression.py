# # await
# import asyncio
# # await asyncio.sleep(2)


# string
def add(a, b):
    return a + b
a = 5
b = 10
result = f"Five plus ten is {add(a, b)}, not {a * b, a - b}"
print(result)

# name = 'World'
# program = 'Python'
# str = f'Hello {name}! This is {program}'
# print("%s %s" %('Hello','World',))

# name = 'world'
# program ='python'
# print('Hello %s! This is %s.'%(name,program))


# # concatenated_string


# a = 3.1415


# # unary_operator
# x = 3
# b = -(x-5)


# # not_operator
# a = True
# b = not a


# # boolean_operator
# a = 1
# b = (not a) and (- a)


# # list_comprehension
# y = [x * 2 for row in [1,2,3] for x in row if x % 2 == 0]


# call
# 参数包含for in
def sum_of_squares(numbers):
    return numbers

result = sum_of_squares([x * x for x in range(10)])

# 参数包含多层for in
def filter_and_multiply(matrix):
    return [x * 2 for row in matrix for x in row if x % 2 == 0]

result = filter_and_multiply([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# 参数包含if
def count_evens(numbers):
    return sum(1 for n in numbers if n % 2 == 0)

even_count = count_evens([1, 2, 3, 4, 5, 6])
print(even_count)


# conditional_expression
a = 7
x = a if a > 0 else - a


# # lambda
# f = lambda x: x + 10

# points = [(1, 2), (3, 1), (5, -1)]
# points_sorted = sorted(points, key=lambda point: point[1])

# numbers = [1, 2, 3, 4, 5]
# squared = [lambda x: x ** 2 for x in numbers]


# named_expression
f = lambda x : x+2
data = [1,2,3,4]
f_data = [y for x in data if (y := f(x)) is not 4]


# # union_type
# y: list[int, str] = [1, 'foo']

# set1 = {1, 2, 3}
# set2 = {3, 4, 5}
# union_set = set1 | set2
# print(union_set)

# a = b = 3
# c = d = 4
# def add(a, b):
#     return a + b
# a, b = add(a, b), add(c, d)
# print(a, b)

# from typing import TypeVar, List

# T = TypeVar('T')  # 创建一个类型变量T
# l1 = 1
# l2 = 2
# async def first_element(items: List[T], item = l1 + l2, *args: T) -> tuple[T,T]:
#     return (items[0], item[1])


# def get_score():
#     return 99

# # 一个包含学生信息的字典
# student_info = {
#     'name': 'Alice',
#     'score': get_score(),
#     'age': 20,
#     'grade': 'A',
#     'courses': ['Math', 'Physics', 'Chemistry']
# }

# # 打印字典内容
# print(student_info)
