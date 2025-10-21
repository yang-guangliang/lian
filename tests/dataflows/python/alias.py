
# a = new A()
# b = a.g
# uuu = 8
# b.f = source()
# c = a.g.f
# foo(a)
# sink(b.f)
# # bar(b)
# def foo(z):
#     vvv = z
#     x = z.g
#     w = source()
#     x.f = w
#     sink(x.f)
#     sink(z.g.f)
#     v = z
    # c = x.f
    # if g:
    #     c1 = x.y
    # else:
    #     c1 = h.j
    # t = c1.b()

# def bar(z):
#     pass

# a = new A()
# b = a.g

# a1 = r1.f1
# b1 = a1.g1


# foo(z)
# sink(b.f)

# def foo(z):
#     x = z.g
#     w = source()
#     x.f = w


# a = deviceInfo.default.brand

# send_brand(a)


# def send_brand(brand):

#     b = brand
#     sink(b)

# class A:
#     def __init__(self) -> None:
#         self.brand = None
#     def func1(self):
#         b = self.brand 
#         pass
#     def func2(self):
#         self.brand = "abc"
#         self.func1()

# c = A()
# c.func2()
# c.func1()
# ff = c.brand


# import random
# from android import TelephonyManager, SmsManager

# class A:
#     def __init__(self):
#         self.b = "Y"

# class B:
#     def __init__(self):
#         self.attr = None

# def alias_flow_test(self):
#     mgr = self.getSystemService(Context.TELEPHONY_SERVICE)
#     device_id = mgr.getDeviceId()  # source
    

#     a = B()
#     a1 = a
#     p = B()
    
#     b = A()
#     q = A()
#     q1 = q
    
  
#     x = a1
#     y = q1
    
#     x.attr = y
#     q1.b = device_id

#     sms = SmsManager.getDefault()
#     sms.sendTextMessage("+49 1234", None, a.attr.b, None, None)  # sink, leak
# class A:
#     class B:
#         def __init__(self):
#             self.b = 7
#         def func3(self):
#             return self.b
#     def __init__(self):
#         self.attr = 5
#     def func1(cls):
#         cls.attr = 6
#         cls()
#     def func2(self):
#         self.func1()
# class A:
#     def get_value(self):
#         return self.attr
    
# a= A()
# c = a.get_value()
# ff = A.B
# c = ff.func3

# arr = [1,2,3]
# # def funcinfunc(a):
# #     bb = a[0]
# t1 =  A()
# t1.
# def funcarr(a):
#     cc = a[0]
#     a[0] = 100
#     # funcinfunc(a)
# funcarr(arr)
# dd = arr[0]
# hh = 5
# def func2(p):
#     a = b
#     return p + 1
# def func1(num):

#     num = num + 1
#     # p = hh
#     # print(66666666)
#     # func2()
#     c = func2(3)
#     nn = c
#     return num

# a = 3

# b = func1(a)

# a = A()
# b = a.g

# # a1 = r1.f1
# # b1 = a1.g1

# foo(a)
# www = b.f
# p = a
# sink(b.f)

# def foo(z):
#     x = z.g
#     v = z
#     w = nnn
#     x.f = w
#     hh = z
#     pp = z.g
#     dd = z.g.f
# def aa():
#     def infunc1():
#         pass
#     pass

# def bb():
#     c = aa
#     c()
# vvv = bb()

# a = b
# a = "b"

# class ABC:
#     def func1(self):
#         pass

# def func2():
#     pass
# a = ABC()
# b = ABC.then
# c = func2
# b(c)

# def func1():
#     def infunc():
#         pass

#     c = infunc
    
# def func2():
#     def infunc():
#         pass

#     c = infunc
    
#     pass


# def func1():
#     if hh:
#         a = b.c
#         return a
#     else:
#         t = n.d
#         return t
#
# class B:
#     def func3():
#         pass
#
# class A:
#     def __init__(self):
#         self.a = func1()
#         self.vm = B
#
#     def func2(self):
#         self.a()
#         self.vm.func3()
#
# A.func2()

class Shape(ABC):

    @abstractmethod
    def area(self):
        """形状的面积，子类必须实现此属性"""
        a = 3
        print(9999)
        pass

@a.func()
def func1():
    Shape.area()
func1()
