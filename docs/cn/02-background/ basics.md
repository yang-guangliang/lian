# 程序语义基础 Fundamentals of Program Semantics

## 1. 词法单元 Token

在编译器分析的第一阶段，输入是字符串形式的源代码，经过词法分析器（Lexical Analyzer）的扫描（Scan）后，输出为词法单元或记号（Token）的序列。也就是说字符串流被分割成一个个token。Token主要包括两部分，一部分是分割出的内容，也叫词位（Lexeme），一部分是该内容的类别，因此一个Token可以表示为：(Lexeme, Type)。

以下列C源代码为例：

```c
int x = 1;

int f(int y) {
    int z;
    if (y > 0) {
        z = x + y;
    } else {
        z = x - y;
    }
    return z;
}
```

当上述代码开始被lexer进行扫描时，它不会关心语义信息，例如if是控制流关键词，z会被多次赋值。相反，它只关心语法信息，如if是关键词，z、x、y 全部只是标识符（identifier，缩写为IDENT）。当空白和换行符被忽略后，最终得到以下Token序列：

```
[01] int     , KEYWORD_INT
[02] x       , IDENTIFIER
[03] =       , ASSIGN
[04] 1       , INT_LITERAL
[05] ;       , SEMICOLON

[06] int     , KEYWORD_INT
[07] f       , IDENTIFIER
[08] (       , LPAREN
[09] int     , KEYWORD_INT
[10] y       , IDENTIFIER
[11] )       , RPAREN
[12] {       , LBRACE

[13] int     , KEYWORD_INT
[14] z       , IDENTIFIER
[15] ;       , SEMICOLON

[16] if      , KEYWORD_IF
[17] (       , LPAREN
[18] y       , IDENTIFIER
[19] >       , GREATER_THAN
[20] 0       , INT_LITERAL
[21] )       , RPAREN
[22] {       , LBRACE

[23] z       , IDENTIFIER
[24] =       , ASSIGN
[25] x       , IDENTIFIER
[26] +       , PLUS
[27] y       , IDENTIFIER
[28] ;       , SEMICOLON
[29] }       , RBRACE

[30] else    , KEYWORD_ELSE
[31] {       , LBRACE
[32] z       , IDENTIFIER
[33] =       , ASSIGN
[34] x       , IDENTIFIER
[35] -       , MINUS
[36] y       , IDENTIFIER
[37] ;       , SEMICOLON
[38] }       , RBRACE

[39] return  , KEYWORD_RETURN
[40] z       , IDENTIFIER
[41] ;       , SEMICOLON

[42] }       , RBRACE
```


## 2. 抽象语法树 AST (Abstract Syntax Tree)

抽象语法树（AST）是程序源代码的抽象表示，是程序语义分析的基础。它是一种树形结构，它是由一系列的节点组成的，这些节点表示源代码中的各种元素，如变量、函数、运算符、表达式等等。

以Token序列为输入，解析器Parser会应用语法规则来生成语法解析树（Parse Tree）。语法规则由人为描述的，通常使用BNF（Backus-Naur Form，巴科斯-诺尔范式）来表示。以下语法规则例子表示了对if分支结构语法的描述，其中"xxx"表示的固有的关键字或者语法元素。该规则描述了一个if-else结构，其中Cond表示条件表达式，Then表示then块，Else表示else块，Block表示块，Stmt表示语句。

```
IfStmt ::= "if" "(" Cond ")" Then "else" Else
Cond ::= BoolExpr
Then ::= Block
Else ::= Block
Block ::= "{" Stmt* "}"
```

通过按照该规则对Token流进行自上而下的解析，将Token流转换为语法解析树。不过，语法解析树非常繁琐，再通过去繁就简后，最终得到抽象语法树（AST）。上述C源代码的抽象语法树如下：

```
Global
├── VarDecl
│   ├── Type: int
│   ├── Name: x
│   └── Init
│       └── IntegerLiteral(1)
│
└── FunctionDecl
    ├── ReturnType: int
    ├── Name: f
    ├── Params
    │   └── ParamDecl
    │       ├── Type: int
    │       └── Name: y
    └── Body: CompoundStmt
        ├── VarDecl
        │   ├── Type: int
        │   └── Name: z
        │
        ├── IfStmt
        │   ├── Cond
        │   │   └── BinaryExpr (>)
        │   │       ├── Identifier(y)
        │   │       └── IntegerLiteral(0)
        │   │
        │   ├── Then
        │   │   └── CompoundStmt
        │   │       └── ExprStmt
        │   │           └── AssignExpr (=)
        │   │               ├── Identifier(z)
        │   │               └── BinaryExpr (+)
        │   │                   ├── Identifier(x)
        │   │                   └── Identifier(y)
        │   │
        │   └── Else
        │       └── CompoundStmt
        │           └── ExprStmt
        │               └── AssignExpr (=)
        │                   ├── Identifier(z)
        │                   └── BinaryExpr (-)
        │                       ├── Identifier(x)
        │                       └── Identifier(y)
        │
        └── ReturnStmt
            └── Identifier(z)

```

## 3. 作用域 Scope

作用域（Scope）是程序语义分析的基本单位，作用域描述了变量和函数的访问范围。作用域可以理解为变量和函数的命名空间，作用域内定义的变量和函数可以在作用域内被访问，而作用域外定义的变量和函数则不能被访问。实际应用中，作用域由作用域嵌套构成，作用域嵌套关系由作用域的声明顺序决定。

对于一个作用域的刻画，它不仅需要描述包含其内嵌的作用域和外层作用域，还需要完整记录本作域内定义的（或者所拥有的）变量和函数，以方便查找。

还是以之前的C源代码为例，它的作用域层级关系（Scope Hierarchy）如下：

```
GlobalScope
├── x : int
├── f : function(int) -> int
│
└── FunctionScope(f)
    ├── y : int
    │
    └── BlockScope (function body)
        ├── z : int
        ├── BlockScope (then)
        └── BlockScope (else)
```




