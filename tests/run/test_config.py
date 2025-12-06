#!/usr/bin/env python3

import unittest
from unittest import mock

from tests.run.init_test import TEST_CONFIG


class TestConfig(unittest.TestCase):

	@mock.patch("sys.argv", new=["", "--debug", "--temp_dir", "ted"])
	def test_set_config(self):
		print(TEST_CONFIG)
		TEST_CONFIG.set_config()
		print(TEST_CONFIG)

	@classmethod
	def tearDownClass(cls):
		TEST_CONFIG.reset_config()
		print(TEST_CONFIG)


if __name__ == '__main__':
	unittest.main()
