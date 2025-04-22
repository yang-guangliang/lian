<?php
namespace MyNamespace\First {


const MY_CONST = 'This is a constant in the namespace.';

function myFunction() {
    echo "Hello from function in namespace MyNamespace\n";
}

class MyClass {
    public function hello() {
        echo "Hello from namespace MyNamespace\n";
    }
    
    public function useFunctionAndConst() {
        echo myFunction() . " and const: " . MY_CONST . "\n";
    }
}

// 创建对象并调用其方法
$obj = new MyClass();
$obj->hello();
$obj->useFunctionAndConst();
}


namespace MyNamespace\Second {




}
?>