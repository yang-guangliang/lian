try {
    throw {a: "1", b: "2"};
} catch ({a, b}) {
    console.log(a); // 输出: Error1
    console.log(b); // 输出: Error2
}