# # # 创建一个列表
my_list = [0, 1, 2, 3, 4, 5]

# # testvar = my_list[1]

# start = 2
# end = 3
# step = 2

# ### slice_read ###
# # 简单切片：从索引1到索引4（不包括4）
# simple_slice = my_list[1:4:2]
# simple_slice = my_list[1:end:step]
# simple_slice = my_list[start:4:2]
# simple_slice = my_list[start:end:step]

# my_list[start] = 99

def slice_test_func(array, start, end, step): 
    array = [0, 1, 2, 3, 4, 5]
    testarr = [0, 1, 2, 3, 4, 5]
    # start = 1
    # end = 4
    # step = 2
    test = array[start:end:step]
    testarr[start:end:step] = array
    return test

# # 省略开始索引：从开始到索引3
# start_omitted = my_list[:3]

# # 省略结束索引：从索引3到最后
# end_omitted = my_list[3:]

# # 使用步长：每隔一个元素取一个
# step_slice = my_list[::2]

# # 使用混合步长
# step_slice = my_list[1:4:2]

# # # 负数索引：从倒数第三个元素到倒数第一个元素
# negative_indices = my_list[::-1]
# print(negative_indices)

# # 反转列表
# reversed_list = my_list[::-1]




### slice_write ###
# 简单切片赋值：替换索引1到索引4（不包括4）的元素
my_list[1:2] = [11, 12, 13]
print(my_list)
my_list[1:2] = (11, 12, 13)
print(my_list)
my_list[1:2] = {11, 12, 13}
print(my_list)
my_list[1::1] = "abc"
print(my_list)
my_list[1:2] = []
print(my_list)

# testlist = [11, 12, 13]
# my_list[1:2] = testlist
# print(my_list)

# # 非法
# my_list[1:2] = 11
# print(my_list)

# # 插入元素：在索引1位置插入两个新元素
# my_list[1:1] = [8, 9]

# # 删除元素：删除索引3到索引6（不包括6）的元素
# my_list[3:6] = []

# # 替换所有元素：用一个新的列表替换整个列表
# my_list[:] = [1, 2, 3, 4, 5]

# # 使用步长进行赋值：每隔一个元素替换一次
# my_list[::2] = [10, 20, 30]

# # 使用负数索引进行赋值：替换倒数第三个到倒数第一个的元素
# my_list[-3:-1] = [40, 50]

# # 反转赋值：将列表反转
# my_list[::-1] = [1, 2, 3, 4, 5]