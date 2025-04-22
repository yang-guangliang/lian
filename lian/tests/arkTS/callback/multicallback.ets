const a = {
  b: {
    c: function (message) {
      console.log("Callback Message:", message);
    }
  }
};

// 接收一个回调并执行
function executeCallback(callback, message) {
  console.log("Executing callback...");
  callback.b.c(message);
}

// 传递 a.b.c 作为回调函数
executeCallback(a, "Hello from Callback");
// 输出:
// Executing callback...
// Callback Message: Hello from Callback
