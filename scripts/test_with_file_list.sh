#!/bin/bash

# 检查是否提供了文件参数
if [ $# -ne 1 ]; then
    echo "Usage: $0 <file_with_paths>"
    exit 1
fi

input_file="$1"
error_log="failed_files1.log"  # 定义错误日志文件路径

# 检查输入文件是否存在
if [ ! -f "$input_file" ]; then
    echo "Error: File '$input_file' does not exist."
    exit 1
fi

# 清空或创建错误日志文件
> "$error_log"

# 逐行读取文件路径并处理
while IFS= read -r filepath || [[ -n "$filepath" ]]; do
    # 去除可能的空白字符
    filepath=$(echo "$filepath" | xargs)
    
    # 跳过空行和注释行（以#开头）
    if [[ -z "$filepath" || "$filepath" == \#* ]]; then
        continue
    fi

    echo "Processing file: $filepath"
    
    # 检查文件是否存在且是普通文件（非目录）
    if [ ! -f "$filepath" ]; then
        echo "Error: File '$filepath' does not exist or is a directory"
        echo "$filepath" >> "$error_log"
        continue
    fi

    # 检查是否是Python文件（可选）
    if [[ "$filepath" != *.py ]]; then
        echo "Warning: '$filepath' is not a .py file, processing anyway"
    fi

    # 执行test_nodfview.sh并传递文件路径作为参数
    /home/corgi/workspace/lian/lian/scripts/test_nodfview.sh "$filepath"
    
    # 检查是否执行成功
    if [ $? -ne 0 ]; then
        echo "Error: test_nodfview.sh failed for file $filepath"
        echo "$filepath" >> "$error_log"
    fi
done < "$input_file"

echo "All files processed."
echo "Failed files recorded in: $error_log"