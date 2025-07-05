def sequence(a):
    z = a
    y = a
    z.g = 1
    y.g = 2
class F:
    def __init__(self, a) -> None:
        self.a = a

gg = F

cc = F()
print(cc.a)