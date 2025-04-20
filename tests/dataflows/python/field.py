class T:
    def __init__(self):
        self.field1 = 1
        self.field2 = 1
        self.field3 = 2

def test_field():
    t = T()
    t.field1 = 1
    t.field2 = 2
    x = t.field3
    print(x)

def test_field2():
    t = T()
    t.field1 = 1
    t.field2 = 2
    x = t.field3
    print(x)

a = [1,2]
a[0] = test_field
g = 2
f = 1
d = {1: "123", 2: "255"}

d[f] = a[0]
d[1] = test_field2
d[f]()
a = d[g] 
print(d[f])
print(d[g])