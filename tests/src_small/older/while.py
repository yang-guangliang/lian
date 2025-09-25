def cfg_while():
    count = 0
    while count < 5:
       print(count, " is  less than 5")
       x = count + 1
       if x > 3:
          break
       count += 1
    else:
       print(count, " is not less than 5")
    y = x * 2

cfg_while()
