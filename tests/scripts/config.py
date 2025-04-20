#!/usr/bin/env python3

import builtins
try:
    builtins.profile
except AttributeError:
    # No line profiler, provide a pass-through version
    def profile(func): return func
    builtins.profile = profile

import argparse
import dataclasses
from os import path

import pandas as pd

pd.set_option('display.max_columns', None)  # or 1000
pd.set_option('display.max_rows', None)  # or 1000
pd.set_option('display.max_colwidth', None)  # or 199

import sys,os
ROOT_PATH = os.path.realpath(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
SRC_PATH = os.path.join(ROOT_PATH, "src")
# sys.path.append(ROOT_PATH)
sys.path.append(SRC_PATH)

DEBUG = True
TEST_DIR = path.realpath(path.dirname(__file__))
TMP_DIR = path.realpath(path.join(TEST_DIR, './tmp'))
RESOURCE_DIR = path.realpath(path.join(TEST_DIR, './testcases'))
OUTPUT_DIR = path.realpath(path.join(TEST_DIR, './lian_workspace'))
OUTPUT_LLVM = os.path.join(OUTPUT_DIR, "output.ll")
