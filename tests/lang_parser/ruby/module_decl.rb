module Utilities
    def self.format_string(str)
      str.strip.capitalize
    end
  
    def self.factorial(n)
      return 1 if n <= 1
      n * factorial(n - 1)
    end