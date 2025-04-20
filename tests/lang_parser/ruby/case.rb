day = "Wednesday"
case day
when "Monday"
  puts "It's the start of the week!"
when "Tuesday"
  puts "It's the middle of the week."
when "Thursday"
  puts "It's almost the weekend."
when "Friday"
  puts "It's the weekend!"
else
  puts "Invalid day of the week: #{day}"
end