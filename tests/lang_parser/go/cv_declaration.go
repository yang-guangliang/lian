const Pi = 3.14159
const MaxUint = ^uint(0)
const MinInt = -1 << 31	
// 变量声明
var name string = "John"
var age int = 30
var isAdult bool = true

// 多变量声明
var x, y, z int
var a, b, c string

// 复杂类型声明
var point Point = Point{X: 10, Y: 20}
var person Person = Person{Name: "John", Age: 30}
var student Student = Student{Person: Person{Name: "John", Age: 30}, Grade: 90}

// 复杂类型初始化
var point = Point{X: 10, Y: 20}
var person = Person{Name: "John", Age: 30}
var student = Student{Person: Person{Name: "John", Age: 30}, Grade: 90}
// 1. 直接赋值
var name string = "John"
var age int = 30
var isAdult bool = true

// 2. 使用关键字 `new`
var point *Point = new(Point)
var person *Person = new(Person)

// 3. 使用类型推断
var x = 10
var y = 3.14
var z = "Hello"

// 4. 使用匿名结构体
// var point = struct {
//   X int
//   Y int
// }{X: 10, Y: 20}

// 5. 使用匿名函数
var f = func(x int) int {
  return x * x
}
var arr [10]int // 声明一个长度为 10 的整型数组
var arr2 [5]string // 声明一个长度为 5 的字符串数组
arr := [3]int{1, 2, 3} // 初始化一个长度为 3 的整型数组，元素为 1, 2, 3
arr3 := [...]int{4, 5, 6, 7, 8} // 初始化一个长度为 5 的整型数组，元素为 4, 5, 6, 7, 8
var slice []int // 声明一个空的整型切片
var slice2 []string // 声明一个空的字符串切片
slice := []int{1, 2, 3} // 初始化一个长度为 3 的整型切片，元素为 1, 2, 3
slice3 := make([]string, 5) // 初始化一个长度为 5 的字符串切片，元素为 ""
var m map[string]int // 声明一个字符串到整型的映射
var m2 map[int]string // 声明一个整型到字符串的映射
m := map[string]int{"a": 1, "b": 2} // 初始化一个字符串到整型的映射，键值对为 {"a": 1, "b": 2}
m3 := make(map[int]string) // 初始化一个整型到字符串的映射，为空
var ch chan int // 声明一个无缓冲的整型通道
var ch2 chan string // 声明一个无缓冲的字符串通道
ch := make(chan int) // 初始化一个无缓冲的整型通道
ch3 := make(chan string, 10) // 初始化一个缓冲为 10 的字符串通道