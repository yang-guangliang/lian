# Singleton class on an object
obj = Object.new
class << obj
  def speak
    puts "Hello from singleton class"
  end
end

obj.speak
