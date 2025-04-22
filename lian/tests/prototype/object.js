const o = {
    a: 1,
    b: 2,
    // __proto__ 设置了 [[Prototype]]。它在这里被指定为另一个对象字面量。
    __proto__: {
        b: 3,
        c: 4,
        __proto__: {
            d: 5,
        },
    },
};

// { a: 1, b: 2 } ---> { b: 3, c: 4 } ---> { d: 5 } ---> Object.prototype ---> null
e = o.d;
console.log(o.d); // 5

