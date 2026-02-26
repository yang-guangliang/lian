import os
import tempfile
import unittest
from collections import defaultdict
from unittest.mock import patch

import init_test

import unittest
from dataclasses import dataclass


from lian.util.gir_block import GIRBlockViewer  # 替换为你的模块路径


# --------------------------
# 测试用 IR 结构
# --------------------------

@dataclass
class DummyStmt:
    stmt_id: int
    operation: str
    value: int = 0


# --------------------------
# 构造一棵结构化 IR
# --------------------------

def build_sample_ir():
    """
    结构如下（索引标注）：

    0: block_start (id=1)
    1: add
    2: block_start (id=2)
    3: mul
    4: block_end   (id=2)
    5: sub
    6: block_end   (id=1)
    """

    return [
        DummyStmt(1, "block_start"),
        DummyStmt(10, "add", value=5),
        DummyStmt(2, "block_start"),
        DummyStmt(11, "mul", value=7),
        DummyStmt(2, "block_end"),
        DummyStmt(12, "sub", value=9),
        DummyStmt(1, "block_end"),
    ]


# --------------------------
# 测试主体
# --------------------------

class TestGIRBlock(unittest.TestCase):

    def setUp(self):
        self.GIRBlock = GIRBlockViewer
        self.ir = build_sample_ir()
        self.root = self.GIRBlock(self.ir)

    # --------------------------
    # 基础容器语义
    # --------------------------

    def test_len(self):
        # root 内部可见 stmt 为索引 0~6 之间
        # 半开区间 (-1,7)，内部 0~6
        # size = 7
        self.assertEqual(len(self.root), 7)

    def test_iteration(self):
        ops = [stmt.operation for stmt in self.root]
        self.assertEqual(
            ops,
            ["block_start", "add", "block_start",
             "mul", "block_end", "sub", "block_end"]
        )

    def test_getitem(self):
        stmt = self.root[1]
        self.assertEqual(stmt.operation, "add")

        stmt = self.root[-1]
        self.assertEqual(stmt.operation, "block_end")

        with self.assertRaises(IndexError):
            _ = self.root[100]

    def test_contains(self):
        stmt = self.root.get_stmt_by_id(11)
        self.assertTrue(stmt in self.root)

    # --------------------------
    # read_block
    # --------------------------

    def test_read_block_level1(self):
        block = self.root.read_block(1)
        self.assertIsNotNone(block)

        ops = [s.operation for s in block]
        self.assertEqual(
            ops,
            ["add", "block_start", "mul", "block_end", "sub"]
        )

    def test_read_block_nested(self):
        level1 = self.root.read_block(1)
        level2 = level1.read_block(2)

        self.assertIsNotNone(level2)

        ops = [s.operation for s in level2]
        self.assertEqual(ops, ["mul"])

    def test_read_block_visibility_violation(self):
        level1 = self.root.read_block(1)
        level2 = self.root.read_block(2)

        # root 可以直接访问 2
        self.assertIsNotNone(level2)

        # level2 不能访问 1（几何不包含）
        self.assertIsNone(level2.read_block(1))

    # --------------------------
    # get_stmt_by_id
    # --------------------------

    def test_get_stmt_by_id(self):
        stmt = self.root.get_stmt_by_id(10)
        self.assertEqual(stmt.operation, "add")

        self.assertIsNone(self.root.get_stmt_by_id(999))

    # --------------------------
    # query_operation
    # --------------------------

    def test_query_operation(self):
        adds = self.root.query_operation("add")
        self.assertEqual(len(adds), 1)
        self.assertEqual(adds[0].stmt_id, 10)

    def test_query_operation_nested_scope(self):
        level2 = self.root.read_block(2)
        muls = level2.query_operation("mul")

        self.assertEqual(len(muls), 1)
        self.assertEqual(muls[0].operation, "mul")

        # level2 中不应看到 sub
        subs = level2.query_operation("sub")
        self.assertEqual(len(subs), 0)

    # --------------------------
    # query_field
    # --------------------------

    def test_query_field(self):
        result = self.root.query_field("value", 9)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].operation, "sub")

    # --------------------------
    # 异常路径
    # --------------------------

    def test_duplicate_stmt_id(self):
        ir = [
            DummyStmt(1, "block_start"),
            DummyStmt(1, "add"),
        ]
        with self.assertRaises(RuntimeError):
            self.GIRBlock(ir)

    def test_block_mismatch(self):
        ir = [
            DummyStmt(1, "block_start"),
            DummyStmt(2, "block_end"),
        ]
        with self.assertRaises(RuntimeError):
            self.GIRBlock(ir)

    def test_unclosed_block(self):
        ir = [
            DummyStmt(1, "block_start"),
        ]
        with self.assertRaises(RuntimeError):
            self.GIRBlock(ir)


if __name__ == "__main__":
    unittest.main()
