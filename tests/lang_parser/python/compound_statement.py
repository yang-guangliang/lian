# if
def condition():
    return False

if condition():
    x = 1
elif 3 != 4:
    x = 5
elif 6 != 4:
    y = 5
else:
    y = 7


# for
fruits = ["apple", "banana", "cherry"]
for index, fruit in enumerate(fruits):
    print(f"Index {index}: {fruit}")


# while
n = 5
while n > 0:
    print(n)
    n -= 1
    n = 3
    n = 5
else:
    # 这部分只有在while循环正常结束时执行
    n = 2
    n = 4
    print("Loop ended without break")


# with
with open('file1.txt', 'r') as file1, open('file2.txt', 'w') as file2:
    for line in file1:
        file2.write(line)

with open('file1.txt', 'r') as file1:
    with open('file2.txt', 'w') as file2:
        file2.write(file1.read())


# match
## 语法没问题，语义有问题
value = 5
def add(a, b):
    return a + b
match value:
    case 0, 1, 2:
        print("在0、1或2中")
    case 3, 4, 5:
        print("在3、4或5中")
    case _:
        print("不在0到5中")
