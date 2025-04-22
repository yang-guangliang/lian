<?php
function f0() {
    $x = [1, 2, 3];
    $y = 4;

    echo implode(', ', $x) . ', ' . $y . "\n"; // Output the modified array and variable
 
    $f = function($a, $b) use ($x, $y) { // Use references to modify the original variables
        // nonlocal_stmt $x;
        // nonlocal_stmt $y;
        // copy_stmt $$x = $x
        // copy_stmt $$y = $y

        // $y = %v1;

        // $$x[0] = 3; // This will modify the original array $$x
        $x[0] = 3;
        $y = 5; // This will modify the original variable $y
        echo implode(', ', $$x) . ', ' . $y . "\n"; // Output the modified array and variable
        return $a + $b;
    };
 
    $f(1, 2); // Call the function to execute the modifications
 
    echo implode(', ', $x) . ', ' . $y; // Output the modified array and variable
}

f0();


// https://dev.to/robertobutti/mastering-php-namespaces-simplifying-code-with-use-function-for-external-functions-38fb

// use function MyMath\add as myAddFunction, Another;

// 使用插件修改成如下形式
// // =>

// from MyMath import add as myAddFunction;
// import Another;

?>
