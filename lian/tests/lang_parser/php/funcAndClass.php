<?php
function sum(int ...$numbers) {
    $total = 0;
    foreach ($numbers as $number) {
        $total += $number;
    }
    return $total;
}
$numbers = [3, 4, 5];
$result = sum(0, [1, 2], ...$numbers, 6);
$result2 = sum(0, [1, 2]);
print $result;

// // simple parameter
// function greet(string $name, int $age = 20) {
//     echo "Hello, my name is $name and I am $age years old.";
// }

// class User implements Named
// {
//     private bool $isModified = false;
 
//     public function __construct(
//         private string $first,
//         private string $last
//     ) {}
 
//     public string $fullName {
//         // Override the "read" action with arbitrary logic.
//         get => $this->first . " " . $this->last;
 
//         // Override the "write" action with arbitrary logic.
//         set {
//             [$this->first, $this->last] = explode(' ', $value, 2);
//             $this->isModified = true;
//         }
//     }
// }

// $factor=10;
// $multiplier = function($n) use ($factor) {
//     return $n * $factor;
// };

// // variadic_parameter
// function sum(int ...$numbers): int {
//     $y = 1;
//     return array_sum($numbers);
// }

// // arrow function
// $y = 1;
// $fn1 = fn($x) => $x + $y;
// // 匿名函数
// $fn2 = function ($x) {
//     return $x;
// };
// // equivalent to using $y by value:
// $fn3 = function ($x) use ($y) {
//     return $x + $y;
// };

// // property_promotion_parameter
// class MyClass {
//     public function __construct(public readonly int $x = 10, protected string $y = "Hello") {
//         // ...
//     }
// }

// $obj = new MyClass();
// echo $obj->x;
?>