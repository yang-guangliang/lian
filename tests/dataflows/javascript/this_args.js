// object method
const obj = {
    method: function() {
      console.log(this); // 这里的 this 指向 obj
    },
    a : 3
  };
  
obj.method(); // 输出 obj

// class method
class MyClass {
    constructor(name) {
      this.name = name;
    }
  
    sayHello() {
      console.log(this);
    }
  }
  
const obj2 = new MyClass('Alice');
obj2.sayHello();  // obj2

// dynamic method
const obj21 = new MyClass('Alice');
console.log(obj21.sayHello);
a = obj21.sayHello;
console.log(a);
a() // undefined

// function
function globalFunc() {
    this.name = 'Instance';
    console.log(this);
}
globalFunc();// 输出 global 对象
const instance2 = new globalFunc();

// array method
const arr = [1, globalFunc, 3];
arr[1](); // 输出 arr 对象