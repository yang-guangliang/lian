# import numpy as np
# array_3d = np.array([[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
#                      [[10, 11, 12], [13, 14, 15], [16, 17, 18]],
#                      [[19, 20, 21], [22, 23, 24], [25, 26, 27]]])
# print(array_3d[2, 1, 0])


# # import lib1

# # a = 3
# # if lib1.code(a) % 2 == 0:
# #     b = 2
# # elif a == 2:
# #     b = 3
# # print(b)

# 假设 obj1 和 obj2 是两个字典
# obj1 = {'a': 1, 'b': 2}
# obj2 = {'c': 3, 'd': 4}

# # 使用字典解包创建新的字典
# new_obj2 = {**obj1, 'z': 26, **obj2}

# print(new_obj2)

# 创建一个多维字典
multi_dimensional_dict = {
    'fruits': {
        'apple': {
            'color': 'red',
            'weight': 150
        },
        'banana': {
            'color': 'yellow',
            'weight': 120
        },
        'cherry': {
            'color': 'red',
            'weight': 5
        }
    },
    'vegetables': {
        'carrot': {
            'color': 'orange',
            'weight': 70
        },
        'potato': {
            'color': 'brown',
            'weight': 100
        }
    }
}

# # 创建一个类
# class Fruit:
#     def __init__(self, color, weight):
#         self.color = color
#         self.weight = weight

# class Basket:
#     def __init__(self):
#         self.fruits = []

#     def add_fruit(self, fruit):
#         self.fruits.append(fruit)

# # 创建一个篮子对象并添加水果
# basket = Basket()
# apple = Fruit('red', 150)
# banana = Fruit('yellow', 120)
# cherry = Fruit('red', 5)
# basket.add_fruit(apple)
# basket.add_fruit(banana)
# basket.add_fruit(cherry)

# # 动态索引
# key = 'fruits'
# sub_key = 'apple'
# property = 'color'

# # 复杂索引
# key_expression = 'vegetables'
# sub_sub_key = 'carrot'
# property_expression = 'color'

# # 数组片段访问
# array = [1, 2, 3, 4, 5]
# start = 1
# end = 3

# # 变量变量
# dynamic_key_var = 'fruits'
# dynamic_sub_key_var = 'apple'
# dynamic_property_var = 'color'

# 输出结果
print("Multi-Dimensional Dictionary Elements:")
print(f"Apple Color: {multi_dimensional_dict['fruits']['apple']['color']}")  # red
print(f"Banana Weight: {multi_dimensional_dict['fruits']['banana']['weight']}")  # 120
print(f"Cherry Color: {multi_dimensional_dict['fruits']['cherry']['color']}")  # red

# print("\nNested Object Properties:")
# print(f"First Fruit Color: {basket.fruits[0].color}")  # red
# print(f"Second Fruit Color: {basket.fruits[1].color}")  # yellow
# print(f"Third Fruit Color: {basket.fruits[2].color}")  # red

# print("\nDynamic Multi-Dimensional Dictionary Elements:")
# print(f"Apple Color: {multi_dimensional_dict[key][sub_key][property]}")  # red

# print("\nComplex Multi-Dimensional Dictionary Elements:")
# print(f"Carrot Color: {multi_dimensional_dict[key_expression][sub_sub_key][property_expression]}")  # orange

# print("\nArray Slice:")
# print(f"Fragment: {array[start:end]}")  # [2, 3]

# print("\nVariable Variable:")
# print(f"Apple Color: {getattr(globals()[dynamic_key_var], dynamic_sub_key_var)[dynamic_property_var]}")  # red