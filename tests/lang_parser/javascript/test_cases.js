// 1. 条件判断
// if
if (time < 10) {
    greeting = "Good morning";
} else if (time < 20) {
    greeting = "Good day";
} else {
    greeting = "Good evening";
} 
// switch
const expr = 'Papayas';
switch (expr) {
case 'Oranges':
    console.log('Oranges are $0.59 a pound.');
    break;
case 'Mangoes':
case 'Papayas':
    console.log('Mangoes and papayas are $2.79 a pound.');
    // Expected output: "Mangoes and papayas are $2.79 a pound."
    break;
default:
    console.log(`Sorry, we are out of ${expr}.`);
}
// 2. 循环
// for
// 基本的 for 循环
for (let i = 0; i < 5; i++) {
    console.log(i);
}
// 倒序循环
for (let i = 4; i >= 0; i--) {
    console.log(i);
}
// 循环数组元素
const arr = ['apple', 'banana', 'orange'];
for (let i = 0; i < arr.length; i++) {
    console.log(arr[i]);
}

// for_in
var arr2 = { 
    name: "Searchin",
    age:18,
    address:"beijing" 
}; 
for(var i in arr){ 
    console.log(i); //若想输出属性值，则console.log(arr[i])
} 

// while
let i = 0;
while (i < 5) {
    console.log(i);
    i++;
}

// do
let i = 0;
do {
    console.log(i);
    i++;
} while (i < 5);

// 3. 跳转 (带labeled_statement一起测试)
// break
outer:
for (var i = 0; i < 3; i++) {
    console.log("外层循环：" + i);
    
    for (var j = 0; j < 3; j++) {
        console.log("    内层循环：" + j);
        break outer; 
    }
}

// continue
outer:
for (var i = 0; i < 3; i++) {
    a = a + i;
    continue outer; 
}

// return_statement
function add(a, b) {
    var result = a + b;
    return result; // 返回计算结果给调用者
}

// 4. 其他
//import
import defaultExport from "module-name";
import * as name from "module-name";
import { export1 } from "module-name";
import { export1 as alias1 } from "module-name";
import { default as alias } from "module-name";
import { export1, export2 } from "module-name";
import { export1, export2 as alias2, temp } from "module-name";
// import { "abc" as alias } from "module-name";
import defaultExport, { export1, exp2 } from "module-name";
import defaultExport, * as name from "module-name";
import "module-name";

// throw
function checkPositiveNumber(number) {
    if (typeof number !== 'number' || number <= 0) {
        throw new Error('传入的参数必须是一个正数'); // 抛出一个带有错误消息的异常
    }
    return true;
}

// with
var person = {
    name: "John",
    age: 30,
    country: "USA"
};

// 使用 with 语句简化代码
with (person) {
    console.log(name + " is " + age + " years old and lives in " + country + ".");
}

// try
export function divideNumbers(a, b) {
    try {
      if (b === 0) {
        throw new Error("Division by zero is not allowed.");
      }
      return a / b;
    } catch (error) {
      console.error("Caught an error!");
      return null;
    }
}

// export
export let name1;
export let myVariable = Math.sqrt(2);
export function cube(x) {
  return x * x * x;
};
export { key, value };
export { helloworld as default };
export { default as bar, customer } from "bar.js";
export {child as kid} from "./childModule1.mjs";




