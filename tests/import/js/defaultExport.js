// 定义一个常量
const myConst = 'Hello, World!';

// 定义一个函数
function sayHello(name) {
  return `Hello, ${name}!`;
}

// 导出
// export  { myConst, sayHello };

export default {sayHello};

export {a as t, b};

export {c, d as p} from "module";

export {} from "module2";

export * as test from "module3"

// 修改export解析结构