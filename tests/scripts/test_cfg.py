#!/usr/bin/env python3

import os
import tempfile
import unittest
import pandas as pd
import pprint
import numpy as np
from collections import defaultdict
from unittest.mock import patch

import config
from lian.interfaces.main import Lian

class CFGTestCase(unittest.TestCase):
    @classmethod
    def compare_cfg(cls, edge_list, target_file):
        file_name = os.path.basename(target_file)
        cfg_results = {
            "each.py": [
                (24, 25, 13),
                (24, 40, 12),
                (25, 26, 0),
                (26, 28, 4),
                (26, 29, 5),
                (28, 26, 0),
                (29, 40, 0),
                (30, 31, 13),
                (30, 40, 12),
                (31, 32, 0),
                (32, 34, 4),
                (32, 35, 5),
                (34, 32, 0),
                (35, 40, 0),
                (36, 37, 13),
                (36, 40, 12),
                (37, 38, 0),
                (38, 40, 0),
                (40, 41, 0),
                (41, 42, 0),
                (42, 43, 0),
                (43, 45, 4),
                (43, 63, 5),
                (45, 46, 0),
                (46, 47, 0),
                (47, 49, 1),
                (47, 51, 2),
                (49, 43, 7),
                (51, 52, 0),
                (52, 53, 0),
                (53, 55, 1),
                (53, 57, 2),
                (55, 63, 0),
                (57, 58, 0),
                (58, 59, 0),
                (59, 60, 0),
                (60, 61, 0),
                (61, 62, 0),
                (62, 43, 0),
                (63, 64, 0),
                (64, 65, 0),
                (65, 66, 0),
                (66, -1, 0)
            ],
            "while.py": [
                (12, 13, 0),
                (13, 14, 0),
                (14, 15, 0),
                (15, 17, 4),
                (15, 27, 4),
                (17, 18, 0),
                (18, 19, 0),
                (19, 20, 0),
                (20, 21, 0),
                (21, 22, 0),
                (22, 24, 1),
                (22, 25, 2),
                (24, 28, 0),
                (25, 15, 0),
                (27, 28, 0),
                (28, 29, 0),
                (29, 30, 0),
                (30, -1, 0)
            ],
            "if.py": [
                (12, 13, 0),
                (13, 14, 0),
                (14, 15, 0),
                (15, 16, 0),
                (16, 17, 0),
                (17, 18, 0),
                (18, 19, 0),
                (19, 21, 1),
                (19, 24, 2),
                (21, 22, 0),
                (22, 32, 0),
                (24, 25, 0),
                (25, 27, 1),
                (25, 30, 2),
                (27, 28, 0),
                (28, 32, 0),
                (30, 31, 0),
                (31, 32, 0),
                (32, -1, 8)
            ],
            "try.py": [
                (12, 14, 0),
                (14, 15, 0),
                (15, 16, 0),
                (16, 17, 0),
                (17, 18, 0),
                (18, 19, 0),
                (19, 20, 0),
                (20, 22, 0),
                (20, 32, 10),
                (22, 24, 9),
                (22, 25, 0),
                (24, 34, 11),
                (25, 27, 9),
                (25, 28, 0),
                (27, 34, 11),
                (28, 30, 9),
                (30, 34, 11),
                (32, 34, 11),
                (34, -1, 0)
            ]
            ,
            "decl.py": [
                (14, 16, 12),
                (16, 17, 0),
                (17, 19, 1),
                (17, 29, 2),
                (19, 21, 0),
                (21, 51, 0),
                (25, 27, 12),
                (27, -1, 0),
                (29, 30, 0),
                (30, 32, 1),
                (30, 42, 2),
                (32, 34, 0),
                (34, 51, 0),
                (38, 40, 12),
                (40, -1, 0),
                (42, 44, 0),
                (44, 51, 0),
                (48, 50, 12),
                (50, -1, 0),
                (51, 52, 0),
                (52, 54, 1),
                (52, 57, 2),
                (54, 55, 0),
                (55, 62, 0),
                (57, 58, 0),
                (58, 60, 1),
                (58, 62, 2),
                (60, 61, 0),
                (61, 62, 0),
                (62, -1, 8)
            ],
            "for.java":[
                (12, -1, 5),
                (12, 22, 4),
                (14, 15, 0),
                (15, 17, 0),
                (17, 12, 0),
                (19, 20, 0),
                (20, 17, 0),
                (22, 23, 0),
                (23, 24, 0),
                (24, 25, 0),
                (25, 27, 1),
                (25, 29, 2),
                (27, 28, 0),
                (28, -1, 0),
                (29, 30, 0),
                (30, 31, 0),
                (31, 19, 0)
            ],
            "yield.py":[
                (12, -1, 0),
                (12, 13, 0),
                (13, -1, 0),
                (13, 14, 0),
                (14, -1, 0),
                (14, 15, 0),
                (15, 16, 0),
                (16, -1, 0),
                (16, 17, 0),
                (17, 18, 0),
                (18, -1, 0),
            ],
            "list.py":[
                (12, 13, 0),
                (13, 14, 0),
                (14, 15, 0),
                (15, 16, 0),
                (16, 17, 0),
                (17, 18, 0),
                (18, 19, 0),
                (19, 20, 0),
                (20, 21, 0),
                (21, 22, 0),
                (22, 23, 0),
                (23, 24, 0),
                (24, 25, 0),
                (25, -1, 0)
            ],
            "field.py":[
                (20, 22, 12),
                (22, -1, 0),
                (29, 30, 0),
                (30, 31, 0),
                (31, 32, 0),
                (32, 33, 0),
                (33, 34, 0),
                (34, 35, 0),
                (35, 36, 0),
                (36, 37, 0),
                (37, -1, 0)
            ]

        }
        print("=== target file ===")
        print(target_file)
        result = sorted(cfg_results[file_name])
        edge_list = sorted(edge_list)
        print("+ reference answer")
        pprint.pprint(result)
        print("+ current result")
        pprint.pprint(edge_list)
        assert result == edge_list


    @classmethod
    def setUpClass(cls):
        def get_all_tests(root_dir: str):
            tests = defaultdict(list)
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for file in filenames:
                    tests[os.path.basename(dirpath)].append(os.path.realpath(os.path.join(dirpath, file)))
            return tests

        cls.tests = get_all_tests(os.path.join(config.RESOURCE_DIR, "control_flows"))
        # cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR, delete=False)
        os.system("mkdir -p " + config.TMP_DIR)
        cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR)

    @classmethod
    def raw_test(cls):
        loader = Lian().parse_command()
        return loader

    @classmethod
    def read_cfg(cls, cfg_path):
        cfg = pd.read_feather(cfg_path)
        results = []
        source_nodes = cfg["src_stmt_id"].values.tolist()
        dst_nodes = cfg["dst_stmt_id"].values.tolist()
        type_nodes = cfg["control_flow_type"].values.tolist()
        for index in range(len(cfg)):
            results.append((source_nodes[index], dst_nodes[index], type_nodes[index]))
        return results

    def test_run_all(self):
        os.system('clear')
        for test, files in self.tests.items():
            for target_file in files:
                print("*"*20, target_file, "*"*20)
                patched_testcase = patch(
                    'sys.argv',
                    ["", "run", "-f", "-d", "-l", "python,java", target_file, "-w", config.OUTPUT_DIR]
                    # ["", "run", "-f", "-l", "python,java", target_file, "-w", config.OUTPUT_DIR]
                )(
                    self.raw_test
                )
                patched_testcase()
                cfg_path = os.path.join(config.OUTPUT_DIR, "semantic/cfg.bundle0")
                cfg = self.read_cfg(cfg_path)
                self.compare_cfg(cfg, target_file)

if __name__ == '__main__':
    unittest.main()
