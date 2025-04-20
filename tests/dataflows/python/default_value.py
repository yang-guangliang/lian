def f1(a, b = 0): 
    return b


# call
c = f1(0)

# call
d = f1(0, 1)

print(c, d) # 0 1

benign = {
    "vulnerable_code": 1
}
def validators():

    
    return  lambda x: print(x)

# # case1
# def main(checker=validators):
#     inp = input()
#     for key in checker:
#         value = checker[key]

#         # call
#         value(inp)

# # call
# main()

# case2
def update(a, b, origin = benign):
    c = a + b
    print(c)
    for key in origin:

        # call
        origin[key] = validators()

def main():

    # call
    update(1, 2)
    inp = input()
    for key in benign:
        value = benign[key]
        # call
        value(inp)
# call 
main()