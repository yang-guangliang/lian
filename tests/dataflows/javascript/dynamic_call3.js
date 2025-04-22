function MyClass() {
    this.abc = function() {
        alert("abc");
    }
}

var myObject = new MyClass();
myObject["abc"]();
