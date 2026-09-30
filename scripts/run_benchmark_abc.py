#!/usr/bin/env python3
"""ABC 字节码 benchmark 批量跑分脚本。

对 tests/abc/cases/<category>/<case>.txt 逐个执行 Lian 的 `run` 流程，
用 taint 产物判定"是否检出泄露"，并与 groundtruth 对照表比对，
输出明细 CSV 与混淆矩阵统计。

用法示例:
    python3 scripts/run_benchmark_abc.py                      # 全量顺序跑
    python3 scripts/run_benchmark_abc.py -j 4                 # 4 并发
    python3 scripts/run_benchmark_abc.py --only aliasing,icc  # 只跑部分类别
    python3 scripts/run_benchmark_abc.py -k navigation        # 用例名过滤
    python3 scripts/run_benchmark_abc.py --resume             # 断点续跑
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CASES_DIR = ROOT / "tests" / "abc" / "cases"
DEFAULT_GROUNDTRUTH = (
    ROOT / "tests" / "arkts" / "benchmark" / "复旦华为合作数据分享-benchmark类别与数量.csv"
)
DEFAULT_SETTINGS = ROOT / "benchmark_settings"
DEFAULT_OUT_DIR = ROOT / "tests" / "benchmark_results"
DEFAULT_WORKSPACE_ROOT = Path("/tmp/lian_bench_abc")

_print_lock = threading.Lock()

# 用例文件名与 groundtruth 用例名不一致的手工对齐表(按类别归一化名索引)。
# 例: abc 侧文件叫 fieldsentivity.txt(拼写笔误), 对照表里写的是 fieldsensitivity。
NAME_ALIAS = {
    "language": {"obfuscation1": "obfuscate"},
    "no_leak": {"fieldsentivity": "fieldsensitivity"},
}


def norm(text: str) -> str:
    """归一化: 小写并去掉所有非字母数字字符。"""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def load_groundtruth(path: Path):
    """解析 groundtruth 对照表。

    CSV 结构: 第1列仅在该类别首行出现(形如 `aliasing(3)`), 第2列是用例名,
    第3列是 groundtruth(√=预期有泄露, ×=预期无泄露), 第4列是 HScope 字节码结果。
    """
    records = []
    if not path.is_file():
        print(f"[WARN] 未找到 groundtruth 文件: {path}")
        return records

    category = ""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f))

    for row in rows[1:]:
        if len(row) < 3:
            continue
        raw_category, name, mark = row[0].strip(), row[1].strip(), row[2].strip()
        if not name or name == "例子":
            continue
        if raw_category:
            category = re.sub(r"[\(（].*?[\)）]\s*$", "", raw_category).strip()
        expected = 1 if mark == "√" else (0 if mark == "×" else None)
        records.append({
            "category": category,
            "category_norm": norm(category),
            "name": name,
            "name_norm": norm(name),
            "expected": expected,
            "hscope_abc": row[3].strip() if len(row) > 3 else "",
        })
    return records


def match_groundtruth(case_path: Path, records):
    """把用例文件匹配到 groundtruth 记录。

    优先 (类别, 用例名) 精确匹配, 再退化为名称包含匹配(如 `background task1short` -> `short`)。
    """
    case_cat = norm(case_path.parent.name)
    case_name = norm(case_path.stem)

    # 先按手工对齐表查找
    aliased = NAME_ALIAS.get(case_path.parent.name, {}).get(case_path.stem)
    if aliased:
        case_name = norm(aliased)

    # 类别兼容: `indirectcalls` -> `indirectcall`, `statesharing` -> `state`
    same_category = [
        r for r in records
        if r["category_norm"] and (
            r["category_norm"].startswith(case_cat) or case_cat.startswith(r["category_norm"])
        )
    ]

    for pool in (same_category, records):
        for r in pool:
            if r["name_norm"] == case_name:
                return r
        for r in pool:
            if r["name_norm"] and (
                r["name_norm"] in case_name or case_name in r["name_norm"]
            ):
                return r
    return None


def discover_cases(cases_dir: Path, only, exclude, keyword):
    cases = sorted(
        p for p in cases_dir.rglob("*.txt")
        if p.is_file() and "sourcecode" not in p.parts
    )
    if only:
        wanted = {norm(x) for x in only.split(",") if x.strip()}
        cases = [p for p in cases if norm(p.parent.name) in wanted]
    if exclude:
        unwanted = {norm(x) for x in exclude.split(",") if x.strip()}
        cases = [p for p in cases if norm(p.parent.name) not in unwanted]
    if keyword:
        cases = [p for p in cases if keyword.lower() in p.stem.lower()]
    return cases


def read_verdict(workspace: Path, log_path: Path):
    """从产物或日志中判定: 是否检出污点流。

    返回 (found, flows, note)。found 为 None 表示无法判定。
    """
    json_paths = list(workspace.rglob("taint_data_flow.json")) if workspace.is_dir() else []
    if json_paths:
        try:
            flows = len(json.loads(json_paths[0].read_text(encoding="utf-8")))
            return (1 if flows > 0 else 0), flows, "json"
        except Exception as exc:  # noqa: BLE001
            return None, None, f"json解析失败: {exc}"

    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    if "No taint flows found." in log:
        return 0, 0, "log"
    match = re.search(r"Found (\d+) taint flows?\.", log)
    if match:
        flows = int(match.group(1))
        return (1 if flows > 0 else 0), flows, "log"
    return None, None, "无判定依据"


def run_case(case_path: Path, args, record):
    name = f"{case_path.parent.name}_{case_path.stem}"
    workspace = Path(args.workspace_root) / name
    log_path = workspace.parent / f"{name}.log"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    env = None
    if args.engine == "hscope":
        hscope_bin = Path(args.hscope_bin).resolve()
        run_cwd = hscope_bin.parents[1]
        env = dict(os.environ)
        env["HSCOPE_JVM_OPTS"] = args.hscope_jvm_opts
        cmd = [str(hscope_bin), "run", "-l", "abc", "-w", str(workspace)]
        if args.extra_args:
            cmd.extend(args.extra_args.split())
        cmd.append(str(case_path.resolve()))
    else:
        run_cwd = ROOT
        cmd = [
            args.python, str(ROOT / "src" / "lian" / "main.py"), "run",
            "-l", "abc",
            "--default-settings", str(Path(args.settings).resolve()),
            "-w", str(workspace),
            "-f",
        ]
        if args.nomock:
            cmd.append("--nomock")
        if args.extra_args:
            cmd.extend(args.extra_args.split())
        cmd.append(str(case_path.resolve()))

    if not args.keep_workspace and workspace.exists():
        shutil.rmtree(workspace, ignore_errors=True)

    started = time.time()
    rc, timed_out = 0, False
    with open(log_path, "w", encoding="utf-8") as log:
        try:
            rc = subprocess.run(
                cmd, cwd=str(run_cwd), stdout=log, stderr=subprocess.STDOUT,
                timeout=args.timeout, env=env,
            ).returncode
        except subprocess.TimeoutExpired:
            rc, timed_out = -1, True
    elapsed = round(time.time() - started, 1)

    if getattr(args, "hscope_taint_in_cwd", False):
        # 6 月版(doc-code-benchmark.zip 自带)忽略 -w, 把 taint 结果写在"工程目录"的
        # taint_output/taint_data_flow.json 里, 也不打印 "Found N taint flows.",
        # 因此只能自己取回并按用例清理, 否则会污染下一个用例。
        cwd_json = Path(run_cwd) / "taint_output" / "taint_data_flow.json"
        found, flows, note = None, None, "cwd-json缺失"
        if cwd_json.is_file():
            try:
                flows_in_cwd = len(json.loads(cwd_json.read_text(encoding="utf-8")))
                found = 1 if flows_in_cwd > 0 else 0
                flows, note = flows_in_cwd, "cwd-json"
            except Exception as exc:  # noqa: BLE001
                note = f"cwd-json解析失败: {exc}"
            finally:
                cwd_json.unlink(missing_ok=True)
        else:
            # 该版本"无流"时不落盘 json, 只打印 "No taint flows found.", 回退到日志判定
            found, flows, note = read_verdict(Path("/nonexistent_workspace"), log_path)
    else:
        found, flows, note = read_verdict(workspace, log_path)

    expected = record["expected"] if record else None
    if timed_out:
        verdict = "TIMEOUT"
    elif rc != 0:
        verdict = "ERROR"
        note = f"exit code {rc}; {note}"
    elif found is None:
        verdict = "ERROR"
    elif expected is None:
        verdict = "UNKNOWN"
    elif expected == 1 and found == 1:
        verdict = "TP"
    elif expected == 1 and found == 0:
        verdict = "FN"
    elif expected == 0 and found == 1:
        verdict = "FP"
    else:
        verdict = "TN"

    result = {
        "category": case_path.parent.name,
        "case": case_path.stem,
        "case_file": str(case_path.relative_to(ROOT)) if ROOT in case_path.parents else str(case_path),
        "gt_category": record["category"] if record else "",
        "gt_name": record["name"] if record else "",
        "expected": expected,
        "hscope_abc": record["hscope_abc"] if record else "",
        "found": found,
        "flows": flows,
        "verdict": verdict,
        "rc": rc,
        "seconds": elapsed,
        "note": note,
        "workspace": str(workspace),
        "log": str(log_path),
    }
    with _print_lock:
        print(
            f"  {result['category']:<15} {result['case']:<28} "
            f"gt={'-' if expected is None else expected}  "
            f"found={'-' if found is None else found}  "
            f"flows={'-' if flows is None else flows:<3} "
            f"{verdict:<8} {elapsed:>6.1f}s",
            flush=True,
        )
    return result


def print_summary(results):
    order = ["TP", "TN", "FN", "FP", "ERROR", "TIMEOUT", "UNKNOWN"]
    counts = {k: sum(1 for r in results if r["verdict"] == k) for k in order}

    print("\n" + "=" * 78)
    print("总体结果")
    print("=" * 78)
    print(f"  用例总数: {len(results)}")
    for key in order:
        if counts[key]:
            print(f"  {key:<8}: {counts[key]}")
    evaluated = counts["TP"] + counts["TN"] + counts["FN"] + counts["FP"]
    if evaluated:
        accuracy = (counts["TP"] + counts["TN"]) / evaluated * 100
        print(f"  准确率(TP+TN / 已判定)  : {accuracy:.1f}%  ({counts['TP'] + counts['TN']}/{evaluated})")
        print(f"  检出率(TP / 预期有泄露) : ", end="")
        positives = counts["TP"] + counts["FN"]
        print(f"{counts['TP'] / positives * 100:.1f}%  ({counts['TP']}/{positives})" if positives else "n/a")

    print("\n" + "=" * 78)
    print("按类别统计")
    print("=" * 78)
    print(f"  {'category':<16} {'TP':>3} {'TN':>3} {'FN':>3} {'FP':>3} {'ERR':>4} {'未对齐':>6}")
    categories = sorted({r["category"] for r in results})
    for category in categories:
        rows = [r for r in results if r["category"] == category]
        def count(key):
            return sum(1 for r in rows if r["verdict"] == key)
        err = count("ERROR") + count("TIMEOUT")
        print(
            f"  {category:<16} {count('TP'):>3} {count('TN'):>3} "
            f"{count('FN'):>3} {count('FP'):>3} {err:>4} {count('UNKNOWN'):>6}"
        )

    unmatched = [r for r in results if r["verdict"] == "UNKNOWN"]
    if unmatched:
        print("\n" + "=" * 78)
        print("groundtruth 中无对应用例(不计入准确率, 需人工确认)")
        print("=" * 78)
        for r in unmatched:
            print(f"  {r['category']}/{r['case']}")

    problems = [r for r in results if r["verdict"] in ("FN", "FP", "ERROR", "TIMEOUT")]
    if problems:
        print("\n" + "=" * 78)
        print("待排查用例")
        print("=" * 78)
        for r in problems:
            print(f"  [{r['verdict']:<7}] {r['category']}/{r['case']}  flows={r['flows']}  {r['note']}")


def main():
    parser = argparse.ArgumentParser(description="Lian ABC 字节码 benchmark 批量跑分")
    parser.add_argument("--cases-dir", default=str(DEFAULT_CASES_DIR))
    parser.add_argument("--groundtruth", default=str(DEFAULT_GROUNDTRUTH))
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS), help="benchmark 专用规则目录")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("-j", "--jobs", type=int, default=1, help="并发数, 默认 1(顺序)")
    parser.add_argument("--timeout", type=int, default=1800, help="单用例超时秒数")
    parser.add_argument("--only", default="", help="只跑这些类别(逗号分隔)")
    parser.add_argument("--exclude", default="", help="排除这些类别(逗号分隔)")
    parser.add_argument("-k", "--keyword", default="", help="用例名关键字过滤")
    parser.add_argument("--keep-workspace", action="store_true", help="保留上次 workspace")
    parser.add_argument("--nomock", action="store_true",
                        help="禁用 mock/外部处理; 默认不禁用(ArkUI 等语义建模依赖 extern_system.init)")
    parser.add_argument("--keep-mock", action="store_true",
                        help="(已废弃) 默认即启用 mock, 保留仅为兼容旧命令")
    parser.add_argument("--engine", choices=["lian", "hscope"], default="lian",
                        help="跑分引擎: lian(默认) 或 hscope(对照参考实现)")
    parser.add_argument("--hscope-bin", default="/home/corgi/workspace/hscope/bin/hscope",
                        help="HScope 启动脚本路径")
    parser.add_argument("--hscope-jvm-opts", default="-Xmx6g",
                        help="传给 HScope 的 HSCOPE_JVM_OPTS")
    parser.add_argument("--hscope-taint-in-cwd", action="store_true",
                        help="HScope 把 taint 结果写在工程目录而非工作区时(6 月版行为)启用")
    parser.add_argument("--extra-args", default="", help="额外传给 main.py 的参数")
    parser.add_argument("--resume", action="store_true", help="跳过本次结果文件中已完成的用例")
    args = parser.parse_args()

    cases = discover_cases(Path(args.cases_dir), args.only, args.exclude, args.keyword)
    if not cases:
        print("没有发现任何用例, 请检查 --cases-dir 与 --only 等参数")
        return 1

    records = load_groundtruth(Path(args.groundtruth))
    print(f"发现用例 {len(cases)} 个; groundtruth 记录 {len(records)} 条")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = "abc_run" if args.engine == "lian" else f"{args.engine}_abc_run"
    csv_path = out_dir / f"{prefix}_{stamp}.csv"

    done_keys = set()
    if args.resume:
        for old in sorted(out_dir.glob("abc_run_*.csv")):
            with open(old, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    done_keys.add(f"{row['category']}/{row['case']}")
        if done_keys:
            print(f"断点续跑: 已完成 {len(done_keys)} 个用例")
            cases = [c for c in cases if f"{c.parent.name}/{c.stem}" not in done_keys]

    print(f"输出: {csv_path}\n" + "-" * 78)

    started = time.time()
    results = []

    def task(case_path):
        record = match_groundtruth(case_path, records)
        return run_case(case_path, args, record)

    if args.jobs > 1:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(task, cases))
    else:
        results = [task(case) for case in cases]

    total_elapsed = round(time.time() - started, 1)

    fieldnames = list(results[0].keys())
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print_summary(results)
    print(f"\n总耗时: {total_elapsed}s   明细已写入: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
