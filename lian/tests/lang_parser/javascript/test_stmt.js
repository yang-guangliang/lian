// if_statement
// case 1
if(age < 18){
    console.log("1");
}else if(age < 30){
    console.log("2");
}else
    console.log("3");

// case 2
if(a > 0)
    if(a < 10)
        alert(123);
    else
        alert(456);


// while_statement
a = 0
while (a++ < 10) {
    console.log(a);
}


// do_statement
result = "";
i = 0;
do {
    i += 1;
    result += `${i} `;
} while (i > 0 && i < 5);


// for_statement
// case 1
for (let i = ("start" in window) ? window.start : 0; i < 9; i++) {
    console.log(i);
}

// case 2
i = 0;
for (;;) {
    if (i > 3) break;
    console.log(i);
    i++;
}

// case 3
for (let i = 0, getI = () => i; i < 3; i++, getI = () => i) {
    console.log(getI());
}


// for_in_statement
// case 1
const obj = { a: 1, b: 2 };

for (const prop in obj) {
    console.log(`obj.${prop} = ${obj[prop]}`);
    Object.setPrototypeOf(obj, { c: 3 });
}

// case 2
const iterable = new Map([
    ["a", 1],
    ["b", 2],
]);
  
for (const entry of iterable) {
    console.log(entry);
}
  
for (const [key, value] of iterable) {
    console.log(value);
}


// try_statement && throw_statement
// case 1
try {
    throw new TypeError("oops");
} catch ({ name, message }) {
    console.log(name); // "TypeError"
    console.log(message); // "oops"
}

// case 2
try {
    try {
        throw new Error("oops");
    } finally {
        console.log("finally");
    }
} catch (ex) {
    console.error("outer", ex.message);
}


// with_statement
// case 1
with ([1, 2, 3]) {
    console.log(toString()); // 1,2,3
}

// case 2
with (Math) {
    a = PI * r * r;
    x = r * cos(PI);
    y = r * sin(PI / 2);
}

// switch_statement
Animal = "Giraffe";
switch (Animal) {
    case "Cow":
    case "Giraffe":
    case "Dog":
    case "Pig":
        console.log("This animal is not extinct.");
        break;
    case "Dinosaur":
    default:
        console.log("This animal is extinct.");
}


// import_statement
import * as myModule from "/modules/my-module.js";

import { LongModuleExportName as shortName } from "/modules/my-module.js";

import "/modules/my-module.js";

import myDefault from "/modules/my-module.js";

import myDefault, * as myModule from "/modules/my-module.js";

import myDefault, { foo, bar } from "/modules/my-module.js";


// export_statement
export { myFunction as function1, myVariable as variable };

export default function () {
    console.log("Hi");
}

export * as ns from "mod";

export * from "module-name";

export { default as function1, function2 } from "bar.js";

export const name1 = 1, name2 = 2;

export const [ name1, name2 ] = array;


// labeled_statement
// case 1
handleFriends: {
    if (!user.loggedIn) {
        console.log("You are not logged in");
        break handleFriends;
    }
    const friends = user.getFriends();
    if (!friends.length) {
        console.log("No friends found");
        break handleFriends;
    }
    for (const friend of friends) {
        handleFriend(friend);
    }
}

// case 2
// The first for statement is labeled "loop1"
loop1: for (let i = 0; i < 3; i++) {
    // The second for statement is labeled "loop2"
    loop2: for (let j = 0; j < 3; j++) {
        if (i === 1 && j === 1) {
            continue loop1;
        }
        console.log(`i = ${i}, j = ${j}`);
    }
}


// return_statement
// case 1
counter = function () {
    for (let count = 1; ; count++) {
        if (count === 5) {
            return;
        }
    }
}

// case 2
for (var i = 0; i < 2; i++) {
    const button = document.createElement("button");
    button.innerText = `Button ${i}`;
    button.onclick = (function (copyOfI) {
        return function () {
            console.log(copyOfI);
        };
    })(i);
    document.body.appendChild(button);
}


// 测试expression部分新增的内容
[a, b] = [c, d] = [3, 4];

re = /\w+\s/g;

foo = function* () {
    yield 'a';
    yield 'b';
    yield 'c';
};
