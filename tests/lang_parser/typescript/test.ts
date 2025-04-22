// // test2
outerLoop: for (let i = 0, j = 10; i < 5; i++ , --j) {
  let obj = { a: 1, b: 2, c: 3 };
  for (let key in obj) {
    if(obj[key] == 2){
      break outerLoop;
    }
    else{
      continue;
    }
  }
}

const arr = [1, 2, 3];
for (let [index, value] of arr.entries()) {
  console.log(index, value);
}

// // 定义一个异步生成器函数
// async function* asyncGenerator() {
//   yield Promise.resolve(6);
//   yield Promise.resolve(7);
//   yield Promise.resolve(8);
//   yield Promise.resolve(9);
//   yield Promise.resolve(10);
// }

// // 定义一个异步迭代的数据结构
// const asyncIterable = {
//   [Symbol.asyncIterator]: async function* () {
//     yield Promise.resolve(11);
//     yield Promise.resolve(12);
//     yield Promise.resolve(13);
//     yield Promise.resolve(14);
//     yield Promise.resolve(15);
//   }
// };
// // 使用 for...of 遍历异步迭代的生成器函数
// console.log("Using for...of to iterate over async generator function:");
(async () => {
  for await (let value of asyncGenerator()) {
    console.log(value);
  }
})();
// // 使用 for...of 遍历异步迭代的数据结构
// console.log("Using for...of to iterate over async iterable object:");
// (async () => {
//   for await (let value of asyncIterable) {
//     console.log(value);
//   }
// })();


// 使用 with 语句简化访问对象属性
const obj = { a: 1, b: 2, c: 3 };
with (obj) {
    console.log(b); // 输出 2
}
//------------------------------------------------
export * from './module';
export * as ns from './module';
export { name1, name2 as n2 } from './module';
export { name1, name2 as n2 };
export function foo() {}
export default function() {}
export default a+b;
export type { Type1, Type2 as t2} from './types';
export type { Type1, Type2 as t2};
export = a+b;
export as namespace ns;

//------------------------------------------------
// throw statement
throw new Error("This is a test error");

// import statement
import { readFileSync } from 'fs';
import { join as pathJoin } from 'path';

// try statement
try {
    const data = readFileSync('test.txt', 'utf8');
} catch (err) {
    console.error(err);
} finally {
    console.log('Finished reading file');
}

// switch statement
switch (value) {
    case 1:
        console.log('Value is 1');
        break;
    case 2:
        console.log('Value is 2');
        break;
    default:
        console.log('Value is unknown');
}

while(a > 0){
  do{
    console.log(a);
  }while( a < 1)
}


