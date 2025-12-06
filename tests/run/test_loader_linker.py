#!/usr/bin/env python3

import os
import tempfile
import unittest
import ast
import pandas as pd
import numpy as np
from prettytable import PrettyTable

from collections import defaultdict
from unittest.mock import patch

import tests.run.init_test as init_test
from lian.interfaces.main import Lian

class LoaderLinkerTestCase(unittest.TestCase):
    @classmethod
    def compare_LoaderLinker(cls, symbols_states, stmt_status, method_summary, target_file):
        space_path = os.path.join(init_test.RESOURCE_DIR, "method_summary", "standard_results", f"{target_file}.space")
        status_path = os.path.join(init_test.RESOURCE_DIR, "method_summary", "standard_results", f"{target_file}.status")
        summary_path = os.path.join(init_test.RESOURCE_DIR, "method_summary", "standard_results", f"{target_file}.summary")

        print("_"*60, "current symbols_states", "_"*60)
        for item in symbols_states:
            print(item)

        # with open(space_path, 'r') as file:
        #     correct_symbols_states = [ast.literal_eval(line.strip()) for line in file if line.strip()]
        # print("_"*60, "correct symbols_states", "_"*60)
        # for item in correct_symbols_states:
        #     print(item)

        print("_"*60, "current stmt_status", "_"*60)
        for item in stmt_status:
            print(item)

        # with open(status_path, 'r') as file:
        #     correct_stmt_status = [ast.literal_eval(line.strip()) for line in file if line.strip()]
        # print("_"*60, "correct stmt_status", "_"*60)
        # for item in correct_stmt_status:
        #     print(item)

        print("_"*60, "current method_summary", "_"*60)
        for item in method_summary:
            print(item)

        with open(summary_path, 'r') as file:
            correct_method_summary = [ast.literal_eval(line.strip()) for line in file if line.strip()]
        print("_"*60, "correct method_summary", "_"*60)
        for item in correct_method_summary:
            print(item)

        # assert symbols_states == correct_symbols_states
        # assert stmt_status == correct_stmt_status
        assert method_summary == correct_method_summary

    @classmethod
    def setUpClass(cls):
        def get_all_tests(root_dir: str):
            tests = defaultdict(list)
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for file in filenames:
                    tests[os.path.basename(dirpath)].append(os.path.realpath(os.path.join(dirpath, file)))
            return tests

        cls.tests = get_all_tests(os.path.join(init_test.RESOURCE_DIR, "loader"))
        # cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR, delete=False)
        os.system("mkdir -p " + init_test.TMP_DIR)
        cls.out_dir = tempfile.TemporaryDirectory(dir=init_test.TMP_DIR)

    @classmethod
    def raw_test(cls):
        Lian().parse_command()

    @classmethod
    def read_stmt_status(cls, LoaderLinker_path):
        LoaderLinker = pd.read_feather(LoaderLinker_path)
        results = []
        unit_id = LoaderLinker["unit_id"].values
        stmt_id = LoaderLinker["stmt_id"].values
        defined_symbol = LoaderLinker["defined_symbol"].values
        used_symbols = LoaderLinker["used_symbols"].values
        field = LoaderLinker["field"].values
        operation = LoaderLinker["operation"].values
        in_bits = LoaderLinker["in_bits"].values
        out_bits = LoaderLinker["out_bits"].values
        for index in range(len(LoaderLinker)):
            # results.append((unit_id[index], stmt_id[index], defined_symbol[index], used_symbols[index],
                            # field[index], operation[index], in_bits[index], out_bits[index]))
            results.append((stmt_id[index], defined_symbol[index], used_symbols[index], field[index]))
        results = sorted(results)
        table = PrettyTable()
        table.field_names = ["stmt_id", "defined_symbol", "used_symbols", "field"]
        for item in results:
            table.add_row(item)
        print("_"*60, "stmt_status_table", "_"*60)
        print(table)
        return results

    def test_run_all(self):
        os.system('clear')
        for test, files in self.tests.items():
            for target_file in files:
                file_name, _ = os.path.splitext(os.path.basename(target_file))
                if file_name == "test_loader":
                    print()
                    print("\n","=*"*30, file_name, "=*"*30)
                    patched_testcase = patch(
                                'sys.argv',
                                ["", "run", "-p", "-d", "-f", "-l", "python,java,c", target_file, "-w", init_test.OUTPUT_DIR]
                            )(
                                self.raw_test
                            )
                    patched_testcase()
                    symbols_states_path = os.path.join(init_test.OUTPUT_DIR, "semantic/glang_bundle0.symbols_states")
                    stmt_status_path = os.path.join(init_test.OUTPUT_DIR, "semantic/glang_bundle0.stmt_status")
                    method_summary_path = os.path.join(init_test.OUTPUT_DIR, "semantic/glang_bundle0.method_summary")
                    symbols_states = self.read_symbols_states(symbols_states_path)
                    stmt_status = self.read_stmt_status(stmt_status_path)
                    method_summary = self.read_method_summary(method_summary_path)
                    self.compare_LoaderLinker(symbols_states, stmt_status, method_summary, file_name)

if __name__ == '__main__':
    unittest.main()
