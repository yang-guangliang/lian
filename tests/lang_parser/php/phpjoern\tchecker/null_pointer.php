<?php
class Greeter {
// 接受⼀个匿名类作为参数的⽅法
public function greet($greetingObject) {
echo $greetingObject->sayHello();
 }
}
// 创建 Greeter 类的实例
$greeter = new Greeter();
// 调⽤ greet ⽅法，传递匿名类作为参数
$greeter->greet(new class {
public $message = "Hello from an anonymous class!";
public function sayHello() {
return $this->message;
 }
});