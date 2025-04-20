type MyInt int
type MyFloat float64
type MyString string
type IntAlias = int
type StringAlias = string
type FloatAlias = float64
type Person struct {
    Name string
    Age  int
}

type Address struct {
    Street string
    City   string
    State  string
    Zip    string
}
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
type IntArray [10]int
type StringSlice []string
type StringMap map[string]string
type IntMap map[int]int
type IntChannel chan int
type StringChannel chan string
type (
    MyInt int
    MyFloat float64
    MyString string
    Person struct {
        Name string
        Age  int
    }
    Address struct {
        Street string
        City   string
        State  string
        Zip    string
    }
    Reader interface {
        Read(p []byte) (n int, err error)
    }
    Writer interface {
        Write(p []byte) (n int, err error)
    }
    IntArray [10]int
    StringSlice []string
    StringMap map[string]string
    IntMap map[int]int
    IntChannel chan int
    StringChannel chan string
)
type Container[T any] struct {
    value T
}
type Number interface {
    ~int | ~float64
}

type Container[T Number] struct {
    value T
}
type Pair[K any, V any] struct {
    Key   K
    Value V
}
nestedSlice := [][]int{
	{1, 2, 3},
	{4, 5, 6},
	{7, 8, 9},
}
nestedMap := map[string]map[string]int{
	"A": {"X": 10, "Y": 20},
	"B": {"X": 30, "Y": 40},
}
type Contact struct {
    Email    string
    Phone    string
}

type Person struct {
    Name     string
    Age      int
    Contacts []Contact
}
person := Person{
	Name: "Alice",
	Age: 30,
	Contacts: []Contact{
		{Email: "alice@example.com", Phone: "123-456"},
		{Email: "bob@example.com", Phone: "789-012"},
	},
}
type Pair[T any, U any] struct {
    First  T
    Second U
}
pair1 := Pair[int, string]{First: 1, Second: "one"}
type Person struct {
    Name string `json:"name" xml:"name"`
    Age  int    `json:"age,omitempty"`
    Address *Address "af"
}
type Person struct {
    Name    string
    Age     int
    *Address // 嵌入指针类型
}

type ExampleInterface interface {
    Method1() string
    Method2(int) bool
    Method3(x int, y int) (int, error)
}
