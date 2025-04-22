<?php
$x = 5;
$y = "world";

// 定义一个匿名函数，并使用 use 关键字来捕获外部变量 $x 和 $y
$func = function () use ($x, $y) {
    echo "The value of x is: $x and the value of y is: $y\n";
};

// 调用匿名函数
$func();