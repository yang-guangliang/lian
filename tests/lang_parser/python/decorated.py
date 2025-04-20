def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

# 等价于 say_hello = my_decorator(say_hello)

say_hello()


def repeat(num_times):
    def decorator_repeat(func):
        def wrapper(*args, **kwargs):
            for _ in range(num_times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator_repeat

@repeat(num_times=3)
def greet(name):
    print(f"Hello {name}")

# 等价于 greet = repeat(num_times=3)(greet)

greet("World")


class MyClass:
    @staticmethod
    def my_static_method():
        print("This is a static method.")

    @classmethod
    def my_class_method(cls):
        print("This is a class method.")

    @property
    def my_property(self):
        return "This is a property."

class MyClass:
    @repeat(num_times=3)
    def greet(self, name):
        print(f"Hello {name}")
# # 等价于 MyClass.greet = repeat(num_times=3)(MyClass.greet)

# 示例
my_obj = MyClass()
my_obj.greet("World")

def add_class_name(cls):
    cls.class_name = cls.__name__
    return cls

@add_class_name
class MyClass:
    def greet(self, name):
        print(f"Hello {name}")
#  等价于 MyClass = add_class_name(MyClass)

# 示例
my_obj = MyClass()
my_obj.greet("World")
print(my_obj.class_name)  # 输出 "MyClass"

from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function"""
        print("Something is happening before the function is called.")
        result = func(*args, **kwargs)
        print("Something is happening after the function is called.")
        return result
    return wrapper

@my_decorator
def say_hello():
    """Say hello function"""
    print("Hello!")
