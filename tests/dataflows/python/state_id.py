def func(a, b):
    m = a.x
    n = a.x

    p = b[0]
    q = b['y']

a = [{1,2,3}, {2,3,4}]

a = {
    "x": 1,
    "y": 3
}

o = {
    "a": a["x"],
    "b": 2,
    "c": 3
}

o["a"] = 2
print(a)

def func(this):
    this["a"] = -1
    this["b"] = -2

this = {
    'f': func,
    'a': {
        "x": 1,
    },
    'b': [1,2,3]
}
# call
this['f'](this)
a = {
        'm': 1
    }
b = {
        'n': 2
    }
o = {
    'x': a,
    'y': b
}