function showName() {
  console.log(this.name);
}

const obj = { name: 'Alice' };

showName.call(obj); // 输出：Alice
showName.apply(obj); // 输出：Alice

const boundFunc = showName.bind(obj);
boundFunc(); // 输出：Alice
