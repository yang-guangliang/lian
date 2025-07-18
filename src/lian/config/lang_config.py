from dataclasses import dataclass
import os
from lian.config.config import LANG_SO_PATH
from lian.lang import (
    c_parser,
    csharp_parser,
    go_parser,
    java_parser,
    javascript_parser,
    python_parser,
    ruby_parser,
    php_parser,
    llvm_parser
)

@dataclass
class LangConfig:
    name     : str
    parser   : object
    extension: list     = None
    so_path  : str      = LANG_SO_PATH


LANG_TABLE = [
    LangConfig(name = "c", extension = [".c", ".h", ".i",], parser = c_parser.Parser),
    LangConfig(name = "csharp", extension = [".cs"], parser = csharp_parser.Parser),
    LangConfig(name = "go", extension = [".go"], parser = go_parser.Parser),
    LangConfig(name = "java", extension = [".java"], parser = java_parser.Parser),
    LangConfig(name = "javascript", extension = [".js"], parser = javascript_parser.Parser),
    LangConfig(name = "python", extension = [".py"], parser = python_parser.Parser),
    LangConfig(name = "php", extension = [".php"], parser = php_parser.Parser),
    LangConfig(name = "ruby", extension = [".rb"], parser = ruby_parser.Parser),
    LangConfig(name = "llvm", extension = [".ll"], parser = llvm_parser.Parser),
]

LANG_EXTENSIONS = {}
EXTENSIONS_LANG = {}

def update_lang_extensions(lang_table, lang_list):
    global LANG_EXTENSIONS
    global EXTENSIONS_LANG

    for line in lang_table:
        LANG_EXTENSIONS[line.name] = line.extension

    # Adjust the attribution of .h files
    if "c" in lang_list:
        if ".h" in LANG_EXTENSIONS.get("cpp", []):
            LANG_EXTENSIONS["cpp"].remove(".h")
    elif "cpp" in lang_list:
        if ".h" in LANG_EXTENSIONS.get("c", []):
            LANG_EXTENSIONS["c"].remove(".h")

    for lang, exts in LANG_EXTENSIONS.items():
        for each_ext in exts:
            if each_ext not in EXTENSIONS_LANG:
                EXTENSIONS_LANG[each_ext] = lang