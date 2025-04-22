<?php
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

// """
// def LoggerTrait {
//     variable self
//     protected %vv0 = [];
    
//     field_write self log %vv0;

//     public function %vv1() {
//         return end($this->log);
//     }

//     field_write self getLastLoggedMessage %vv1;
//     return self
// }
// """

class User {
    use LoggerTrait;

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

// 创建一个 User 实例
$user = new User("Alice");

// 调用方法
$user->sayHello();
$user->sayGoodbye();

// 获取最后一条日志消息
$lastMessage = $user->getLastLoggedMessage();
echo "Last logged message: $lastMessage\n";

// 清除日志
$user->clearLog();

?>