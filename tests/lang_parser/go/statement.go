//comment
//`go_statement`: 这个语句用于启动一个新的并发执行线程（goroutine）。
go myFunction(a)
//defer_statement`: 这个语句用于延迟（defer）函数的执行，通常在函数结束时执行。
defer cleanup()
//if_statement
if x > 10 {
    fmt.Println("x is greater than 10")
} else {
    fmt.Println("x is less than or equal to 10")
}
// //for_statement
// for i := 0; i < 5; i++ { fmt.Println(i) }


// //expression_switch_statement`: 用于基于表达式的值进行多路分支选择。

// switch x {
// case 1:
// 	fmt.Println("x is 1")
// case 2:
// 	fmt.Println("x is 2")
// default:
// 	fmt.Println("x is neither 1 nor 2")
// }
// //type_switch_statement`: 类型开关语句，用于基于接口变量的动态类型进行分支选择。

// switch value.(type) {
// case int:
// 	fmt.Println("value is an int")
// case string:
// 	fmt.Println("value is a string")
// default:
// 	fmt.Println("value is of unknown type")
// }
// //select_statement`: 用于处理多个通道操作，选择其中一个可用的操作执行。

// select {
// case msg1 := <-channel1:
// 	fmt.Println("Received message from channel 1:", msg1)
// case msg2 := <-channel2:
// 	fmt.Println("Received message from channel 2:", msg2)
// default:
// 	fmt.Println("No messages received")
// }