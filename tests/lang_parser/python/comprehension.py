[x**2 for x in range(10)]

# a = []
# for x in range(10):
#     a.append(x**2)

[(x, y) for x in [1,2,3] for y in [3,1,4] if x != y]

# b = []
# for x in [1,2,3]:
#     for y in [3,1,4]:
#         if x != y:
#             b.append((x,y))


{x for x in range(10) if x % 2 == 0}

{x: x**2 for x in range(10)}  

# a = {}
# for x in range(10):
#     a.update({x: x**2})