matrix = [[i * j for j in range(3)] for i in [k + 2 for k in range(4) if k % 2 == 0]]
"""
# [k + 2 for k in range(3) if k % 2 == 0]
%v0 = new_array
%v1 = range(3)
%v2 = 0
while %v2 < len(%v1):
    k = %v1[%v2]
    if k % 2 == 0:
        %v3 = k + 2
        array_write(%v0, %v3, %v2)
    %v2 += 1



matrix = [[i * j for j in range(3)] for i in %v0]
"""
b = {y:y for y in a}
y = [x * 2 for row in matrix for x in row if x % 2 == 0]
"""
for row in matrix:
    for x in row:
        if x % 2 == 0:
            x * 2

"""
"""
%v0 = 0
%v1 = new_array
while %v0 < len(matrix):
  row = matrix[%v0]
  for x in row
  %v0 += 1
  array_write(%v1, x * 2, %v0)
"""