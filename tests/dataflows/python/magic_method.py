class Item:
    def __init__(self, e=None):
        self.e = e

    def c(self):
        print(self.e)

b = Item('b')
a = Item('a')
d = a.c
b.c = d
b.c() # self is a, not b