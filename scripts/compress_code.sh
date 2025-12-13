#!/bin/bash

# 设置错误处理
set -e

# 获取当前日期
DATE=$(date +"%Y%m%d")
TARGET_DIR="lian-v1.0.0"

echo "开始创建压缩包: $TARGET_DIR.zip"

# Step 1: 创建目标目录
ROOT_DIR=$(dirname $(realpath $(dirname $0)))
cd "$ROOT_DIR"
echo "创建目录: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Step 2: 检查文件是否存在并复制
echo "复制文件到目标目录..."

# 复制目录和文件，并检查是否存在
copy_items=(
    "default_settings"
    "lib"
    "scripts"
    "src"
    "CREDITS.txt"
    "LICENSE.txt"
    "README.md"
    "requirements.txt"
)

for item in "${copy_items[@]}"; do
    if [ -e "$item" ]; then
        echo "复制: $item"
        cp -r "$item" "$TARGET_DIR"/
    else
        echo "警告: $item 不存在，跳过"
    fi
done

# 检查是否复制了必要的文件
required_files=("$TARGET_DIR/src" "$TARGET_DIR/scripts")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "错误: 以下必要文件缺失: ${missing_files[*]}"
    exit 1
fi

# Step 3: 清理可能不需要的文件
echo "清理不必要的文件..."
find "$TARGET_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TARGET_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$TARGET_DIR" -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true

# Step 4: 创建zip压缩包
echo "创建压缩包: $TARGET_DIR.zip"
if command -v zip >/dev/null 2>&1; then
    zip -rq "$TARGET_DIR.zip" "$TARGET_DIR"
else
    echo "错误: zip命令未找到，请安装zip工具"
    exit 1
fi

rm -r "$TARGET_DIR"


# Step 6: 显示结果
echo "✅ 压缩完成!"
