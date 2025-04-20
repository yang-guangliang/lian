# Simple class
class SimpleClass
end

# Class with inheritance
class ChildClass < SimpleClass
  def method1
    puts "Inherited method"
  end
end

# Class with methods and variables
class ComplexClass
  attr_accessor :name
  
  def initialize(name)
    @name = name
  end
  
  def greet
    puts "Hello #{@name}"
  end
end
