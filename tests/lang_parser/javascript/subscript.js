// 创建一个多维对象
const multiDimensionalObject = {
    fruits: {
        apple: {
            color: 'red',
            weight: 150
        },
        banana: {
            color: 'yellow',
            weight: 120
        },
        cherry: {
            color: 'red',
            weight: 5
        }
    },
    vegetables: {
        carrot: {
            color: 'orange',
            weight: 70
        },
        potato: {
            color: 'brown',
            weight: 100
        }
    }
};

let test = multiDimensionalObject[0];
let a = multiDimensionalObject['fruits']['apple']['color'];
let b = multiDimensionalObject['fruits']['banana']['weight'];
let c = multiDimensionalObject['fruits']['cherry']['color'];

multiDimensionalObject['fruits']['apple']['color'] = 'test';

// // 创建一个类
// class Fruit {
//     constructor(color, weight) {
//         this.color = color;
//         this.weight = weight;
//     }
// }

// class Basket {
//     constructor() {
//         this.fruits = [];
//     }

//     addFruit(fruit) {
//         this.fruits.push(fruit);
//     }
// }

// // 创建一个篮子对象并添加水果
// const basket = new Basket();
// const apple = new Fruit('red', 150);
// const banana = new Fruit('yellow', 120);
// const cherry = new Fruit('red', 5);
// basket.addFruit(apple);
// basket.addFruit(banana);
// basket.addFruit(cherry);

// // 动态索引
// const key = 'fruits';
// const subKey = 'apple';
// const property = 'color';

// // 复杂索引
// const keyExpression = 'vegetables';
// const subSubKey = 'carrot';
// const propertyExpression = 'color';

// // 数组片段访问
// const array = [1, 2, 3, 4, 5];
// const start = 1;
// const end = 3;

// // 变量变量
// const dynamicKeyVar = 'fruits';
// const dynamicSubKeyVar = 'apple';
// const dynamicPropertyVar = 'color';

// // 输出结果
// console.log("Multi-Dimensional Object Elements:");
// console.log(`Apple Color: ${multiDimensionalObject["fruits"]["apple"]["color"]}`);  // red
// console.log(`Banana Weight: ${multiDimensionalObject.fruits.banana.weight}`);  // 120
// console.log(`Cherry Color: ${multiDimensionalObject.fruits.cherry.color}`);  // red

// console.log("\nNested Object Properties:");
// console.log(`First Fruit Color: ${basket.fruits[0].color}`);  // red
// console.log(`Second Fruit Color: ${basket.fruits[1].color}`);  // yellow
// console.log(`Third Fruit Color: ${basket.fruits[2].color}`);  // red

// console.log("\nDynamic Multi-Dimensional Object Elements:");
// console.log(`Apple Color: ${multiDimensionalObject[key][subKey][property]}`);  // red

// console.log("\nComplex Multi-Dimensional Object Elements:");
// console.log(`Carrot Color: ${multiDimensionalObject[keyExpression][subSubKey][propertyExpression]}`);  // orange

// console.log("\nArray Slice:");
// console.log(`Fragment: ${array.slice(start, end)}`);  // [2, 3]

// console.log("\nVariable Variable:");
// console.log(`Apple Color: ${eval(`${dynamicKeyVar}.${dynamicSubKeyVar}.${dynamicPropertyVar}`)}`);  // red