g = 3
'''
1、gir阶段把所有临时变量改名字

g = 10
int f()
	g = 11
	int g;
	g = 12
print g

2、
'''
def f1():
    f2()

def f2():
    global g
    g = 4
    f3()

def f3():
    g = 8
    f4()

def f4():
    print(g)

# def f3():
#     g = 8
#     def f4():
#         print(g)
#     f4()

f1()