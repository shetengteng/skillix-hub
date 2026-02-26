#!/usr/bin/env python3
"""Unit tests for lib/file_lock.py"""

import json
import os
import shutil
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent.parent
TESTDATA_DIR = TESTS_DIR / "testdata" / "runtime"
SKILL_DIR = TESTS_DIR.parent.parent / "skills" / "skill-store"

sys.path.insert(0, str(SKILL_DIR))

passed = 0
failed = 0


def assert_true(condition, msg):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")


def make_sandbox(label):
    sandbox = TESTDATA_DIR / f"{label}-{os.getpid()}"
    sandbox.mkdir(parents=True, exist_ok=True)
    return sandbox


def test_locked_read_json_not_exists():
    sandbox = make_sandbox("lock-read-noexist")
    try:
        from lib.file_lock import locked_read_json
        result = locked_read_json(sandbox / "missing.json", {"default": True})
        assert_true(result == {"default": True}, "locked_read_json returns default when file missing")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_locked_read_json_valid():
    sandbox = make_sandbox("lock-read-valid")
    try:
        filepath = sandbox / "data.json"
        filepath.write_text(json.dumps({"key": "val"}), encoding="utf-8")
        from lib.file_lock import locked_read_json
        result = locked_read_json(filepath, {})
        assert_true(result == {"key": "val"}, "locked_read_json returns parsed content")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_locked_write_json():
    sandbox = make_sandbox("lock-write")
    try:
        filepath = sandbox / "output.json"
        from lib.file_lock import locked_write_json
        locked_write_json(filepath, {"written": True})
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert_true(content == {"written": True}, "locked_write_json writes correct data")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_locked_update_json():
    sandbox = make_sandbox("lock-update")
    try:
        filepath = sandbox / "update.json"
        filepath.write_text(json.dumps({"count": 0}), encoding="utf-8")
        from lib.file_lock import locked_update_json

        def increment(data):
            data["count"] += 1

        locked_update_json(filepath, {"count": 0}, increment)
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert_true(content["count"] == 1, "locked_update_json applies updater function")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_locked_update_json_creates_file():
    sandbox = make_sandbox("lock-update-create")
    try:
        filepath = sandbox / "new.json"
        from lib.file_lock import locked_update_json

        def set_value(data):
            data["initialized"] = True

        locked_update_json(filepath, {"initialized": False}, set_value)
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert_true(content["initialized"] is True, "locked_update_json creates file if not exists")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_lock_file_cleanup():
    sandbox = make_sandbox("lock-cleanup")
    try:
        filepath = sandbox / "test.json"
        from lib.file_lock import file_lock
        with file_lock(filepath):
            lock_path = filepath.with_suffix(".json.lock")
            assert_true(lock_path.exists(), "lock file exists during lock")
        assert_true(not lock_path.exists(), "lock file cleaned up after release")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def main():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_file_lock.py ===")
    test_locked_read_json_not_exists()
    test_locked_read_json_valid()
    test_locked_write_json()
    test_locked_update_json()
    test_locked_update_json_creates_file()
    test_lock_file_cleanup()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main() > 0 else 0)
