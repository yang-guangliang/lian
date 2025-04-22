console.log(x)
if (false)
    { var x = 1 }
console.log(x)

var y
console.log(y)
y = 1
console.log(y)

try{
    console.log(z)
    z = 1
    console.log(z)
}
catch{
    console.log("z is not defined")
}

if (true) { 
    let m = 1 
}
else if(true){
    let m = 1 
}

console.log("Testing variable scope ......")
function showGlobal() {
    myVar = "I am global";
    var localVar = "I am local";
}

showGlobal();
console.log(myVar);
console.log(localVar);


if (true) {
    let blockVar = "I am block scoped";
    console.log(blockVar); // 可以访问块级变量
}

console.log(blockVar); // ReferenceError: blockVar is not defined


function outerFunction() {
    var outerVar = "I am outer";
    let innerVar = "I am inner";

    function innerFunction() {
        console.log(outerVar);
        console.log(innerVar);
    }

    return innerFunction;
}

var innerFunc = outerFunction(); // outerFunction执行完毕，但innerFunction仍可以访问outerVar
innerFunc(); // 输出: I am outer