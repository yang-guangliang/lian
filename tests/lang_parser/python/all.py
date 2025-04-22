# 类定义
class Person:
    # 构造函数和属性
    def __init__(self, name, age):
        self.name = name
        self.age = age

    # 实例方法
    def greet(self):
        if self.age < 18:
            return f"Hi, I'm {self.name}! I'm underage."
        else:
            return f"Hello, I'm {self.name}."

    def celebrate_birthday(self):
        self.age += 1

# 继承
class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade

    # 方法覆盖
    def greet(self):
        return f"Hi, I'm {self.name}, a {self.grade} grade student."

# 创建实例

# call
john = Person("John", 25)

# call
jane = Student("Jane", 16, 10)

# 列表和循环
people = [john, jane]
for person in people:

    # call
    print(person.greet())

# 异常处理
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")

# 字典和解构
person_info = {"name": "Alice", "age": 30}

# call
alice = Person(**person_info)
print(f"{alice.name} is {alice.age} years old.")

# 生成器表达式
even_numbers = (x for x in range(10) if x % 2 == 0)
print(list(even_numbers))

# 上下文管理器和with语句
with open("example.txt", "w") as file:
    file.write("Hello, this is an example.")

# 装饰器
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Something is happening before the function is called.")

        # call
        result = func(*args, **kwargs)
        print("Something is happening after the function is called.")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

# call
say_hello()

# Lambda表达式
add = lambda x, y: x + y

# call
print(add(3, 5))

# Set集合
set_a = {1, 2, 3}
set_b = {3, 4, 5}

# 集合运算

print(set_a.update(set_b))
print(set_a.intersection(set_b))

# 列表解析
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(squared)
