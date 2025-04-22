function f1(o, p1) {
    o = {
        "k1": 1, 
        "k2": 2
    }

    testvar = o[p1]
}

let receiver_object = [1, 2, 3]
receiver_object["key"] = 9

let a = receiver_object[1]
let b = receiver_object.key

let receiver_object2 = {
    "key1": 1
}

let var1 = receiver_object[0]
let var2 = receiver_object["key1"]
let var3 = receiver_object2[0]
let var4 = receiver_object2["key1"]

let index = 0

receiver_object2[0] = 9

testvar2 = receiver_object[index]
console.log("receiver_object: ", receiver_object)
receiver_object[index] = [1, 2, 3]
console.log("receiver_object: ", receiver_object)
receiver_object[index] = {"key": 1}
console.log("receiver_object: ", receiver_object)
console.log("receiver_object: ", receiver_object)

index = "2"
receiver_object[index] = 99

for (const key in receiver_object) {
    const element = receiver_object[key];
    console.log(key, " : ", element)
}
