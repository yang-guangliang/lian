#!/usr/bin/env python3

validators = {
    "a": function(x) {return x;}
}

function f(p) {
    for (x in validators) {
            target[x] = validators[x]
    }
    
}

target = Object()
f(target)
console.log(target)
