<?php
function myMessage() {
  echo "Hello world!";
}

myMessage();

class MyClass {
    public static function myStaticMethod($arg1, $arg2) {
        return "Called static method with arguments: $arg1, $arg2";
    }
}

echo MyClass::myStaticMethod('hello', 'world');

$obj = new MyClass();
echo $obj->myInstanceMethod('hello', 'world');
echo $obj?->myInstanceMethod('hello', 'world');

?>