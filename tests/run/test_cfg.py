#!/usr/bin/env python3

import os
import json
import unittest
import tempfile
from collections import defaultdict
from unittest.mock import patch

import pandas as pd

import init_test
from lian.main import Lian


class CFGTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.system("clear")
        cls.tests = cls._collect_tests(
            os.path.join(init_test.TEST_DIR, "control_flows")
        )

    @staticmethod
    def _collect_tests(root_dir: str):
        tests = defaultdict(list)
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                if file.endswith((".py", ".java")):
                    tests[os.path.basename(dirpath)].append(
                        os.path.realpath(os.path.join(dirpath, file))
                    )
        return tests

    @staticmethod
    def _normalize_edges(edges):
        # 去重 + 排序，保证比较稳定
        edges = list(set(tuple(e) for e in edges))
        edges.sort(key=lambda x: (x[0], x[1], x[2]))
        return edges

    @staticmethod
    def _read_cfg(cfg_path):
        cfg = pd.read_feather(cfg_path)
        edges = list(
            zip(
                cfg["src_stmt_id"].tolist(),
                cfg["dst_stmt_id"].tolist(),
                cfg["control_flow_type"].tolist(),
            )
        )
        return edges

    @staticmethod
    def _load_reference(target_file):
        ref_path = os.path.splitext(target_file)[0] + ".cfg.json"
        if not os.path.exists(ref_path):
            raise FileNotFoundError(f"Reference CFG not found: {ref_path}")

        with open(ref_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [tuple(edge) for edge in data["edges"]]

    def _run_lian(self, target_file):
        argv = [
            "",
            "semantic",
            "-f",            
            "-l",
            "python,java",
            "--nomock",
            "-w",
            init_test.OUTPUT_DIR,
            target_file
        ]

        with patch("sys.argv", argv):
            Lian().run()

    def test_run_all(self):
        for _, files in self.tests.items():
            for target_file in files:
                # 执行 Lian
                self._run_lian(target_file)

                # 默认仍读取 bundle0
                cfg_path = os.path.join(init_test.OUTPUT_DIR, "semantic_p1", "cfg.bundle0")
                self.assertTrue(
                    os.path.exists(cfg_path),
                    f"CFG output not found: {cfg_path}",
                )

                actual = self._normalize_edges(
                    self._read_cfg(cfg_path)
                )
                expected = self._normalize_edges(
                    self._load_reference(target_file)
                )

                self.assertEqual(expected, actual, f"CFG mismatch in {target_file}")


if __name__ == "__main__":
    unittest.main()
