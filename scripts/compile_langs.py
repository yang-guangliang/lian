#!/usr/bin/python3

import os,re

from tree_sitter import Language, Parser
from pathlib import Path

LANGS_PATH = "tree-sitter-langs"
SO_PATH = "./langs_linux.so"

os.system("mkdir -p %s" % os.path.dirname(SO_PATH))
os.system("rm -f %s" % SO_PATH)

def obtain_lang_paths():
    ret_list = []
    langs_path = Path(LANGS_PATH).glob('tree-sitter-*')
    for possible_path in langs_path:
        possible_path = str(possible_path)
        if "typescript" in possible_path:
            possible_path = possible_path + "/typescript"
        if "php" in possible_path:
            possible_path = possible_path + "/php"

        ret_list.append(possible_path)
    return ret_list

print("Building tree sitter grammar files...")
Language.build_library(SO_PATH, obtain_lang_paths())

Language(SO_PATH, 'go')
Language(SO_PATH, 'java')
Language(SO_PATH, 'rust')
Language(SO_PATH, 'cpp')
Language(SO_PATH, 'javascript')
Language(SO_PATH, 'python')
Language(SO_PATH, 'php')
Language(SO_PATH, 'swift')

print("Successfully tested: %s" % SO_PATH)
