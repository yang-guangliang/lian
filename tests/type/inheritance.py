# 定义基类 Animal
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def info(self):
        return f"我是一只{self.name}"

class leg():
    def __init__(self, name):
        self.name = name

class tail():
    def __init__(self, name):
        self.name = name

# 定义 Dog 类，继承自 Animal
class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

    def speak(self):
        return f"{self.name}：汪汪！"

    def info(self):
        return f"我是一只{self.breed}狗，名字叫{self.name}"

# 定义 Cat 类，继承自 Animal
class Cat(Animal, leg, tail):
    def __init__(self, name, color):
        super().__init__(name)
        self.color = color

    def speak(self):
        return f"{self.name}：喵喵！"

    def info(self):
        return f"我是一只{self.color}的猫，名字叫{self.name}"

# 创建对象并调用方法
dog = Dog("小黑", "拉布拉多")
cat = Cat("小白", "白色")

print(dog.speak())  # 输出：小黑：汪汪！
print(dog.info())   # 输出：我是一只拉布拉多狗，名字叫小黑

print(cat.speak())  # 输出：小白：喵喵！
print(cat.info())   # 输出：我是一只白色的猫，名字叫小白

