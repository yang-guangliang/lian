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

class symbol_graphTestCase(unittest.TestCase):
    @classmethod
    def compare_symbol_graph(cls, edge_list, target_file):
        file_name, _ = os.path.splitext(os.path.basename(target_file))
        print("="*20, file_name, "="*20)
        symbol_graph_results = {
            "each": [
                (24, 26, 'a'),
                (25, 28, '%v0'),
                (25, 29, '%v0'),
                (26, 28, 'x'),
                (28, 28, '%v0'),
                (28, 29, '%v0'),
                (30, 63, 'b'),
                (31, 34, '%v1'),
                (31, 35, '%v1'),
                (32, 34, 'y'),
                (34, 34, '%v1'),
                (34, 35, '%v1'),
                (35, 63, 'b'),
                (37, 38, '%v2'),
                (41, 63, 'a'),
                (42, 43, '%v3'),
                (43, 45, 'i'),
                (43, 51, 'i'),
                (43, 57, 'i'),
                (45, 46, '%v4'),
                (46, 47, '%v5'),
                (51, 52, '%v6'),
                (52, 53, '%v7'),
                (57, 59, '%v8'),
                (59, 60, 'a'),
                (59, 62, 'a'),
                (59, 63, 'a'),
                (62, 63, 'b'),
                (63, 65, '%v10')
            ],
            "while": [
                (13, 14, 'count'),
                (13, 17, 'count'),
                (13, 18, 'count'),
                (13, 25, 'count'),
                (13, 27, 'count'),
                (14, 15, '%v0'),
                (18, 20, '%v2'),
                (20, 21, 'x'),
                (20, 28, 'x'),
                (21, 22, '%v3'),
                (25, 17, 'count'),
                (25, 18, 'count'),
                (25, 25, 'count'),
                (25, 27, 'count'),
                (28, 30, '%v5')
            ],
            "if": [
                (13, 14, 'a'),
                (13, 17, 'a'),
                (14, 16, '%v0'),
                (16, 22, 'b'),
                (17, 18, '%v1'),
                (18, 19, '%v2'),
                (22, 32, 'x'),
                (24, 25, '%v3'),
                (28, 32, 'x'),
                (31, 32, 'x')
            ],
            "try": [(14, 15, '%v0'),
                    (15, 17, '%v1'),
                    (17, 18, 'number'),
                    (18, 20, '%v2'),
                    (20, 34, 'result'),
                    (22, 23, 'VE'),
                    (26, 27, 'VE')
            ],
            "decl": [
                (14, 16, 'vehicle_type'),
                (14, 29, 'vehicle_type'),
                (14, 51, 'vehicle_type'),
                (14, 57, 'vehicle_type'),
                (16, 17, '%v0'),
                (29, 30, '%v1'),
                (51, 52, '%v2'),
                (55, 62, '%v3'),
                (57, 58, '%v4')
            ],
            "for":[
                (15, 17, 'i'),
                (15, 19, 'i'),
                (15, 20, 'i'),
                (15, 22, 'i'),
                (20, 17, 'i'),
                (20, 19, 'i'),
                (20, 20, 'i'),
                (20, 22, 'i'),
                (22, 23, '%v2'),
                (23, 24, 'a'),
                (23, 31, 'a'),
                (24, 25, '%v3'),
                (29, 30, '%v4'),
                (30, 31, '%v5')
            ],
            "yield":[
                (15, 16, '%v0'),
                (17, 18, '%v1')
            ],
            "list":[
                (12, 13, '%v0'),
                (13, 14, '%v0'),
                (14, 15, '%v0'),
                (15, 16, '%v0'),
                (16, 18, '%v0'),
                (18, 19, 'array'),
                (19, 20, 'array'),
                (20, 21, 'array'),
                (21, 22, 'array'),
                (22, 23, 'array'),
                (23, 25, '%v1')
            ],
            "field":[
                (29, 31, '%v0'),
                (31, 32, 't'),
                (32, 33, 't'),
                (33, 34, 't'),
                (34, 36, '%v1'),
                (36, 37, 'x')
            ]
        }

        result = sorted(symbol_graph_results[file_name])
        edge_list = sorted(edge_list)
        print("="*20, "current results", "="*20)
        pprint.pprint(edge_list)
        print("="*20, "correct results", "="*20)
        pprint.pprint(result)
        assert result == edge_list

    @classmethod
    def setUpClass(cls):
        def get_all_tests(root_dir: str):
            tests = defaultdict(list)
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for file in filenames:
                    tests[os.path.basename(dirpath)].append(os.path.realpath(os.path.join(dirpath, file)))
            return tests

        cls.tests = get_all_tests(os.path.join(config.RESOURCE_DIR, "symbol_dependence"))
        # cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR, delete=False)
        os.system("mkdir -p " + config.TMP_DIR)
        cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR)

    @classmethod
    def raw_test(cls):
        loader = Lian().parse_command()
        return loader

    @classmethod
    def read_symbol_graph(cls, symbol_graph_path):
        symbol_graph = pd.read_feather(symbol_graph_path)
        results = []
        source_nodes = symbol_graph["src_stmt_id"].values
        dst_nodes = symbol_graph["dst_stmt_id"].values
        type_nodes = symbol_graph["symbol_dependency_type"].values
        for index in range(len(symbol_graph)):
            results.append((source_nodes[index], dst_nodes[index], type_nodes[index]))
        return results

    def test_run_all(self):
        for test, files in self.tests.items():
            for target_file in files:
                print("*"*20, target_file, "*"*20)
                patched_testcase = patch(
                        'sys.argv',
                        ["", "run", "-f", "-l", "python,java", target_file, "-w", config.OUTPUT_DIR]
                    )(
                        self.raw_test
                    )
                # symbol_graph_path = os.path.join(config.OUTPUT_DIR, "semantic/glang_bundle0.symbol_graph")
                # symbol_graph = self.read_symbol_graph(symbol_graph_path)
                # self.compare_symbol_graph(symbol_graph, target_file)
                loader = patched_testcase()
                all_cfgs = loader.load_all_cfg()
                edge_list = []
                for _, cfg in all_cfgs.items():
                    for u, v, data in cfg.edges(data=True):
                        edge_list.append((u, v, data['weight']))
                self.compare_cfg(edge_list, target_file)

if __name__ == '__main__':
    unittest.main()
