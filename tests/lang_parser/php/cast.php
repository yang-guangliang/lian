<?php
$number = "42";
$integerNumber = (int) $number; // 显式类型转换为整型
echo gettype($integerNumber);   // 输出 "integer"

$floatNumber = (float) "3.14";
echo gettype($floatNumber);     // 输出 "double" （PHP 中 float 和 double 是同义词）

$stringValue = (string) true;
echo gettype($stringValue);     // 输出 "string"

$boolValue = (bool) "";
echo gettype($boolValue);       // 输出 "boolean"

$arrayValue = (array) "hello";
print_r($arrayValue);           // 输出 Array ( [0] => h [1] => e [2] => l [3] => l [4] => o )

$objectValue = (object) ["name" => "Alice"];
print_r($objectValue);          // 输出 stdClass Object ( [name] => Alice )
?>