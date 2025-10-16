#! /bin/sh

clear

cd $(dirname $0)/..

#CMD="python -W ignore"
CMD="python"
TARGET=src/lian/main.py
OUTPUT_PATH="tests/lian_workspace"
OPTIONS="run -f -p -d -l python,java,c -w $OUTPUT_PATH"
DEFAULT_PATH="tests/testcases/lang_parser/python/import.py"

echo $CMD $TARGET $OPTIONS $DEFAULT_PATH

if [ "$#" -gt 0 ]; then
    $CMD $TARGET $OPTIONS $@
else
    $CMD $TARGET $OPTIONS $DEFAULT_PATH
fi
