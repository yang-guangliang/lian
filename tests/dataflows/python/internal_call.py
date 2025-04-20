def internal():
    i = 0
    a()
    while i < 3:
        if i % 3 == 0:
            print("8")
        elif i % 3 == 1000:
            a = 1
        a()
        i += 1