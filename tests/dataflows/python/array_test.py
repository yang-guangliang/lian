# array_append & array_extend
def my_function1(p1, p2, p3):
   p3['x'] = 2

a = {'x': 1, 'y': 3}
l = [1, 2, a]
my_function1(*l)
b = a['x']

# array_extend
r = {'x': 1, 'y': 3}
a = [1, 2, 3]
b = [4, 5, r]
c = [*a, *b]
c[5]['y'] = 4

# array_read
a = [1, 2, 3]
b = [4, 5, a]
c = b[2]
a[0] = 0
print(c)

# array_writez
a = [1, 2, 3]
b = a
if b:
   a[0] = 0
else:
   a[0] = 1

# packed_args
def my_function2(p1, p2, p3, p4):
   p2['x'] = 2
   p2['y'] = 6
   p4['y'] = 4
a = {'x': 1, 'y': 3}
l = [2, a]
k = {
   'p3': 1,
   'p4': a
}
my_function2(*l, **k)
b = a['x']
b = a['y']

# # packed_parameters
def my_function3(p1, *args, **kwargs):
   p1 = p1 + 6
   args[0] = 2
   args[1][1] = 3
   other_function = kwargs['y'][1]
   other_function()
   p1 = p1 + 6
   

a = 1
b = [-1, -2, -3]
c = 3
d = 4
e = {'m': 1}
my_function3(a, b, c, x=d, y=e)
d = 4

l = [4, 5, 6]
d = {"d": 7, "e": 8}
# l2 = [9, 8, *l, 2]
d2 = {"g": 7, "h": 9, **d, "c": 6}
my_function3(*l, 1, 2, 3, *l, **d2, c=4, b=5)

