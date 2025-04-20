// class method
const o1 = {
  f() { this.g(); },
  g() { console.log("foo"); },
};


class MyClass {
    constructor(name) {
      this.name = name;
    }
  
    sayHello() {
      console.log(this);
    }
  }
  
// dynamic method
const obj21 = new MyClass('Alice');
a = obj21.sayHello;
a() 
