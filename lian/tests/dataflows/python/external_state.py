# condition 1 <global>
x = 1
y = 2
z = 3
g = 4

# condition 2 <nested_function>
def external():
    a = 2
    def internal(m):
        b = a + 1 + x + m
        print(b)
        return b
    # call
    c = internal(5)
    return c
# call
external()

# condition 3 <closure>
def a():
    m = "a"
    def b():
        t = m
    # call
    return b

g = 1
# condition 4 <call chain>
def f1():
    g = 2
    def f3():
        nonlocal g
        g = 8
        # call
        f4()

    def f4():
        print(g)

    def f2():
        global g
        g = 4
        # call
        f3()
    # call
    f2()

class A:
    def m(self):
        print("call m")

def f():
    def g():
        print("call g")
    # call
    b = A()
    c = {
        "x": b,
    }
    a = [c]

    a.append(g)
    def h():
        # call
        a[0]['x'].m()
        # call
        a[1]()
    # call
    h()
# call
f()

def ep1(c): # c_states: {1, 2, 3}
    def ep():
        def h():
            nonlocal c
            c['f'] = g
        # call
        h()
    # call
    ep()

    def ep2():
        # call
        c['f']()
    # call
    ep2(a = c)


def ep1(c): # c_states: {1, 2, 3}
    def ep():
        def h():
            # call
            c['f']() # key_dynamic_content
            # array_read v c f  # 1c(state_id:1, source_symbol_id: 68)
                                # 2v(state_id:2, source_symbol_id: 68, access_path: f) 3i_c(state_id:1, source_symbol_id: 68 fields f: 2)
            # call v            # 2v(state_id:2, source_symbol_id: 68, access_path: f)


            # c['f']['g']() # key_dynamic_content
            # array_read v c f  # 1c(state_id:1, source_symbol_id: 68)
                                # 2v(state_id:2, source_symbol_id: 68, access_path: f) 3i_c(state_id:1, source_symbol_id: 68 fields f: 2)
            # array_read u v g  # 2v(state_id:2, source_symbol_id: 68, access_path: f)
                                # 4u(state_id:2, source_symbol_id: 68, access_path: [f, g]) 5i_
            # call v            # 2v(state_id:2, source_symbol_id: 68, access_path: f)
        # call
        h()
    # call
    ep()

    def ep2(**d):
        def h():
            a = [0]
            # call
            d['a']['f'](a)
            # call
            a[0]()
        # call
        h()
    # call
    ep2(a = c)

e = 3
def f():
    b = e

def g(p):
    p[0] = f

c = {}
c['f'] = g
# call
ep1(c)

"""
phase 2:
    external symbol has no state
->  symbol is external
->  new anything state  ->  assign  ->  trans state to target symbol, don't need copy
->  field/array operation
->  anything has no field/array
->  new anything state

    parameter symbol
->  has init anything state  source_stmt_id = parameter's source_stmt_id ->  assign  ->  trans state to target symbol, don't need copy
->  field/array operation (p.a)
->  anything has no field/array
->  new anything state
->  field/array operation (p.a.b)
->  anything has no field/array
->  new anything state

phase 3:
    meet one external key state
->
"""