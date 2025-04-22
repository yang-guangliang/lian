<?php

trait TraitA {
    const A = 'A';

    private static $a = 1;

    // 定义一个公共方法
    public function methodA() {
        echo "This is method A from TraitA.\n";
    }

    // 定义一个受保护的方法
    protected function protectedMethodA($pa) {
        echo "This is protected method A from TraitA.\n";
        return $pa;
    }

    // 定义一个私有方法
    private function privateMethodA() {
        echo "This is private method A from TraitA.\n";
    }
}

class MyClass {
    use TraitA;
}

// ```
// var_decl %vv1
// call_stmt target: %vv2 name: TraitA
// assign_stmt target: %vv1 oprand: %vv2
// ```

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

?>