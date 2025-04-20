<?php

echo "Outside declare block:\n";
echo 1 + '1';  // 输出 2，因为 PHP 会尝试转换为整数

declare (strict_types=1) {
    echo "Inside declare block:\n";
    echo 1 + '1';  // 将抛出 TypeError，因为严格类型检查开启
}

echo "\nAfter declare block:\n";
echo 1 + '1';  // 再次输出 2
?>