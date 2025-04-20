// 从 test2.js 导入 myConst 和 sayHello 函数
// import { myConst, sayHello } from './test1.js';

// console.log(myConst); // 输出: Hello, World!
// console.log(sayHello('ES6 Modules')); // 输出: Hello, ES6 Modules!

// 从 test2.js 导入 myConst 和 sayHello 函数
import * as myModule from 'test1.js';
// ==> import test1 as myModule
// ==> import a.b.test1 .....

console.log(myModule.myConst); // 输出: Hello, World!
console.log(myModule.sayHello('ES6 Modules')); // 输出: Hello, ES6 Modules!