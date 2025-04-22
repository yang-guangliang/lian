<?php

trait Loggable {
    public function log(string $message): void {
        echo "Logging: $message\n";
    }
}

enum LogLevel: string {
    use Loggable;  // 使用特质

    case DEBUG;
    case INFO = 'info';
    case WARNING = 'warning';
    case ERROR = 'error';
    case CRITICAL = 'critical';

    public function describe(): string {
        $this->log("Current log level is {$this->value}");
        return "LogLevel: {$this->value}";
    }
}

$logLevel = LogLevel::INFO;
echo $logLevel->describe();

// enum MyExceptionCase {
//     case InvalidMethod;
//     case InvalidProperty;
//     case Timeout;
// }

// class MyException extends Exception {
//     function __construct(private MyExceptionCase $case){
//         match($case){
//             MyExceptionCase::InvalidMethod      =>    parent::__construct("Bad Request - Invalid Method", 400),
//             MyExceptionCase::InvalidProperty    =>    parent::__construct("Bad Request - Invalid Property", 400),
//             MyExceptionCase::Timeout            =>    parent::__construct("Bad Request - Timeout", 400)
//         };
//     }
// }

// // Testing my custom exception class
// try {
//     throw new MyException(MyExceptionCase::InvalidMethod);
// } catch (MyException $myE) {
//     echo $myE->getMessage();  // Bad Request - Invalid Method
// }
?>