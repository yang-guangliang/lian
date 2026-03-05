#! /bin/bash

cd $(dirname $0)/

TARGET=$1
UPDATE_FLAG=$2

if [ "$UPDATE_FLAG" == "--update" ] || [ "$UPDATE_FLAG" == "-u" ]; then
    export UPDATE_GOLDEN=1
    echo "[INFO] UPDATE_GOLDEN is set. Standard results will be generated/overwritten."
fi

TESTS=()

if [ "$TARGET" == "cfg" ]; then
    TESTS=("tests.run.test_cfg")
elif [ "$TARGET" == "sfg" ]; then
    TESTS=("tests.run.test_sfg")
elif [ "$TARGET" == "sdg" ]; then
    TESTS=("tests.run.test_sdg")
elif [ -z "$TARGET" ] || [ "$TARGET" == "all" ]; then
    TESTS=("tests.run.test_util_dataframe" "tests.run.test_cfg" "tests.run.test_sfg" "tests.run.test_sdg")
else
    echo "Usage: $0 [cfg|sfg|sdg|all] [--update]"
    exit 1
fi

cd ../../

for test in "${TESTS[@]}"
do
    echo
    echo "[!] Running: $test"
    echo
    
    python3 -m unittest $test || { echo "Test $test failed"; exit 1; }
done
