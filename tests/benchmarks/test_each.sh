#!/bin/bash

CUR_DIR=`realpath $(dirname $0)`
DEFAULT_FILE_LIST="$CUR_DIR/file_list.txt"
RESULTS_DIR=$CUR_DIR/results
ROOT_DIR=$(dirname $(dirname $(dirname $RESULTS_DIR/)))
CMD=$ROOT_DIR/scripts/lian.sh
TIMEOUT_DURATION=20s

if [ $# -gt 0 ]; then
    FILE_LIST=$1
else
    echo -e "用法:\n\t" `basename $0` "[列表文件]\n"
    echo -e "没有指定文件，使用默认文件\t:" $DEFAULT_FILE_LIST
    FILE_LIST=$DEFAULT_FILE_LIST
fi

if [ ! -f "$FILE_LIST" ];
then
    echo -e "找不到待测试文件\t\t:" $FILE_LIST
    echo "退出"
    exit 1
fi

echo "读取测试文件列表：$FILE_LIST"
echo "测试中……"
echo

# echo "清理$RESULTS_DIR"
rm -rf $RESULTS_DIR
mkdir -p $RESULTS_DIR

for each_file in `cat "$FILE_LIST"`; do
    echo $each_file

    base_name=`basename "$each_file"`

    if [ "$base_name" = "main.py" ]; then
        base_name=`basename $(dirname "$each_file")`
    fi

    target_dir=$RESULTS_DIR/$base_name
    cat $base_name
    mkdir -p $target_dir

    timeout $TIMEOUT_DURATION $CMD "$each_file" > "$target_dir/${base_name%.*}.log"  2>&1
    cp $ROOT_DIR/tests/lian_workspace/dataframe.html $target_dir/
    cp $each_file $target_dir/
done

echo "======= 结束 =========="
grep -n "Error:" -R $RESULTS_DIR

