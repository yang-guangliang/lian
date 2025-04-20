<?php
$person1 = new Person("Alice", 30);
$person2 = clone $person1;

$person1->name = "Bob"; // 修改 person1 的名字
echo $person2;          // 输出 "Name: Alice, Age: 30"，因为 person2 是独立的
?>