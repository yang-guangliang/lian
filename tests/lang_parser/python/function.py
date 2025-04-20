from typing import TypeVar, List

T = TypeVar('T')  # 创建一个类型变量T

async def first_element(items: List[T], item = [1, 2], *args: T) -> tuple[T,T]:
    return (items[0], item[1], args[0])

def func(arg : [T],a: int = 3,  b = "123", ):
    return a + b

numbers = [1, 2, 3]
strings = ["apple", "banana", "cherry"]
first_num = first_element(numbers)
first_str = first_element(strings)


# 闭包
def outer_function(x):
    def inner_function(y):
        return x + y
    return inner_function

add_five = outer_function(5)
print(add_five(10))  # 输出 15


# 带装饰器的函数
from functools import wraps

def debug(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        args_repr = [repr(a) for a in args]                      
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  
        signature = ", ".join(args_repr + kwargs_repr)           
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")           
        return value
    return wrapper

@debug
def add(x, y):
    return x + y

add(3, 4)

