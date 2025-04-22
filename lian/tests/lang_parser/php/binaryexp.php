<?php
$x = new stdClass();
$y = $x instanceof stdClass; // true

$a = null;
$b = 5;
$c = $a ?? $b; // 结果为 5

$a = true;
$b = false;
$c = $a and $b; // 结果为 false
$d = $a || $b;  // 结果为 true

?>