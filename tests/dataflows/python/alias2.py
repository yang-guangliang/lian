# def sequence(a):
#     z = a
#     y = a
#     z.g = 1
#     y.g = 2
# class F:
#     def __init__(self, a) -> None:
#         self.a = a

# gg = F

# cc = F()
# print(cc.a)

def callback1(a):
    print(a)


callbackk = callback1

receiver = access.on
x = 1
y = 2
receiver(x, y, callbackk)