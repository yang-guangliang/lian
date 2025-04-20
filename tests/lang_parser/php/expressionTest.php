<?php
// clone
class MyClass {
  public $color;
  public $amount;
  const MY_CONSTANT = "Hello, World!";
  public static $staticProperty = "Hello, World!";
}

$obj = new MyClass();
$copy = clone $obj;

// class_constant_access_expression
echo MyClass::MY_CONSTANT; // 输出 "Hello, World!"
echo MyClass::$staticProperty; // 不带命名空间的静态属性访问
echo \MyClass::$staticProperty; // 使用完全限定名称访问静态属性
?>