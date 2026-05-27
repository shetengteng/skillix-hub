#!/usr/bin/env python3
"""agent-workflow 统一测试入口。

用法：
    python3 tests/agent-workflow/run_tests.py
    python3 -m unittest discover -s tests/agent-workflow/unit
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent           # tests/agent-workflow
SKILL_DIR = TESTS_ROOT.parent.parent / "skills" / "agent-workflow"
for path in (SKILL_DIR, TESTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for sub in ("unit", "integration"):
        sub_dir = TESTS_ROOT / sub
        if sub_dir.exists():
            sub_suite = loader.discover(
                start_dir=str(sub_dir),
                pattern="test_*.py",
                top_level_dir=str(TESTS_ROOT),
            )
            suite.addTests(sub_suite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
