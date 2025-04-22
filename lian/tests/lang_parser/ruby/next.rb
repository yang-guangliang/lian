numbers = [1, 2, 3, 4, 5, 6, 7, 8]
    
sum = 0
loop do
  num = numbers.pop
  sum += num
  
  if num % 3 == 0
    next  
  end
end
puts sum  