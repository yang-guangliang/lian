class T:
    field1 = 1
    field2 = 1
    field3 = 2
    def __init__(self):
        pass

def test_field():
    t = T()
    t.field1 = 1
    t.field2 = 2
    x = t.field3
    print(x)