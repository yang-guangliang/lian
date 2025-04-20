begin
  10 / 0  
rescue ZeroDivisionError => e  
  puts "**Exception caught!**" 
  puts "Dividing by zero is not allowed."
end