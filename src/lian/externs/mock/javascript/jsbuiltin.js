// a[1,2,3];
// a.forEach(function (value, pos, array) { for index in a: m1(a[index], index, a) });
// a.forEach(m1, thisArg) { m1.call(thisArg, value, index, array)  }
// function m1(value, index, array) { this.f = 3 }
// [solution] stmt.used_symbols => compute_target_method_states_when_first_args_is_this()
function forEach(callback) {
    for (var index in this) {
        callback(obj[index], index, obj);
    }
}

function push(e) {
    this[e] = e;
}

function Promise(callback) {
    callback()
}

function then(callback){
    callback()
}

function setTimeout(callback) {
    callback()
}

// function map(callback, thisArg) {
//     obj = this;
//     this = thisArg;
//     var result = [];
//     for (var index in obj) {
//         result.push(callback(obj[index], index, obj));
//     }
//     return result;
// }

// function filter(callback, thisArg) {
//     obj = this;
//     this = thisArg;
//     var result = [];
//     for (var index in obj) {
//         if (callback(obj[index], index, obj)) {
//             result.push(obj[index]);
//         }
//     }
//     return result;
// }

// function reduce(callback, initialValue) {
//     obj = this;
//     for (var index in obj) {
//         initialValue = callback(initialValue, obj[index], index, obj);
//     }
// }

// function reduceRight(callback, initialValue) {
//     obj = this;
//     for (var index in obj) {
//         initialValue = callback(initialValue, obj[index], index, obj);
//     }
// }

// function push(element) {
//     this[this.length] = element;
//     this.length++;
//     return this.length;
// }

// function pop() {
//     var result = this[this.length - 1];
//     delete this[this.length - 1];
//     this.length--;
//     return result;
// }

// function slice(start, end) {
//     var result = [];
//     for (var index = start; index < end; index++) {
//         result.push(this[index]);
//     }
// }

// function apply(thisArg, args) {
//     this = thisArg;
//     for (var index in args) {
//         this[index] = args[index];
//     }
// }

// function bind(thisArg, callback) {
//     this = thisArg;
//     function newFunction() {
//         callback.apply(thisArg, arguments);
//     }
// }
