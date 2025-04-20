<?php
namespace MyNamespace\First {

    const MY_CONST_FIRST = 'This is a constant in the first namespace.';

    function myFunctionFirst() {
        echo "Hello from function in namespace MyNamespace\\First\n";
    }

    class MyClassFirst {
        public function hello() {
            echo "Hello from namespace MyNamespace\\First\n";
        }

        public function useFunctionAndConst() {
            echo myFunctionFirst() . " and const: " . MY_CONST_FIRST . "\n";
        }
    }

    // 创建对象并调用其方法
    $objFirst = new MyClassFirst();
    $objFirst->hello();
    $objFirst->useFunctionAndConst();

}

// 定义第二个命名空间
namespace MyNamespace\Second {}
?>