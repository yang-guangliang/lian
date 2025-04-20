# # a = [1, 2, 3]
# # b = [4, 5, 6]
# # c = 3
# # def cfg_for(a: list = [x for x in a], b = {y:y for y in a}, c = a + b):
# #     a = 1
# #     for i in range(10):
# #         if i % 2 == 0:
# #             continue  # Skip this iteration
# #         elif i % 3 == 0:
# #             break
# #         else:
# #             a = i + 1
# #             print(a)
# #         b = a
# #     c = b + a
# #     return a

# # cfg_for(a, b)
# # cfg_for(c, b)

# def count_cycles(t):
#     n = len(t)
#     if n < 2:
#         return 0
    
#     last_element = t[-1]
#     cycle_count = 0
    
#     for i in range(n-2, -1, -1):
#         if t[i] == last_element:
#             cycle_length = n - i - 1
#             if t[i-cycle_length+1:i+1] == t[i+1:i+1+cycle_length]:
#                 current_cycle = t[i-cycle_length+1:i+1]
#                 cycle_count += 1
#                 for j in range(i-2*cycle_length+1, -1, -cycle_length):
#                     if t[j:j+cycle_length] == current_cycle:
#                         cycle_count += 1
#                 break

    
#     return cycle_count

# # 测试用例
# print(count_cycles((1, 2, 3, 1, 2, 3)))  # 1
# print(count_cycles((1, 2, 3, 4, 5, 6)))  # 0
# print(count_cycles((1, 2, 3, 4, 5, 3, 4, 5)))  # 1
# print(count_cycles((1, 2, 3, 4, 5, 3, 4, 5, 3, 4, 5)))  # 2
# print(count_cycles((1, 2, 1, 2, 1, 2)))  # 2
# a = (111, 109, 11, 86, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19, 58, 19)
# # 测试用例
# print(count_cycles(a))  # 2
# # print(count_required_cycles((1, 2, 3, 1, 2, 3)))  # 输出: 1
# # print(count_required_cycles((1, 2, 3, 4, 5, 6)))  # 输出: 0
# # print(count_required_cycles((1, 2, 3, 1, 2, 4)))  # 输出: 0
# # print(count_required_cycles((1, 2, 3, 4, 5, 3, 4, 5)))  # 输出: 1
# # print(count_required_cycles((1, 2, 3, 4, 5, 3, 4, 5, 3, 4, 5)))  # 输出: 2


# # # 测试用例
# # print(count_required_cycles((1, 2, 1, 2, 3, 4, 5, 1, 2, 3)))

a = 1
b = 2
c = 3

# l = [[1, 2], [3, 4], [5, 6]]
# for k, v in l: 
#     testk = k
#     testv = v

l = [1, 2, 3, 4, 5, 6]
for elem in l: 
    testvar = elem

# o = {
#     "k1": 1, 
#     "k2": 2, 
#     "k3": 3
# }
# print("o: ", o)
# print("o.items: ", o.items())
# for i in o: 
#     print("elem is: ", i)