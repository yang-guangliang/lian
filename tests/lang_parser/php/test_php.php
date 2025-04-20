<?php

namespace Foo\Bar\subnamespace{

    function foo(){

    }
    class foo
    {
        static function staticmethod() {}
    }
    const FOO = 2;
}

namespace Foo {
    const Foooooo = 3;
    function foo() {}
    foo();
    echo Bar\subnamespace\FOO;
    // namespace_read v0 = Bar\subnamespace  FOO
}

namespace Foo_Bar {

    // include 'file1.php';
    const FOO = 2;
    function foo() {}
    class foo
    {
        static function staticmethod() {}
    }

    /* 非限定名称 */
    foo(); // 解析为函数 Foo\Bar\foo
    foo::staticmethod(); // 解析为类 Foo\Bar\foo ，方法为 staticmethod
    echo FOO; // 解析为常量 Foo\Bar\FOO

    // echo Foooooo;

    /* 限定名称 */
    // global Foo\Bar\subnamespace as v0
    // v0.foo(); // 解析为函数 Foo\Bar\subnamespace\foo
    // v0.foo.staticmethod(); // 解析为类 Foo\Bar\subnamespace\foo,
    // // 以及类的方法 staticmethod
    // echo v0\FOO; // 解析为常量 Foo\Bar\subnamespace\FOO

    // $s = foo;
    // echo (fn($func) => $func(3))($s);

    /* 完全限定名称 */

    foo(); // 解析为函数 Foo\Bar\foo
    \Foo_Bar\foo(); // 解析为函数 Foo\Bar\foo
    // v0 = namespace_read \Foo_Bar foo;
    // call_stmt v0

    \Foo_Bar\foo::staticmethod(); // 解析为类 Foo\Bar\foo, 以及类的方法 staticmethod
    // v1 = namespace_read \Foo_Bar foo;
    // field_read  v2 = foo.staticmethod();
    // call_stmt v2()
    
    $o = new foo();
    $o = new \Foo_Bar\foo();
// case1:
//     namespace_read v0 = \Foo_Bar foo;
//     $0 = new_object data_type: v0;
// case2:       
//     $o = new_object data_type: \Foo_Bar.foo();

    echo \Foo_Bar\FOO; // 解析为常量 Foo\Bar\FOO

//     ====================================;
//     namespace_read v4 = \Foo_Bar FOO;
//     echo_stmt v4

}


?>
