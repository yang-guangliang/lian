function showThis() {
    console.log(this);
}

const obj = { value: 42 };

showThis.call(obj);  // 输出 { value: 42 }，this 被显式绑定为 obj
showThis.apply(obj); // 输出 { value: 42 }，this 被显式绑定为 obj

showThis();          // 输出 全局对象，this 指向全局对象（浏览器中为 window）
const boundShowThis = showThis.bind(obj);
boundShowThis();     // 输出 { value: 42 }，this 永久绑定为 obj


class Example {
    constructor(value) {
        this.value = value;  // 使用this来引用当前实例的属性
        this.getValue = this.getValue.bind(this); // 确保this总是指向当前实例
    }

    setValue(value) {
        this.value = value;  // 修改当前实例的属性
    }

    getValue() {
        return this.value;   // 返回当前实例的属性
    }
}

const example = new Example(42);
console.log(example.getValue()); // 输出: 42

const getValue = example.getValue;
console.log(getValue()); // 在严格模式下会报错，非严格模式下会输出undefined，因为this不再指向example对象