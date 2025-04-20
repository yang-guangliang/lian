#!/usr/bin/env python3

import os,sys
import unittest
from io import BytesIO
import pandas as pd
import networkx as nx

import config

from lian.semantic.internal import common_structure

class TestSearchGraph(unittest.TestCase):
    def setUp(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(11, 1)
        graph.add_edge(12, 1)
        graph.add_edge(1, 2)
        graph.add_edge(21, 2)
        graph.add_edge(22, 2)
        graph.add_edge(211, 21)
        graph.add_edge(212, 21)
        graph.add_edge(2, 3)

        # 3 -> 2 -> 21 -> 211
        #              -> 212
        #        -> 22
        #        -> 1  -> 11
        #              -> 12

        self.result = {
            1: False,
            11: [11],
            12: [12],
            2: False,
            21: False,
            211: True,
            212: True,
            22: None,
            3: None,
        }

        self.graph = graph

    def test_backward_search(self):
        result = self.result
        class Test:
            def test(self, node):
                nonlocal result
                return result.get(node)

        search = common_structure.GraphTraversal(self.graph)
        self.assertEqual(search.backward_search(3, Test().test), {11, 12, 211, 212})

    def test_pre_process_graph(self):
        


if __name__ == '__main__':
    unittest.main()
