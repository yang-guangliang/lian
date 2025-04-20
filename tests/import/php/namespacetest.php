<?php

require 'Math/Calculator.php';
// ==> from （只能是文件名）Math.Calculator import *
// import + attrs

// 定义 greet 函数
function greet($name) {
    return "Hello, $name!";
}

// 主程序
$calc = new \Math\Calculator();
echo $calc->add(10, 20); // 输出 30

echo greet('World'); // 输出 Hello, World!