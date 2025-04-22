# def f1(a, b = 0): 
#     return b

# c = f1(0)
# d = f1(0, 1)

# print(c, d) # 0 1

benign = {
    "vulnerable_code": 1
}
def validators():
    return  lambda x: print(x)
    # return  lambda x: x + 1

# case1
# def main(checker=validators):
#     inp = input()
#     for key in checker:
#         value = checker[key]
#         value(inp)

# main()

# case2
def update(a, b, origin = benign):
    c = a + b
    # print(c)
    for key in origin:
        origin[key] = validators()

def main():
    update(1, 2)
    inp = input()
    inp = 1
    for key in benign:
        value = benign[key]
        value(inp)

main()