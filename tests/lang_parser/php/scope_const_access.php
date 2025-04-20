<?php
class Parent {

    public static function foo() {
       echo 'foo';
    }
}

class Child extends Parent {

    public static function func() {
       self::foo();
    }

    public static function func2() {
       parent::foo();
    }
}
?>