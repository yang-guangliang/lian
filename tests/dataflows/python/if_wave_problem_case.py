# 2025/5/22 26~30-32-34-33-35-34-36-35-36-42-38-43-40-44-41-42-43-44-48-46-49-47-50-48-49-50-52-57-54

def f(arg): # 22 para_decl
  arg.a = 0 # 26field_write
  arg.b = 0 # 27field_write
  if arg.a < 10: # 28field_read 29assign 30if
      arg.a = 1 # 32field_write
      arg.b = 2 # 33field_write
      
  if arg.b < 10: # 34field_read 35assign 36if 
      b = arg.b # 38field_read
      arg.c = 1 # 40field_write
      arg.d = 2 # 41field_write

  if arg.a < 10: # 42field_read 43assign 44if
      arg.e = 1 # 46field_write
      arg.f = 1 # 47field_write

  if arg.b < 10: #48field_read 49assign 50if
      b = arg.b # 52field_read
      c = arg.c # 54field_read
  else:
      b = arg.b # 57field_read
def f1(x):
  f(x)
