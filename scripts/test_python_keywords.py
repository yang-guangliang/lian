#!/usr/bin/env python3


def check_list_in_text(path, my_list):
    with open(path, 'r') as f:  
        text = f.read()

    text = text.replace("'", " ")
    text = text.replace('"', " ")
    text = text.replace(",", " ")

    flag = True
    text_parts = text.split()
    # print (text_parts)
    for item in text_parts:  
        if item in my_list:  
            print(f"The keyword {item} appears in {path}!")
            flag = False

    if flag:
        print(f"No keyword found in {path}!")
  
# 示例用法  
my_list = ["and", "del", "from", "not", "while", "as", "elif", "global", "or", "with", "assert", "else", "if", "pass", "yield", "break", "except", "import", "class", "in", "raise", "continue", "finally", "is", "return", "def", "for", "lambda", "try", "False", "None", "True", "nonlocal", "async", "def", "for", "with", "await", "match", "case", "self", "abs", "all", "any", "bin", "bool", "callable", "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "eval", "filter", "float", "format", "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow", "print", "property", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip", "__import__", "basestring", "cmp", "execfile", "file", "long", "raw_input", "reduce", "reload", "unichr", "unicode", "xrange", "apply", "buffer", "coerce", "intern", "ascii", "breakpoint", "bytearray", "bytes", "exec", "__annotations__", "__closure__", "__code__", "__defaults__", "__dict__", "__doc__", "__globals__", "__kwdefaults__", "__name__", "__module__", "__package__", "__qualname__", "__all__", "Ellipsis", "False", "None", "NotImplemented", "True", "__debug__", "copyright", "credits", "exit", "license", "quit", "ArithmeticError", "AssertionError", "AttributeError", "BaseException", "BufferError", "BytesWarning", "DeprecationWarning", "EOFError", "EnvironmentError", "Exception", "FloatingPointError", "FutureWarning", "GeneratorExit", "IOError", "ImportError", "ImportWarning", "IndentationError", "IndexError", "KeyError", "KeyboardInterrupt", "LookupError", "MemoryError", "NameError", "NotImplementedError", "OSError", "OverflowError", "PendingDeprecationWarning", "ReferenceError", "RuntimeError", "RuntimeWarning", "StopIteration", "SyntaxError", "SyntaxWarning", "SystemError", "SystemExit", "TabError", "TypeError", "UnboundLocalError", "UnicodeDecodeError", "UnicodeEncodeError", "UnicodeError", "UnicodeTranslateError", "UnicodeWarning", "UserWarning", "ValueError", "Warning", "ZeroDivisionError", "StandardError", "BlockingIOError", "BrokenPipeError", "ChildProcessError", "ConnectionAbortedError", "ConnectionError", "ConnectionRefusedError", "ConnectionResetError", "FileExistsError", "FileNotFoundError", "InterruptedError", "IsADirectoryError", "NotADirectoryError", "PermissionError", "ProcessLookupError", "RecursionError", "ResourceWarning", "StopAsyncIteration", "TimeoutError", "VMSError", "WindowsError", 'list', 'tuple', 'dict', 'str', 'int', 'float', 'bool', 'NoneType', 'type()', 'sum', 'len', 'range', 'zip', 'max', 'min', 'any', 'all', 'input', 'print', 'open']  

check_list_in_text("glang_format.txt", my_list)
check_list_in_text("symbol_table_symbols.txt", my_list)
