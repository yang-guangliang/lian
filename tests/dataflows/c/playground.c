int main() {
// 初始条件判断
if (!(v11 < 0x17)) {  // 原始汇编是 less + jeqz，所以这里取反
    goto jump_label_0;
}

// if 块（条件为真时执行）
v8 = v4;
v5 = v7;
goto jump_label_1;

jump_label_0:
// else 块（条件为假时执行）
v8 = v6;
v5 = v3;

jump_label_1:
int v11 = v8;
v11 = v8;
v11 = v5;
}