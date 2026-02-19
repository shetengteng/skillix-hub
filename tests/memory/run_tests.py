#!/usr/bin/env python3
"""Standalone 测试统一执行器：扫描 unit/integration/e2e 子目录。"""
from __future__ import annotations

import datetime as dt
import importlib
import sys
import time
import unittest
from collections import defaultdict
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR / "src"
REPORTS_DIR = THIS_DIR / "reports"
SUB_DIRS = ("unit", "integration", "e2e")

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class ProgressResult(unittest.TextTestResult):
    """带进度打印和成功记录的 TestResult。"""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.successes = []
        self._test_start = None
        self._counter = 0
        self._total = 0

    def set_total(self, total: int):
        self._total = total

    def startTest(self, test):
        super().startTest(test)
        self._counter += 1
        self._test_start = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)
        elapsed = time.time() - self._test_start
        self.stream.write(f"  [{self._counter}/{self._total}] OK   {test.id()} ({elapsed:.2f}s)\n")
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.time() - self._test_start
        self.stream.write(f"  [{self._counter}/{self._total}] FAIL {test.id()} ({elapsed:.2f}s)\n")
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.time() - self._test_start
        self.stream.write(f"  [{self._counter}/{self._total}] ERR  {test.id()} ({elapsed:.2f}s)\n")
        self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.write(f"  [{self._counter}/{self._total}] SKIP {test.id()} ({reason})\n")
        self.stream.flush()


class ProgressRunner(unittest.TextTestRunner):
    resultclass = ProgressResult

    def run(self, test):
        result = self._makeResult()
        total = test.countTestCases()
        result.set_total(total)
        result.stream = self.stream
        self.stream.write(f"\n{'='*60}\n")
        self.stream.write(f"  Running {total} tests\n")
        self.stream.write(f"{'='*60}\n\n")
        test(result)
        return result


def _next_report_path() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now().strftime("%Y-%m-%d")
    max_seq = 0
    for p in REPORTS_DIR.glob(f"{today}-*.md"):
        parts = p.stem.split("-")
        if len(parts) < 4:
            continue
        try:
            seq = int(parts[3])
        except ValueError:
            continue
        max_seq = max(max_seq, seq)
    return REPORTS_DIR / f"{today}-{max_seq + 1:02d}-standalone-tests.md"


def _build_suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for subdir in SUB_DIRS:
        sub_path = SRC_DIR / subdir
        if not sub_path.is_dir():
            continue
        if str(sub_path) not in sys.path:
            sys.path.insert(0, str(sub_path))
        for path in sorted(sub_path.glob("test_*.py")):
            module = importlib.import_module(path.stem)
            suite.addTests(loader.loadTestsFromModule(module))

    return suite


def _rows(result: ProgressResult):
    rows = []
    for t in result.successes:
        rows.append((t.id(), "PASS", ""))
    for t, tb in result.failures:
        rows.append((t.id(), "FAIL", tb))
    for t, tb in result.errors:
        rows.append((t.id(), "ERROR", tb))
    for t, reason in result.skipped:
        rows.append((t.id(), "SKIP", reason))
    rows.sort(key=lambda x: x[0])
    return rows


def _build_markdown(result: ProgressResult, elapsed: float) -> str:
    rows = _rows(result)
    by_category = defaultdict(lambda: defaultdict(list))
    for test_id, state, detail in rows:
        module = test_id.split(".", 1)[0]
        case = test_id.rsplit(".", 1)[-1]
        category = _module_category(module)
        by_category[category][module].append((case, state, detail))

    failed = len(result.failures)
    errored = len(result.errors)
    status = "PASSED" if result.wasSuccessful() else "FAILED"

    lines = []
    lines.append("# Standalone Memory Skill 测试报告")
    lines.append("")
    lines.append(f"> 时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 结果: {status}")
    lines.append(f"> 耗时: {elapsed:.3f}s")
    lines.append("")

    lines.append("## 汇总")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---:|")
    lines.append(f"| 总用例 | {result.testsRun} |")
    lines.append(f"| 通过 | {len(result.successes)} |")
    lines.append(f"| 失败 | {failed} |")
    lines.append(f"| 错误 | {errored} |")
    lines.append(f"| 跳过 | {len(result.skipped)} |")
    lines.append("")

    category_labels = {"unit": "单元测试", "integration": "集成测试", "e2e": "端到端测试"}
    for cat in ("unit", "integration", "e2e"):
        if cat not in by_category:
            continue
        lines.append(f"## {category_labels.get(cat, cat)}")
        lines.append("")
        for module in sorted(by_category[cat]):
            lines.append(f"### {module}")
            lines.append("")
            lines.append("| 用例 | 状态 |")
            lines.append("|---|---|")
            for case, state, _ in by_category[cat][module]:
                lines.append(f"| `{case}` | {state} |")
            lines.append("")

    if failed or errored:
        lines.append("## 失败详情")
        lines.append("")
        for test_id, state, detail in rows:
            if state not in ("FAIL", "ERROR"):
                continue
            lines.append(f"### {state}: `{test_id}`")
            lines.append("")
            lines.append("```text")
            lines.append(detail.rstrip())
            lines.append("```")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


_MODULE_CATEGORY_MAP = {}


def _module_category(module_name: str) -> str:
    if module_name in _MODULE_CATEGORY_MAP:
        return _MODULE_CATEGORY_MAP[module_name]
    for subdir in SUB_DIRS:
        sub_path = SRC_DIR / subdir
        if (sub_path / f"{module_name}.py").exists():
            _MODULE_CATEGORY_MAP[module_name] = subdir
            return subdir
    return "other"


def main():
    start = dt.datetime.now()
    suite = _build_suite()
    runner = ProgressRunner(stream=sys.stderr, verbosity=0)
    result = runner.run(suite)

    elapsed = (dt.datetime.now() - start).total_seconds()

    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write(f"  {result.testsRun} tests | "
                     f"{len(result.successes)} passed | "
                     f"{len(result.failures)} failed | "
                     f"{len(result.errors)} errors | "
                     f"{len(result.skipped)} skipped | "
                     f"{elapsed:.1f}s\n")
    sys.stderr.write(f"{'='*60}\n")

    report = _build_markdown(result, elapsed)
    report_path = _next_report_path()
    report_path.write_text(report, encoding="utf-8")
    print(f"\nMarkdown report: {report_path}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
