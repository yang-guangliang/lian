<?php

// 创建一个多维数组
$multiDimensionalArray = [
    'fruits' => [
        'apple' => [
            'color' => 'red',
            'weight' => 150
        ],
        'banana' => [
            'color' => 'yellow',
            'weight' => 120
        ],
        'cherry' => [
            'color' => 'red',
            'weight' => 5
        ]
    ],
    'vegetables' => [
        'carrot' => [
            'color' => 'orange',
            'weight' => 70
        ],
        'potato' => [
            'color' => 'brown',
            'weight' => 100
        ]
    ]
];

$test = $multiDimensionalArray[0];
$a = $multiDimensionalArray['fruits']['apple']['color'];
$b = $multiDimensionalArray['fruits']['banana']['weight'];
$c = $multiDimensionalArray['fruits']['cherry']['color'];

$multiDimensionalArray['fruits']['apple']['color'] = 'test';

// // 创建一个对象
// class Fruit {
//     public $color;
//     public $weight;

//     public function __construct($color, $weight) {
//         $this->color = $color;
//         $this->weight = $weight;
//     }
// }

// class Basket {
//     public $fruits = [];

//     public function addFruit($fruit) {
//         $this->fruits[] = $fruit;
//     }
// }

// $basket = new Basket();
// $apple = new Fruit('red', 150);
// $banana = new Fruit('yellow', 120);
// $cherry = new Fruit('red', 5);
// $basket->addFruit($apple);
// $basket->addFruit($banana);
// $basket->addFruit($cherry);

// // 动态索引
// $key = 'fruits';
// $subKey = 'apple';
// $property = 'color';

// // 复杂索引
// $keyExpression = 'vegetables';
// $subSubKey = 'carrot';
// $propertyExpression = 'color';

// // 数组片段访问
// $array = [1, 2, 3, 4, 5];
// $start = 1;
// $end = 3;

// // 变量变量
// $dynamicKeyVar = 'fruits';
// $dynamicSubKeyVar = 'apple';
// $dynamicPropertyVar = 'color';

// // 输出结果
// echo "Multi-Dimensional Array Elements:\n";
// echo "Apple Color: " . $multiDimensionalArray['fruits']['apple']['color'] . "\n"; // red
// echo "Banana Weight: " . $multiDimensionalArray['fruits']['banana']['weight'] . "\n"; // 120
// echo "Cherry Color: " . $multiDimensionalArray['fruits']['cherry']['color'] . "\n"; // red

// echo "\nNested Object Properties:\n";
// echo "First Fruit Color: " . $basket->fruits[0]->color . "\n"; // red
// echo "Second Fruit Color: " . $basket->fruits[1]->color . "\n"; // yellow
// echo "Third Fruit Color: " . $basket->fruits[2]->color . "\n"; // red

// echo "\nDynamic Multi-Dimensional Array Elements:\n";
// echo "Apple Color: " . $multiDimensionalArray[$key][$subKey][$property] . "\n"; // red

// echo "\nComplex Multi-Dimensional Array Elements:\n";
// echo "Carrot Color: " . $multiDimensionalArray[$keyExpression][$subSubKey][$propertyExpression] . "\n"; // orange

// echo "\nArray Fragment:\n";
// echo "Fragment: ";
// print_r($array[$start:$end]); // [2, 3]

// echo "\nVariable Variable:\n";
// echo "Apple Color: " . ${$dynamicKeyVar}[$dynamicSubKeyVar][$dynamicPropertyVar] . "\n"; // red

?>