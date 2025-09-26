cd ./tests
cp ./lian_workspace/dataframe.html .
rm -rf ./inc/*
rm -rf ./lian_workspace/src/*
cp -r ./src/latest/* ./inc
cd ..
./1.sh
cp ./tests/lian_workspace/dataframe.html . 
