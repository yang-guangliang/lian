import test from "./defaultExport.js";
// ==> import defaultExport as test

console.log(test.sayHello('test'))
console.log(test.myConst)

import * as myModule from './test1.js';
// ==> import test1 as myModule
import * as myDirModule from './a/b/test1.js';
// ==> from a.b import test1 as myModule

console.log(myModule.myConst); // 输出: Hello, World!
console.log(myModule.sayHello('ES6 Modules')); // 输出: Hello, ES6 Modules!

console.log(myDirModule.myConst); // 输出: Hello, World!
console.log(myDirModule.sayHello('ES6 Modules')); // 输出: Hello, ES6 Modules!