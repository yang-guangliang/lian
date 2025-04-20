#!/usr/bin/env python3

import unittest

import pandas as pd

import sys

import config

from lian.util import data_model as dm
from lian.util.util import SimpleEnum

class TestSimpleEnum(unittest.TestCase):
    def setUp(self):
        self.Test_A = SimpleEnum(["item1", "item2"])
        self.Test_C = SimpleEnum({"item1": "RED", "item2": "GREEN"})

    def test_value(self):
        self.assertEqual(self.Test_A.item1, 0)
        self.assertEqual(self.Test_A.item2, 1)
        self.assertEqual(self.Test_C.item1, "RED")
        self.assertEqual(self.Test_C.item2, "GREEN")

    def test_name(self):
        self.assertEqual(self.Test_A[0], 'item1')
        self.assertEqual(self.Test_A[1], 'item2')
        self.assertEqual(self.Test_C["RED"], "item1")
        self.assertEqual(self.Test_C["GREEN"], "item2")


def compare_dataframe_and_dataframeagent(df, agent):
    assert agent is not None

    original_results = []
    for row in df.itertuples():
        original_results.append(row)

    counter = 0
    for row in agent:
        assert row.operation == original_results[counter].operation
        assert row.stmt_id == original_results[counter].stmt_id
        assert row.parent_stmt_id == original_results[counter].parent_stmt_id

        counter += 1

class TestDataModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = {'operation':
                [
                    "data0", 'block_start', 'data1', 'block_end', "data2",
                    'block_start', 'block_start', 'data3', 'block_end', 'block_end'
                ] ,

                "stmt_id":
                [
                    0, 1, 2, 1, 3,
                    4, 5, 6, 5, 4
                ],
                "parent_stmt_id":
                [
                    0, 1, 2, 3, 4,
                    5, 6, 7, 8, 9
                 ]
                }
        cls.df = dm.DataModel(data)


    def test_drop(self):
        slice1 = self.df.slice(1, 9)
        print(slice1.access(1))
        assert (slice1.access(1).stmt_id == 2)
        # print(slice1._data.drop(range(2,8)))

    def test_query(self):
        res = pd.DataFrame({'operation': ['block_end', 'block_end', 'block_end'],
                            "stmt_id": [1, 5, 4],
                            "parent_stmt_id": [3, 8, 9]
                            })
        q = self.df.query(self.df.operation == "block_end").reset_index()
        compare_dataframe_and_dataframeagent(res, q)

    def test_access(self):
        row = self.df.access(4)
        self.assertEqual(row.stmt_id, 3)
        self.assertEqual(row.operation, "data2")
        self.assertEqual(row.parent_stmt_id, 4)


    def test_slice(self):
        res = pd.DataFrame({'operation': ["data0", 'block_start'],
                            "stmt_id": [0, 1],
                            "parent_stmt_id": [0, 1]
                            })
        q = self.df.slice(0, 2)._data
        self.assertTrue(q.equals(res))

    def test_read_block(self):
        data = {'operation':
                [
                    "data1",
                ] ,

                "stmt_id":
                [
                    2
                ],
                "parent_stmt_id":
                [
                    2
                ]
                }

        compare_dataframe_and_dataframeagent(pd.DataFrame(data), self.df.read_block(1))
        # self.assertTrue(self.df._block_id_collection == {1: [1, 3], 4: [5, 9], 5: [6, 8]})

        data = {'operation':
                [
                    "block_start",
                    "data3",
                    "block_end",
                ] ,

                "stmt_id":
                [
                    5,6,5
                ],
                "parent_stmt_id":
                [
                    6,7,8
                ]
                }
        compare_dataframe_and_dataframeagent(pd.DataFrame(data), self.df.read_block(4))

    # def test_access_by_stmt_id(self):
    #     row = self.df.access_by_stmt_id(4)
    #     self.assertTrue(row.get_index() == 5)
    #     self.assertTrue(row.operation == "block_start")
    #     self.assertTrue(row.stmt_id == 4)
    #     self.assertTrue(row.parent_stmt_id == 5)

    def test_df_loop(self):
        compare_dataframe_and_dataframeagent(self.df._data, self.df)


if __name__ == '__main__':
    unittest.main()
