#!/bin/sh


mkdir -p 'grammar.js'

cp ./tree-sitter-langs/tree-sitter-php/common/define-grammar.js 				grammar.js/php.grammar.js 
cp ./tree-sitter-langs/tree-sitter-python/grammar.js 				grammar.js/python.grammar.js
cp ./tree-sitter-langs/tree-sitter-java/grammar.js 				grammar.js/java.grammar.js
cp ./tree-sitter-langs/tree-sitter-kotlin/grammar.js 				grammar.js/kotlin.grammar.js
cp ./tree-sitter-langs/tree-sitter-ruby/grammar.js 				grammar.js/ruby.grammar.js
cp ./tree-sitter-langs/tree-sitter-rust/grammar.js 				grammar.js/rust.grammar.js
cp ./tree-sitter-langs/tree-sitter-typescript/common/define-grammar.js 		grammar.js/typescript.grammar.js
cp ./tree-sitter-langs/tree-sitter-javascript/grammar.js 			grammar.js/javascript.grammar.js
cp ./tree-sitter-langs/tree-sitter-c/grammar.js 				grammar.js/c.grammar.js
cp ./tree-sitter-langs/tree-sitter-smali/grammar.js 				grammar.js/smali.grammar.js
cp ./tree-sitter-langs/tree-sitter-swift/grammar.js 				grammar.js/swift.grammar.js
cp ./tree-sitter-langs/tree-sitter-scala/grammar.js 				grammar.js/scala.grammar.js
cp ./tree-sitter-langs/tree-sitter-cpp/grammar.js 				grammar.js/cpp.grammar.js
cp ./tree-sitter-langs/tree-sitter-c-sharp/grammar.js 				grammar.js/sharp.grammar.js
cp ./tree-sitter-langs/tree-sitter-llvm/grammar.js 				grammar.js/llvm.grammar.js
cp ./tree-sitter-langs/tree-sitter-go/grammar.js 				grammar.js/go.grammar.js
cp ./tree-sitter-langs/tree-sitter-abc/grammar.js 				grammar.js/abc.grammar.js

cp -rf grammar.js ../docs/
git a ../docs/grammar.js/*.grammar.js
