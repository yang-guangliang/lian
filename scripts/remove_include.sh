#!/bin/bash

# 定义需要删除的C和C++标准库头文件关键字列表
keywords=(
    "stdio.h"
    "stdlib.h"
    "string.h"
    "math.h"
    "ctype.h"
    "time.h"
    "assert.h"
    "errno.h"
    "limits.h"
    "locale.h"
    "setjmp.h"
    "signal.h"
    "stdarg.h"
    "stddef.h"
    "stdint.h"
    "stdio_ext.h"
    "float.h"
    "iso646.h"
    "wchar.h"
    "wctype.h"
    "fenv.h"
    "inttypes.h"
    "complex.h"
    "tgmath.h"
    "stdalign.h"
    "stdatomic.h"
    "stdnoreturn.h"
    "threads.h"
    "uchar.h"
    "iostream"
    "iomanip"
    "fstream"
    "sstream"
    "cmath"
    "cstdlib"
    "cstdio"
    "cstring"
    "cctype"
    "cwchar"
    "climits"
    "cfloat"
    "cstdarg"
    "cstdbool"
    "csignal"
    "cerrno"
    "ciso646"
    "cwctype"
    "csetjmp"
    "ctime"
    "cassert"
    "cfenv"
    "cstdalign"
    "cstdint"
    "cinttypes"
    "clocale"
    "ccomplex"
    "cuchar"
    "stdexcept"
    "string"
    "vector"
    "deque"
    "list"
    "set"
    "map"
    "unordered_map"
    "unordered_set"
    "stack"
    "queue"
    "algorithm"
    "iterator"
    "numeric"
    "utility"
    "memory"
    "functional"
    "bitset"
    "locale"
    "stdexcept"
    "cassert"
    "mutex"
    "thread"
    "future"
    "condition_variable"
    "chrono"
    "random"
    "ratio"
    "complex"
    "tuple"
    "array"
    "new"
    "type_traits"
    "typeinfo"
    "initializer_list"
    "scoped_allocator"
    "system_error"
    "iosfwd"
    "ios"
    "istream"
    "ostream"
    "limits"
    "exception"
    "functional"
    "locale"
    "codecvt"
    "cstddef"
    "cstdint"
    "compare"
    "coroutine"
    "iterator"
    "memory_resource"
    "version"
    "concepts"
    "ranges"
    "span"
    "stop_token"
    "syncstream"
    "any"
    "optional"
    "variant"
)

file="$1"

if [[ ! -f "$file" ]]; then
    echo "Error: 文件不存在或路径无效。"
    exit 1
fi

extension="${file##*.}"

echo "Processing $file..."

# 临时文件用于存储修改后的内容
tmp_file=$(mktemp)

# 读取每一行，处理关键字匹配和删除
while IFS= read -r line; do
    # 跳过以 #include < 开头的行
    echo "$line" | grep -qE '^[[:space:]]*#include[[:space:]]*<' && continue
    
    # 跳过包含关键字的行
    skip_line=false
    for keyword in "${keywords[@]}"; do
        if echo "$line" | grep -qE "\<$keyword\>"; then
            skip_line=true
            break
        fi
    done

    # 如果行不包含任何关键字，则写入临时文件
    if [ "$skip_line" = false ]; then
        echo "$line" >> "$tmp_file"
    fi
done < "$file"

# 将修改后的内容覆盖写回原始文件
mv "$tmp_file" "$file"

# 根据文件类型执行不同的clang预处理
if [[ "$extension" == "c" ]]; then
    preprocessed_file="${file%.c}.i"
    clang -P -E "$file" -o "$preprocessed_file"
elif [[ "$extension" == "cpp" ]]; then
    preprocessed_file="${file%.cpp}.ii"
    clang++ -P -E "$file" -o "$preprocessed_file"
fi

echo "处理完成！"
