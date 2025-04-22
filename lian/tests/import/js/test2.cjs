var example = require('./test1.cjs');
console.log(example)
// ==> import * as example from './test1.cjs'
// 

console.log(example.x); // 5
// console.log(example.addX(1)); // 6
console.log(example.addX(1)); // 6

var y = require("./test1.cjs").x
// ==> import x as y from './test1.cjs'

console.log(y)