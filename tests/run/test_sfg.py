#!/usr/bin/env python3

import os
import tempfile
import unittest
import pandas as pd
import numpy as np

from collections import defaultdict
from unittest.mock import patch

import tests.run.init_test as init_test
from lian.main import Lian

class sfgTestCase(unittest.TestCase):
    @classmethod
    def compare_sfg(cls, symbols_states: pd.DataFrame, stmt_status: pd.DataFrame, target_file: str):
        st_cols = ["stmt_id", "symbol_or_state", "name", "states", "data_type", "value", "fields"]
        ss_cols = ["stmt_id", "defined_symbol", "used_symbols", "field"]

        for col in st_cols:
            if col in symbols_states.columns:
                symbols_states[col] = symbols_states[col].apply(lambda x: str(x) if isinstance(x, (list, np.ndarray, dict)) else x)
        
        for col in ss_cols:
            if col in stmt_status.columns:
                stmt_status[col] = stmt_status[col].apply(lambda x: str(x) if isinstance(x, (list, np.ndarray, dict)) else x)

        curr_symbols = symbols_states[st_cols].sort_values(by=st_cols).reset_index(drop=True)
        curr_status = stmt_status[ss_cols].sort_values(by=ss_cols).reset_index(drop=True)

        target_base = os.path.basename(target_file)
        
        standard_dir = os.path.join(init_test.TEST_DIR, "state_flows", "standard_results")
        os.makedirs(standard_dir, exist_ok=True)
        
        symbols_ref_path = os.path.join(standard_dir, f"{target_base}.symbols.feather")
        status_ref_path = os.path.join(standard_dir, f"{target_base}.status.feather")

        update_golden = os.environ.get("UPDATE_GOLDEN") == "1"

        if update_golden or not os.path.exists(symbols_ref_path) or not os.path.exists(status_ref_path):
            print(f"Generating/Updating Golden CFG for {target_base}...")
            curr_symbols.to_feather(symbols_ref_path)
            curr_status.to_feather(status_ref_path)
        else:
            ref_symbols = pd.read_feather(symbols_ref_path)
            ref_status = pd.read_feather(status_ref_path)

            pd.testing.assert_frame_equal(
                ref_symbols, curr_symbols, 
                obj=f"{target_base} symbols_states", 
                check_dtype=False
            )
            pd.testing.assert_frame_equal(
                ref_status, curr_status, 
                obj=f"{target_base} stmt_status", 
                check_dtype=False
            )

    @classmethod
    def setUpClass(cls):
        def get_all_tests(root_dir: str):
            tests = defaultdict(list)
            for dirpath, dirnames, filenames in os.walk(root_dir):
                if os.path.basename(dirpath) == "standard_results":
                    continue
                for file in filenames:
                    if file.endswith((".py", ".java", ".c", ".js")):
                        tests[os.path.basename(dirpath)].append(os.path.realpath(os.path.join(dirpath, file)))
            return tests

        cls.tests = get_all_tests(os.path.join(init_test.TEST_DIR, "state_flows"))
        os.system("mkdir -p " + init_test.TMP_DIR)
        cls.out_dir = tempfile.TemporaryDirectory(dir=init_test.TMP_DIR)

    @classmethod
    def raw_test(cls):
        Lian().run()

    def test_run_all(self):
        os.system('clear')
        for test, files in self.tests.items():
            for target_file in files:
                file_name, _ = os.path.splitext(os.path.basename(target_file))
                print()
                print("\n","=*"*30, file_name, "=*"*30)
                patched_testcase = patch(
                            'sys.argv',
                            ["", "run", "-d", "-f", "-l", "python,java,c", target_file, "-w", init_test.OUTPUT_DIR]
                        )(
                            self.raw_test
                        )
                patched_testcase()
                
                symbols_states_path = os.path.join(init_test.OUTPUT_DIR, "semantic_p1/s2space_p1.bundle0")
                stmt_status_path = os.path.join(init_test.OUTPUT_DIR, "semantic_p1/stmt_status_p1.bundle0")
                
                if not os.path.exists(symbols_states_path) or not os.path.exists(stmt_status_path):
                    print(f"[SKIP] No generated feather outputs for {file_name}")
                    continue
                
                symbols_states = pd.read_feather(symbols_states_path)
                stmt_status = pd.read_feather(stmt_status_path)
                
                self.compare_sfg(symbols_states, stmt_status, file_name)

if __name__ == '__main__':
    unittest.main()
