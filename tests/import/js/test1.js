// // 定义一个常量
// const myConst = 'Hello, World!';

// // 定义一个函数
// function sayHello(name) {
//   return `Hello, ${name}!`;
// }

// // 导出
// export { myConst, sayHello };

// // 修改export解析结构

var x = 5;
var add = function (value) {
  return value + 1;
};
module.exports.x = x;
module.exports.add = add;
exports.x = x;
module.exports = x;

module.exports = {
    x: 5, 
    add: function (value) {
        return value + 1
    }
}

// var x = 5;
// var addX = function (value) {
//   return value + x;
// };
// module.exports.x = x;
// // export_stmt alias:x, content:x 
// module.exports.addX = addX;
// // export_stmt content: addX 



// module.exports = {
//     x: 5, 
//     addX: function (value) {
//         return value + x
//     }
// }
// function %m0() ...

// export_stmt alias:x 5
// export_stmt alias:addX %m0