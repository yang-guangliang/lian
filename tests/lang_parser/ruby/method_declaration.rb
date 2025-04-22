# Method without parameters
def no_params
  puts "No parameters"
end

# Method with parameters
def with_params(a, b = 10, *args, **opts)
  puts "Parameters: #{a}, #{b}, #{args}, #{opts}"
end

# Method with complex body
def complex_body(x)
  if x > 0
    puts "Positive"
  else
    puts "Non-positive"
  end
end
