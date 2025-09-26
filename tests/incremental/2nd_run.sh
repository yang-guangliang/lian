cd ./tests
cp ./lian_workspace/dataframe.html ./incremental
rm -rf ./inc/*
rm -rf ./lian_workspace/src/*
cp -r ./incremental/$1/second_run/* ./inc
cd ..
./scripts/test_inc.sh ./tests/inc/
cp ./tests/lian_workspace/dataframe.html ./tests/incremental/small 
