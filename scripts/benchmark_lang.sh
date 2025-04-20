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

#CMD="python -W ignore"
OUTPUT_PATH="$ROOT_DIR/tests/lian_workspace"
CMD="time python -m kernprof -o $OUTPUT_PATH/line_profiler.lprof -lvr -u 1e-3 -z"
CMD2="$ROOT_DIR/src/lian/interfaces/main.py"
OPTIONS="lang -f -l python,java,c,php,llvm,go,mir -w $OUTPUT_PATH"

# echo $CMD $OPTIONS $TARGET_PATH
# $CMD $OPTIONS $TARGET_PATH
echo $CMD $CMD2 $OPTIONS $@
$CMD $CMD2 $OPTIONS $@

# if [ $? -ne 0 ]; then
#     exit 1
# fi
