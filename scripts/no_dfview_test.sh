#! /bin/sh

clear

if [ $# -eq 0 ]; then
    echo "$0 <path>"
    exit 1
fi


ROOT_DIR=$(realpath $0)
ROOT_DIR=$(dirname $ROOT_DIR)
ROOT_DIR=$(dirname $ROOT_DIR)

# TARGET_PATH=$(realpath "$1")

# rm unknown_callees.txt
rm $ROOT_DIR/unknown_callees.txt

#CMD="python -W ignore"s
CMD="python $ROOT_DIR/src/lian/main.py"
OUTPUT_PATH="$ROOT_DIR/tests/lian_workspace"
# OPTIONS="run -f -p -d -l python,java,c -w $OUTPUT_PATH"
OPTIONS="run  -f -d -l python -w $OUTPUT_PATH"

# echo $CMD $OPTIONS $TARGET_PATH
# $CMD $OPTIONS $TARGET_PATH
$CMD $OPTIONS $@

