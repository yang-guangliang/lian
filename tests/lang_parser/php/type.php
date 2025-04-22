<?php
function concatenate(string|int $value1, string|int $value2): ?string {
    return (string)$value1 . (string)$value2;
}

echo concatenate("Hello, ", "world!"); // 输出 "Hello, world!"
echo concatenate(1, 2);               // 输出 "12"

// function count_and_iterate(Iterator&Countable $value) {
//     foreach($value as $val) {}
//     count($value);
// }
?>