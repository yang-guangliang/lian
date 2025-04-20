#! /bin/sh

cd $(dirname $0)/

echo `pwd`

for test in  "test_util_dataframe.py" "test_cfg.py" "test_sdg.py"
do
    echo
    echo "[!]" $test
    echo
    
    python $test || exit
done
