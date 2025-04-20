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

import config
from lian.interfaces.main import Lian

class sfgTestCase(unittest.TestCase):
    @classmethod
    def compare_sfg(cls, symbols_states, stmt_status, target_file):
        space_path = os.path.join(config.RESOURCE_DIR, "state_flow", "standard_results", f"{target_file}.space")
        status_path = os.path.join(config.RESOURCE_DIR, "state_flow", "standard_results", f"{target_file}.status")
        
        print("_"*60, "current symbols_states", "_"*60)
        for item in symbols_states:
            print(item)
        with open(space_path, 'r') as file:
            correct_symbols_states = [ast.literal_eval(line.strip()) for line in file if line.strip()]

        print("_"*60, "current stmt_status", "_"*60)
        for item in stmt_status:
            print(item)
        with open(status_path, 'r') as file:
            correct_stmt_status = [ast.literal_eval(line.strip()) for line in file if line.strip()]

        assert symbols_states == correct_symbols_states
        assert stmt_status == correct_stmt_status

    @classmethod
    def setUpClass(cls):
        def get_all_tests(root_dir: str):
            tests = defaultdict(list)
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for file in filenames:
                    tests[os.path.basename(dirpath)].append(os.path.realpath(os.path.join(dirpath, file)))
            return tests

        cls.tests = get_all_tests(os.path.join(config.RESOURCE_DIR, "state_flow/verified_cases"))
        # cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR, delete=False)
        os.system("mkdir -p " + config.TMP_DIR)
        cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR)

    @classmethod
    def raw_test(cls):
        Lian().run()

    @classmethod
    def read_symbols_states(cls, sfg_path):
        sfg = pd.read_feather(sfg_path)
        results = []
        # unit_id = sfg["unit_id"].values
        # method_id = sfg["method_id"].values
        index_in_space = sfg["index"].values
        stmt_id = sfg["stmt_id"].values
        symbol_or_state = sfg["symbol_or_state"].values
        symbol_id = sfg["symbol_id"].values
        name = sfg["name"].values
        states = sfg["states"].values
        values = sfg["value"].values
        default_data_type = sfg["default_data_type"].values
        state_id = sfg["state_id"].values
        state_type = sfg["state_type"].values
        data_type = sfg["data_type"].values
        array = sfg["array"].values
        array_tangping_flag = sfg["array_tangping_flag"].values
        fields = sfg["fields"].values
        for index in range(len(sfg)):
            results.append((index_in_space[index],  stmt_id[index],     symbol_or_state[index],     symbol_id[index],
                            name[index],            states[index],      default_data_type[index],   state_id[index], 
                            state_type[index],      data_type[index],   values[index],              array_tangping_flag[index], 
                            array[index],           fields[index]))
        results = sorted(results)
        table = PrettyTable()
        table.field_names = ["index_in_space", "stmt_id", "symbol_or_state", 
                             "symbol_id", "name", "states", "default_data_type", 
                             "state_id", "state_type", "data_type", "values", "tpflag", "array", "fields"]
        for item in results:
            table.add_row(item)
        print("_"*60, "symbols_states_table", "_"*60)
        print(table)
        return results

    @classmethod
    def read_stmt_status(cls, sfg_path):
        sfg = pd.read_feather(sfg_path)
        results = []
        unit_id = sfg["unit_id"].values
        stmt_id = sfg["stmt_id"].values
        defined_symbol = sfg["defined_symbol"].values
        used_symbols = sfg["used_symbols"].values
        field = sfg["field"].values
        operation = sfg["operation"].values
        in_bits = sfg["in_bits"].values
        out_bits = sfg["out_bits"].values
        for index in range(len(sfg)):
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
                print()
                print("\n","=*"*30, file_name, "=*"*30)
                patched_testcase = patch(
                            'sys.argv',
                            ["", "run", "-d", "-f", "-l", "python,java,c", target_file, "-w", config.OUTPUT_DIR]
                        )(
                            self.raw_test
                        )
                patched_testcase()
                symbols_states_path = os.path.join(config.OUTPUT_DIR, "semantic/glang_bundle0.symbols_states")
                stmt_status_path = os.path.join(config.OUTPUT_DIR, "semantic/glang_bundle0.stmt_status")
                symbols_states = self.read_symbols_states(symbols_states_path)
                stmt_status = self.read_stmt_status(stmt_status_path)
                self.compare_sfg(symbols_states, stmt_status, file_name)

if __name__ == '__main__':
    unittest.main()
