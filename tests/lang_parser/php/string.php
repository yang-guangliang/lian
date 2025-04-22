<?php
// $name = "Alice";
// $age = 30;

// // 直接嵌入变量
// $greeting = "Hello, my name is $name and I am $age years old. \n";
// echo $greeting;  // 输出: Hello, my name is Alice and I am 30 years old.

// // 嵌入数组元素
// $array = ["apple", "banana", "cherry"];
// $fruit = "I like " . $array[0] . " and " . $array[1] . "." . "\n";
// echo $fruit;  // 输出: I like apple and banana.

// 嵌入对象属性
class Person {
    public $name;
    public $age;

    public function __construct($name, $age) {
        $this->name = $name;
        $this->age = $age;
    }

    public function greet() {
        return "Hello, my name is {$this->name} and I am {$this->age} years old.";
    }
}

// $person = new Person("Alice", 30);
// echo $person->greet();  // 输出: Hello, my name is Alice and I am 30 years old.
?>