def flow():
    a = 111
    b = 222
    c = a + b
    a = 333
    if 1:
        a = 444
    if 1:
        a += "hello"
    d = a
    e = d + d  # TODO: 照理来说应该就是每个d的state*2, 而不应该是两两排列组合