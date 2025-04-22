<?php
// namespace MyNamespace {
//     class MyClass {
//         public function sayHello() {
//             echo "test";
//         }
//     }
// }

// use MyNamespace\MyClass\sayHello;
// sayHello();

// use MyNamespace\MyClass;
// $obj = new MyClass(); // 使用带命名空间的完全限定名称
// $obj->sayHello();

// use MyNamespace\MyClass as Mycls, MyNamespace\Test, MyNamespace as Test;
// $cls = new Mycls();
// $cls.sayHello();

trait LoggerTrait {
    protected $log = [];

    public function logMessage($message) {
        $this->log[] = $message;
    }

    public function getLastLoggedMessage() {
        return end($this->log);
    }

    public function clearLog() {
        $this->log = [];
    }

    public function __destruct() {
        if (!empty($this->log)) {
            file_put_contents('log.txt', implode("\n", $this->log), FILE_APPEND);
        }
    }
}

class User {
    use LoggerTrait, Test;

    private $name;

    public function __construct($name) {
        $this->name = $name;
        $this->logMessage("User created: $name");
    }

    public function sayHello() {
        $this->logMessage("Hello, my name is $this->name.");
    }

    public function sayGoodbye() {
        $this->logMessage("Goodbye!");
    }
}

// namespace TestNamespace;

// class TestClass {
//     public function myMethod() {}
// }

// use TestNamespace\TestClass;

// $obj = new TestNamespace\TestClass(); // 使用带命名空间的完全限定名称
// $obj->myMethod();
?>