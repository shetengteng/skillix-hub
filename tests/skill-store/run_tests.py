#!/usr/bin/env python3
"""Test runner for skill-store unit tests."""

import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
UNIT_DIR = TESTS_DIR / "src" / "unit"


def run_test_file(filepath: Path) -> tuple[bool, str, float]:
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(filepath)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(TESTS_DIR.parent.parent / "skills" / "skill-store")
    )
    elapsed = time.time() - start
    output = result.stdout + result.stderr
    return result.returncode == 0, output, elapsed


def main():
    test_files = sorted(UNIT_DIR.glob("test_*.py"))
    if not test_files:
        print("No test files found.")
        return 1

    print(f"Running {len(test_files)} test files...\n")

    total_passed = 0
    total_failed = 0
    results = []

    for tf in test_files:
        success, output, elapsed = run_test_file(tf)
        print(output)

        passed = output.count("PASS:")
        failed = output.count("FAIL:")
        total_passed += passed
        total_failed += failed
        results.append((tf.name, passed, failed, elapsed, success))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, p, f, elapsed, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}: {p} passed, {f} failed ({elapsed:.2f}s)")

    print(f"\nTotal: {total_passed} passed, {total_failed} failed")

    if total_failed > 0:
        print("\nRESULT: FAILED")
        return 1
    else:
        print("\nRESULT: PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
