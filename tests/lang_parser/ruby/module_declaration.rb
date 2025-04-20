# Simple module
module SimpleModule
end

# Module with methods
module UtilityModule
  def self.help
    puts "Helping..."
  end
end

# Nested modules
module Outer
  module Inner
    def self.say
      puts "Nested module"
    end
  end
end
