# 程序语义基础 Fundamentals of Program Semantics

## 1. 词法单元 Token

在编译器分析的第一阶段，输入是字符串形式的源代码，经过词法分析器（Lexical Analyzer）的扫描（Scan）后，输出为词法单元或记号（Token）的序列。也就是说字符串流被分割成一个个token。Token主要包括两部分，一部分是分割出的内容，也叫词位（Lexeme），一部分是该内容的类别，因此一个Token可以表示为：(Lexeme, Type)。

以下列源代码为例：

```c
int main() {
    char* str = "Hello World!\n";
    print(str);
}
```


## 1. 抽象语法树 AST (Abstract Syntax Tree)

抽象语法树（AST）是程序源代码的抽象表示，是程序语义分析的基础。它是一种树形结构，它是由一系列的节点组成的，这些节点表示源代码中的各种元素，如变量、函数、运算符、表达式等等。

