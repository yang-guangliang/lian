def flow(a, b):
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

def main():
    c = 0
    flow(c, b = 1)
    print(a)

main()
c = 555
# flow(c, b = 1)
hhh = 3