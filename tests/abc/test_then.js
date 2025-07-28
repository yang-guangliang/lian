class ABC {
  func1() {
    // 空方法，对应Python中的pass
  }
}

function func2(pp) {
    let ff = pp.func1
  // 空函数
}

const a = new ABC();
const b = ABC.then; // 注意：标准类没有then方法，需要特殊处理
const c = func2;

// 如果b存在则调用（需先实现then方法）
b(c); 

// function aaa(num) {
//     return num
// }

// num1 = 3

// aaa(num1)