#!/usr/bin/env python3

import os
import tempfile
import unittest
from collections import defaultdict
from unittest.mock import patch

import config
from lian.interfaces.main import Lian


class ParserTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        def get_all_tests(root_dir: str):
            tests = defaultdict(list)
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for file in filenames:
                    tests[os.path.basename(dirpath)].append(os.path.realpath(os.path.join(dirpath, file)))
            return tests

        cls.tests = get_all_tests(os.path.join(config.RESOURCE_DIR, "lang_parser"))
        # cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR, delete=False)
        os.system("mkdir -p " + config.TMP_DIR)
        cls.out_dir = tempfile.TemporaryDirectory(dir=config.TMP_DIR)

    def test_sample(self):
        for test, files in self.tests.items():
            print(test)

    def test_run_all(self):
        def raw_test():
            Lian().run()

        for test, files in self.tests.items():
            try:
                patched_testcase = patch('sys.argv',
                                         ["", "lang", test, files, self.out_dir.name, "-p", "-d"])(raw_test)
                patched_testcase()
            except Exception as e:
                print(f"{test} Lang Parser test failed: {e}")
                continue


if __name__ == '__main__':
    unittest.main()
