#! /bin/sh

ROOT_DIR=$(realpath $0)
ROOT_DIR=$(dirname $ROOT_DIR)
ROOT_DIR=$(dirname $ROOT_DIR)

# TARGET_PATH=$(realpath "$1")

#CMD="python -W ignore"s
CMD="python3 $ROOT_DIR/src/lian/interfaces/main.py"
OPTIONS="run --lang python --incremental"

if [ $# -eq 0 ]; then
    $CMD $OPTIONS --help
    exit 1
fi

$CMD $OPTIONS $@


