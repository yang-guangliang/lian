// 定义一个 sum 函数，接受可变数量的参数并计算总和
function sum(...numbers) {
    return numbers.reduce((total, number) => total + number, 0);
}

// 定义一个数组
const numbers = [3, 4, 5];

// 调用 sum 函数，并使用扩展运算符来展开数组和其他数值
const result = sum(0, [1, 2], ...numbers, 6);
const result2 = sum(0, 1, 2);

// 输出结果
console.log(result);  // 21 (0 + 1 + 2 + 3 + 4 + 5 + 6)
console.log(result2); // 3 (0 + 1 + 2)

const obj = {
    calculate: {
        sum: function(...numbers) {
            return numbers.reduce((total, number) => total + number, 0);
        }
    }
};

const result3 = obj.calculate?.sum(1, 2, 3);  // 如果 obj.calculate 为 null 或 undefined，则不会抛出错误，而是返回 undefined
console.log(result);  // 输出 6 或 undefined