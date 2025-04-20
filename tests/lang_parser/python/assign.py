# ######################### LEFT #########################

# #identifier
# a = 5

# # keyword_identifier
# type = 3

# # subscript
# my_list = [1, 2, 3]
# my_list[1] = 42

# my_dict = {'name': 'Alice', 'age': 30}
# my_dict['age'] = 31

# # slice
# start = 2
# step = 2
# my_list[start: 7: step, 7, 2: 10: step] = [5, start, "str"]
# my_list[start: : step, 2: 10: step, 2] = [5, step, "str"]
# my_list[1][2][3] = 42
# x = my_list[1][2][3]

# slice_result = my_list[1: 4: a]

# # tuple_pattern
# point = (3, 4)
# (x, y) = point
# (x, y) += (1, 2)

# list_pattern
# [first, second]= [1, 2, (1,2)]

data = [
    [1, 'Tom'],
    [2, 'Fred'],
]

first, second = data[0]


# # attribute
# class Person:
#     def __init__(self, name, age):
#         self.name = name
#         self.age = age

# person_obj = Person('Bob', 25)
# person_obj.age = 26

# # list_splat_pattern
# rest, c, d = [1, 2, 3]

# first, *rest, c, d = [1, 2, 3, 4, 5]


# ######################## RIGHT #########################
# x = 10
# y = 20 if x > 5 else 0

# squares = [x**2 for x in range(1, 6)]

# squares_dict = {x: x**2 for x in range(1, 6)}
