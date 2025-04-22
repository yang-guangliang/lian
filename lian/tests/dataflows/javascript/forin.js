let a = [1, 2]
let b = {
    "k1": "v1", 
    "k2": "v2"
}
let c = 3

let l = [a, b, c]

let record_dict1 = {}
let record_dict2 = {}
// let l = [1, 2, 3]
// for (const key in l) {
//     record_dict1[key] = key
// }

index = 0
for (const value of l) {
    record_dict2[index] = value
    index += 1
}

// const person = {name: "John", age: 30, city: "New York"};
// for (let key in person) {
//     console.log(key, ":", person[key]);
// }

// const numbers = [1, 2, 3, 4, 5];
// for (const number of numbers) {
//     console.log(number);
// }