<!-- <?php
function divide($dividend, $divisor) {
    if ($divisor == 0) {
        throw new Exception("Division by zero");
    }
    return $dividend / $divisor;
}

try {
    echo divide(10, 2);  // 正常情况下输出 5
    echo divide(10, 0);  // 这行会抛出异常
} catch (Exception $e) {
    // 当异常发生时，这段代码将被执行
    echo "Caught exception: " . $e->getMessage();
} finally {
    // 这段代码无论是否发生异常都会执行
    echo " - Done.";
}
?>

<?php
$numbers = [1, 2, 3, 4, 5];

foreach ($numbers as $number) {
    if ($number == 3) {
        continue; // 跳过当前迭代
    }
    echo $number . "\n";
}
?> -->
