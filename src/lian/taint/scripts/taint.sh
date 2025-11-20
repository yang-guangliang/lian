#! /bin/sh

clear

if [ $# -eq 0 ]; then
    echo "$0 <path>"
    exit 1
fi


ROOT_DIR=$(realpath $0)
ROOT_DIR=$(dirname $ROOT_DIR)
ROOT_DIR=$(dirname $ROOT_DIR)

CMD="python $ROOT_DIR/taint_analysis.py"
OUTPUT_PATH="$ROOT_DIR/tests/taint_workspace/lian_workspace"
OPTIONS="run -f -d -l python,php,javascript,java --noextern -w $OUTPUT_PATH"

echo $CMD $OPTIONS $TARGET_PATH
# $CMD $OPTIONS $TARGET_PATH
$CMD $OPTIONS $@


echo "============="
$ROOT_DIR/lian/scripts/dfview.py $OUTPUT_PATH
