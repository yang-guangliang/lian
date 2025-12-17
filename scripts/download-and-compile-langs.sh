#! /bin/sh

pip uninstall tree-sitter
pip install tree-sitter==0.21.3

# rm -rf tree-sitter-langs
cd "$(dirname "$0")"
mkdir tree-sitter-langs
cd tree-sitter-langs

download(){
    echo "Downloading the grammar files of $1"
    git clone --depth=1 $2
    echo
}


download c              git@github.com:tree-sitter/tree-sitter-c.git
download cpp            git@github.com:tree-sitter/tree-sitter-cpp.git
download c#             git@github.com:tree-sitter/tree-sitter-c-sharp.git
download rust           git@github.com:tree-sitter/tree-sitter-rust.git
download go             git@github.com:tree-sitter/tree-sitter-go.git
download java           git@github.com:tree-sitter/tree-sitter-java.git
download javascript     git@github.com:tree-sitter/tree-sitter-javascript.git
download typescript     git@github.com:tree-sitter/tree-sitter-typescript.git
download kotlin         git@github.com:fwcd/tree-sitter-kotlin.git
download scala          git@github.com:tree-sitter/tree-sitter-scala.git
download llvm           git@github.com:benwilliamgraham/tree-sitter-llvm.git
download python         git@github.com:tree-sitter/tree-sitter-python.git
download ruby           git@github.com:tree-sitter/tree-sitter-ruby.git
download smali          git@github.com:amaanq/tree-sitter-smali.git
download swift          git@github.com:alex-pinkus/tree-sitter-swift.git
download php            git@github.com:tree-sitter/tree-sitter-php.git

cd tree-sitter-swift
tree-sitter generate

cd ..

cd tree-sitter-php/php
tree-sitter generate

cd ../..

cd ..

python3 compile_langs.py

#pip install tree-sitter

sh ./extract.grammar.js.sh