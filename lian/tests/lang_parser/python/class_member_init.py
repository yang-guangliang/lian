class MyClass:
    class_var = []  # 类的成员（类变量）

    def __init__(self, instance_var):
        self.instance_var = instance_var  # 实例的成员（实例变量）

    def instance_method(self, k = [1, 2, 3]):
        class Test:
            def f(self, k):
                print(k, self.b)

        print(f'Instance method called for instance_var = {self.instance_var}')
        print(self.class_var)
        a = 3

my = MyClass(1)
my.class_var.append(8)
my.instance_method()

my2 = MyClass(2)
my2.class_var = 3
my2.instance_method()

my8 = MyClass(8)
my8.instance_method()
