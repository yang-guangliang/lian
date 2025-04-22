#!/usr/bin/env python3

import os
import unittest
from unittest.mock import patch

from config import TEST_CONFIG

from lian.interfaces.args_parser import parse_args


class ArgsParserTestCase(unittest.TestCase):

    @patch('sys.argv',
           ["", "lang", "python", os.path.realpath("../python/cases/primary_expression.py"), os.path.realpath(
	           "../../lian/output"), "-p", "-d"])
    def test_parse(self):
        parse_args()


if __name__ == '__main__':
    unittest.main()
