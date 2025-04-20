<?php
function generateNumbersWithReturn(int $count) {
    for ($i = 0; $i < $count; $i++) {
        yield $i;
    }
    return "Done generating numbers.";
}

$generator = generateNumbersWithReturn(3);
foreach ($generator as $number) {
    echo $number . PHP_EOL; // 输出 0, 1, 2
}
?>