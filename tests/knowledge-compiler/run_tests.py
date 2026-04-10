#!/usr/bin/env python3
"""Knowledge Compiler 测试运行器。"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UNIT_DIR = ROOT / "src" / "unit"
E2E_DIR = ROOT / "src" / "e2e"
REPORTS_DIR = ROOT / "reports"


def run_tests():
    REPORTS_DIR.mkdir(exist_ok=True)

    test_dirs = [str(UNIT_DIR)]
    if E2E_DIR.exists() and list(E2E_DIR.glob("test_*.py")):
        test_dirs.append(str(E2E_DIR))

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"] + test_dirs,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = result.stdout + result.stderr
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    total = passed + failed

    report = {
        "timestamp": timestamp,
        "total": total,
        "passed": passed,
        "failed": failed,
        "exit_code": result.returncode,
        "output": output,
    }

    report_file = REPORTS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"=== Knowledge Compiler 测试报告 ===\n")
    print(f"时间: {timestamp}")
    print(f"总计: {total} | 通过: {passed} | 失败: {failed}")
    print(f"报告: {report_file}")
    print()

    if result.returncode != 0:
        print("❌ 测试失败")
        print(output)
    else:
        print("✅ 全部通过")

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
