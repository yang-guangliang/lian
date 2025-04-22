def define_alias():
    benign = {
        "vulnerable_code"   : 1,
        "vulnerable_code2"  : 2
    }

    def validators():
        return  lambda x: print(x)

    def update():
        # 没有通过nonlocal的方式修改了外部变量
        origin = benign
        for key in origin:
            origin[key] = validators()

    def run():
        inp = input()
        update()
        for key in benign:
            value = benign[key]
            value(inp)

    run()

define_alias()