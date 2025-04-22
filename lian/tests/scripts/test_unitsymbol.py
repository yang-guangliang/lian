#!/usr/bin/env python3

import unittest
from io import BytesIO

import pandas as pd

import config

from lian.config.constants import SymbolType
from lian.semantic.internal.unit_symbols import UnitSymbol, PackageUnit


class TestUnitSymbol(unittest.TestCase):
	def setUp(self):
		self.a = UnitSymbol(1, 2, 3, SymbolType.UNIT, 5)

	def test_convert_to_dataframe(self):
		df = self.a.to_dataframe()
		print(df['symbol_type'])

	def test_convert_to_feather(self):
		df = self.a.to_dataframe()
		buffer = BytesIO()
		df.to_feather(buffer)
		print(buffer.getvalue())

		df = pd.read_feather(buffer)
		print(df)


class TestPackageUnit(unittest.TestCase):
	def setUp(self):
		self.a = PackageUnit(1, 2, 3, SymbolType.UNIT, 5, "test")

	def test_print(self):
		print(self.a)

	def test_convert_to_dataframe(self):
		df = self.a.to_dataframe()
		print(df)


if __name__ == '__main__':
	unittest.main()
