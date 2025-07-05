g = 1

// function f1() {
//     g += 1
//     return g
// }

// function f2() {
//     a = g
//     return g
// }

// function main() {
//     f0 = {}
//     f0.f = f1
//     if (Math.random()) {
//         f0.f = f2
//     } else {
//         a = f0.f()
//         b= f0
//     }
// }

// main()
document.addEventListener('click', function() {
    console.log('文档被点击了！');
});

// 使用匿名函数作为回调函数
setTimeout(function() {
    console.log('2秒后执行此匿名函数');
}, 2000);