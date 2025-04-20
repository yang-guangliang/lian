function f(x = function(){return 1}){
    x();
}

function g(x = f()) { }
a = g();
