numbers = [1, 2, 3, 4, 5, 6, 7, 8]

even_numbers = numbers unless numbers % 2 == 1
puts even_numbers  

odd_numbers = numbers unless numbers % 2 == 0
puts odd_numbers  

