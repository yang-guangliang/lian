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

CMD="python $ROOT_DIR/src/analyze.py"
OUTPUT_PATH="$ROOT_DIR/test/analyzer_workspace"
OPTIONS="run -f -d  -w $OUTPUT_PATH"
echo $CMD $OPTIONS  $@ 
# $CMD $OPTIONS $TARGET_PATH
$CMD $OPTIONS $@

# if [ $? -ne 0 ]; then
#     exit 1
# fi

echo "============="
$ROOT_DIR/lian/scripts/dfview.py $OUTPUT_PATH


