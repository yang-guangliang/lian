// main.go
package main

import (
    "fmt"
    "math"
)

// Simple function with no parameters and no return value
func printHello() {
    fmt.Println("Hello, world!")
}

// Function with two parameters and a return value
func add(x int, y int) int {
    return x + y
}

// Function demonstrating named return value
func divide(dividend float64, divisor float64) (result float64, err error) {
    if divisor == 0.0 {
        err = fmt.Errorf("cannot divide by zero")
        return
    }
    result = dividend / divisor
    return result, nil
}

// Function with variadic parameters
func sum(numbers ...int) int {
    total := 0
    for _, number := range numbers {
        total += number
    }
    return total
}

// Main function calls other functions
func main() {
    printHello()
    result := add(5, 7)
    fmt.Println("Result of add: ", result)

    quotient, err := divide(5.4, 2.0)
    if err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Println("Result of divide:", quotient)
    }

    total := sum(1, 2, 3, 4, 5)
    fmt.Println("Result of sum:", total)
}
