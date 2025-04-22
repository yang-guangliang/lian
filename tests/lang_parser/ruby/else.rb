
do
  puts "Enter a word (or 'quit' to exit): "
  word = gets.chomp
  if word == 'quit'
    break
  else
    puts "You entered: #{word}"
  end
end