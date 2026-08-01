#!/usr/bin/env python3
"""Compare two Lian workspaces by their decoded artifact contents."""

import argparse
import base64
import dataclasses
import datetime
import decimal
import hashlib
import json
import math
from pathlib import Path

import pyarrow as pa
import pyarrow.ipc as ipc


def _json_value(value, workspace_root=None):
    if dataclasses.is_dataclass(value):
        return _json_value(dataclasses.asdict(value), workspace_root)
    if isinstance(value, dict):
        return {
            str(key): _json_value(item, workspace_root)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_value(item, workspace_root) for item in value]
    if isinstance(value, str) and workspace_root:
        return value.replace(workspace_root, "$WORKSPACE")
    if isinstance(value, bytes):
        return {"$bytes": base64.b64encode(value).decode("ascii")}
    if isinstance(value, (datetime.date, datetime.time, decimal.Decimal)):
        return {f"${type(value).__name__}": str(value)}
    if isinstance(value, float) and not math.isfinite(value):
        return {"$float": repr(value)}
    return value


def _canonical_json(value, workspace_root=None):
    return json.dumps(
        _json_value(value, workspace_root),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _arrow_artifact(path, workspace_root):
    try:
        with pa.memory_map(str(path), "r") as source:
            table = ipc.open_file(source).read_all()
    except (pa.ArrowInvalid, OSError):
        return None

    rows = sorted(
        _canonical_json(row, workspace_root) for row in table.to_pylist()
    )
    payload = _canonical_json({"schema": str(table.schema), "rows": rows})
    return "arrow", len(rows), hashlib.sha256(payload.encode("utf8")).hexdigest()


def _json_artifact(path, workspace_root):
    try:
        value = json.loads(path.read_text(encoding="utf8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    payload = _canonical_json(value, workspace_root)
    return "json", 1, hashlib.sha256(payload.encode("utf8")).hexdigest()


def _artifact(path, workspace_root):
    arrow = _arrow_artifact(path, workspace_root)
    if arrow is not None:
        return arrow
    structured = _json_artifact(path, workspace_root)
    if structured is not None:
        return structured
    return "binary", 1, hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    workspace_root = str(root.resolve())
    return {
        path.relative_to(root).as_posix(): _artifact(path, workspace_root)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def compare(left, right):
    left_snapshot = snapshot(left)
    right_snapshot = snapshot(right)
    differences = []
    for relative_path in sorted(left_snapshot.keys() | right_snapshot.keys()):
        if relative_path not in left_snapshot:
            differences.append(f"only in right: {relative_path}")
        elif relative_path not in right_snapshot:
            differences.append(f"only in left: {relative_path}")
        elif left_snapshot[relative_path] != right_snapshot[relative_path]:
            differences.append(f"different: {relative_path}")
    return differences, len(left_snapshot)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()
    for root in (args.left, args.right):
        if not root.is_dir():
            parser.error(f"workspace directory does not exist: {root}")

    differences, artifact_count = compare(args.left, args.right)
    if differences:
        print("workspaces differ")
        for difference in differences:
            print(difference)
        return 1
    print(f"workspaces are equivalent ({artifact_count} artifacts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
