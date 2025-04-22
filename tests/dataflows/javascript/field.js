o = {
    "foo": 1, 
    "baz": 2
}
function p() {
    return true
}

o.foo = 3
f = p() ? "foo" : "baz";
o[f] = 4