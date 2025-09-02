#!/bin/bash

# 检查是否提供了目录参数
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

target_dir="$1"
error_log="failed_files.log"  # 定义错误日志文件路径

# 检查目录是否存在
if [ ! -d "$target_dir" ]; then
    echo "Error: Directory '$target_dir' does not exist."
    exit 1
fi

# 清空或创建错误日志文件
> "$error_log"  # 清空原有内容（若需保留历史记录可删除此行）

# 遍历目录中的Python文件
find "$target_dir" -type f -name "*.py" | while read -r pyfile; do
    echo "Processing Python file: $pyfile"
    current_dir=$(pwd)
    echo "当前执行目录: $current_dir"
    
    # 执行test_nodfview.sh并传递文件路径作为参数
    /home/corgi/workspace/lian/lian/scripts/test_nodfview.sh "$pyfile"
    
    # 检查test.sh是否执行成功
    if [ $? -ne 0 ]; then
        echo "Error: test_nodfview.sh failed for file $pyfile"
        # 将失败文件路径追加到错误日志
        echo "$pyfile" >> "$error_log"
    fi
done

echo "All Python files processed."
echo "Failed files recorded in: $error_log"