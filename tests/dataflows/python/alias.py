
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

def func1(num):
    num = num + 1
    print(66666666)
    return num

a = 3

b = func1(a)

c = b