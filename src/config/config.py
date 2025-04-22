import os

ROOT_DIR = os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
LIAN_DIR = os.path.join(ROOT_DIR, "lian/src")
ANALYZER_DIR = os.path.join(ROOT_DIR, "src")

DEFAULT_WORKSPACE       = os.path.join(ROOT_DIR, "test/abc_workspace")
LANG_NAME               = "abc"
LANG_EXTENSION          = [".txt"]
LANG_SO_PATH            = os.path.join(ANALYZER_DIR, "frontend/abc_lang_linux.so")
OUT_DIR                 = "out"


LRU_CACHE_CAPACITY      = 10000
BUNDLE_CACHE_CAPACITY   = 10

LANG_NAME="abc"
LANG_SO_PATH= ""
LANG_EXTENSION=".txt"