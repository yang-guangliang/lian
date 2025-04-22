var countMe = ( function() {
  var c = 0;

  return function() {
    c++;
    return c;
  }
})();

a = countMe(); // Alerts "1"
b = countMe(); // Alerts "2"
