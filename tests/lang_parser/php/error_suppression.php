<?php
// 试图打开一个可能不存在的文件
$file = @fopen("nonexistentfile.txt", "r");

if ($file === false) {
    // 处理文件打开失败的情况
    echo "无法打开文件。";
} else {
    // 文件成功打开，进行后续操作
    fclose($file);
}
?>