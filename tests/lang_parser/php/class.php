<?php
// trait Displayable {
//   public function displayInfo() {
//     echo "The fruit is {$this->name} and its color is {$this->color}.";
//   }
// }

class Fruit {
  // Properties
  public $name = '';
  public $color;

  // Methods
  function set_name($name) {
    $this->name = $name;
  }

  function get_name() {
    return $this->name;
  }

  use Displayable; // Use the Displayable trait
}

// class MyClass {
//   public static $count = 0;

//   public static function incrementCount() {
//       self::$count++;
//       echo "Count is now: " . self::$count . "\n";
//   }

//   public static function getCount() {
//       return self::$count;
//   }
// }

// interface Template
// {
//     public function setVariable($name, $var);
//     public function getHtml($template);
// }

// 接口的多继承
interface InterfaceA {
  public function methodA();
}

interface InterfaceB {
  public function methodB();
}

// 定义一个接口C，它继承了InterfaceA和InterfaceB
interface InterfaceC extends InterfaceA, InterfaceB {
  // 这里可以添加新的方法或者保持为空，
  // 只继承InterfaceA和InterfaceB的所有方法
}
?>