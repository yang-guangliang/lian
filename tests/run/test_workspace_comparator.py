import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pyarrow as pa
import pyarrow.ipc as ipc


class WorkspaceComparatorTest(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.comparator = self.repo_root / "scripts" / "compare_lian_workspaces.py"

    @staticmethod
    def _write_arrow(path, rows):
        table = pa.Table.from_pylist(rows)
        with pa.OSFile(str(path), "wb") as sink:
            with ipc.new_file(sink, table.schema) as writer:
                writer.write_table(table)

    def _compare(self, left, right):
        return subprocess.run(
            [sys.executable, str(self.comparator), str(left), str(right)],
            cwd=self.repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_equivalent_json_and_arrow_artifacts_compare_equal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            left = Path(tmp_dir) / "left"
            right = Path(tmp_dir) / "right"
            left.mkdir()
            right.mkdir()

            (left / "index.json").write_text(
                json.dumps({
                    "methods": [2, 1],
                    "status": "ok",
                    "workspace": str(left / "lian_workspace"),
                }),
                encoding="utf8",
            )
            (right / "index.json").write_text(
                json.dumps({
                    "status": "ok",
                    "methods": [2, 1],
                    "workspace": str(right / "lian_workspace"),
                }),
                encoding="utf8",
            )
            self._write_arrow(
                left / "summary.bundle0",
                [
                    {"index": 1, "value": str(left / "src" / "a.c")},
                    {"index": 2, "value": "b"},
                ],
            )
            self._write_arrow(
                right / "summary.bundle0",
                [
                    {"index": 2, "value": "b"},
                    {"index": 1, "value": str(right / "src" / "a.c")},
                ],
            )
            (left / "schema.txt").write_text("same\n", encoding="utf8")
            (right / "schema.txt").write_text("same\n", encoding="utf8")

            result = self._compare(left, right)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("workspaces are equivalent", result.stdout)

    def test_changed_arrow_value_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            left = Path(tmp_dir) / "left"
            right = Path(tmp_dir) / "right"
            left.mkdir()
            right.mkdir()
            self._write_arrow(left / "summary.bundle0", [{"index": 1}])
            self._write_arrow(right / "summary.bundle0", [{"index": 2}])

            result = self._compare(left, right)

            self.assertEqual(result.returncode, 1)
            self.assertIn("summary.bundle0", result.stdout)

    def test_workspace_name_prefix_in_non_path_value_is_not_normalized(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            left = Path(tmp_dir) / "left"
            right = Path(tmp_dir) / "right"
            left.mkdir()
            right.mkdir()
            (left / "index.json").write_text(
                json.dumps({"label": f"{left}-metadata"}), encoding="utf8"
            )
            (right / "index.json").write_text(
                json.dumps({"label": f"{right}-metadata"}), encoding="utf8"
            )

            result = self._compare(left, right)

            self.assertEqual(result.returncode, 1)
            self.assertIn("index.json", result.stdout)

    def test_missing_artifact_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            left = Path(tmp_dir) / "left"
            right = Path(tmp_dir) / "right"
            left.mkdir()
            right.mkdir()
            (left / "only-left.json").write_text("{}", encoding="utf8")

            result = self._compare(left, right)

            self.assertEqual(result.returncode, 1)
            self.assertIn("only-left.json", result.stdout)


if __name__ == "__main__":
    unittest.main()
