Function.prototype.toString = function() {
    return this();
}

var x = 1;
var y = function() { return x }
x++;
alert(y);
