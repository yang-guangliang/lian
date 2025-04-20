validators = {
    "vulnerable_code": lambda a: print(a)
}

def update(origin, add):
    for key in add:
        origin[key] = add[key]

def main():
    inp = input()
    checker = {}
    update(checker, validators)
    for key in checker:
        value = checker[key]
        value(inp)

main()

# validators = {
#     "vulnerable_code": lambda a: print(a)
# }

# def update(origin, add):
#     for key in add:
#         origin[key] = add[key]

# def run(num):
#     inp = num
#     checker = {}
#     update(checker, validators)
#     for key in checker:
#         value = checker[key]
#         value(inp)

# def main():
#     nums = [1, 2, 3, 4, 5]
#     for num in nums:
#         if num % 2 == 0:
#             run(num)
#         else:
#             run(num)

# main()
