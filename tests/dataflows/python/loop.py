# condition = True
# if condition:
#     a = {
#         'x': 1,
#         'y': 2,
#         'z': 3
#     }
# else:
#     a = [1,2,3]

# b = 1
# c = a[b]

# b = 'x'
# c = a[b]


a = {
    'x': 1,
    'y': 2,
    'z': 3
}

b = {}
for key in a:
    b[key] = a[key]
