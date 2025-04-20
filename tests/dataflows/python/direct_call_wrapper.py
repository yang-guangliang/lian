def outer_function():
    def inner_function(x, y):
        return operation(x, y)

    def operation(a, b):
        return a * b
    
    result = inner_function(10, 5)
    return result

result = outer_function()
print("Result:", result)  # 输出: Result: 50


def f1():
    a = 2
    b = 3
    def f2(a, b):
        def f3():
            return a + b
        return f3()

    print(f2(1, 2))
f1()

