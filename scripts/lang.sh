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
CMD="python $ROOT_DIR/src/lian/interfaces/main.py"
OUTPUT_PATH="$ROOT_DIR/tests/lian_workspace"
# OPTIONS="lang -f -d -l python,java,c,php,llvm,go,mir -w $OUTPUT_PATH"
OPTIONS="lang -d -f -l python,java,php,javascript -w $OUTPUT_PATH"

# echo $CMD $OPTIONS $TARGET_PATH
# $CMD $OPTIONS $TARGET_PATH
$CMD $OPTIONS $@

# if [ $? -ne 0 ]; then
#     exit 1
# fi

echo "============= Output dataframe files =============="

python $ROOT_DIR/scripts/dfview.py $OUTPUT_PATH

