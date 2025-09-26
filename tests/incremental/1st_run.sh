cd ./tests
rm -rf ./inc/*
rm -rf ./lian_workspace
cp -r ./incremental/$1/first_run/* ./inc
cd ..
./scripts/test_inc.sh ./tests/inc/
