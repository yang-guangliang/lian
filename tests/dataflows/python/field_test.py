def field():
   a = 1.03
   a.f = 33333
   a.g = 44444
   if a:
      a.f = 55555
   b = a.f # Challenge:只有5了，3丢了。line3和line8中，a的state都是同一个，直接将line3覆盖了 
            #已解决，每次write时clone一个新的state
   o1 = 1.2222222
   o2 = 1.3333333
   x = 999
   o2.f = x
   o1.f = o2
   y = o1.f.f
   
