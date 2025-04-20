#! /bin/sh

pip uninstall tree-sitter
pip install tree-sitter==0.21.3

cd tree-sitter-langs

for i in `ls`
do
    cd $i
    echo "Updating the grammar files of $i"
    git pull
    echo
    cd ..
done

cd ..

python3 compile_langs.py

pip install tree-sitter
