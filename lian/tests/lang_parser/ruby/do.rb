do 
  puts "Hello, World!"
  p "This is a do block"
end


x = 10
do 
  x += 5
  p x
  p "Inside the do loop"
end


do
  puts "Counting down..."
  count = 10
  break if count == 1
  count -= 1
end