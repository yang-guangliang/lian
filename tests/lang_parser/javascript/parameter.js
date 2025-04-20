a = 4
g = 5
function add(a, b = a + 4, c = g) {
  console.log(a, b, c)
  return a + b + c;
}
a = 10
g = 6
console.log(add(5, 2));
console.log(add(5));