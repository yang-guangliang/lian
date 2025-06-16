// 全局词法环境
const globalVar = '全局变量';

function outerFunction() {
  // outerFunction的词法环境
  const outerVar = '外部函数变量';
  let d = globalVar
  a(d)
  let innerFunction =  ()=> {
    // innerFunction的词法环境
    const innerVar = '内部函数变量';

    let a = globalVar
    let b = outerVar
    console.log(innerVar); // 访问自己的变量
    console.log(outerVar); // 访问外部函数的变量（闭包）
    console.log(globalVar); // 访问全局变量
  }

  innerFunction();

  // 尝试访问内部函数的变量 - 会报错

}

outerFunction();