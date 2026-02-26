#!/usr/bin/env python3
"""Unit tests for lib/config.py"""

import json
import os
import shutil
import sys
import tempfile
from io import StringIO
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


async def test_load_json_file_not_exists():
    sandbox = make_sandbox("load-noexist")
    try:
        from lib.config import load_json
        result = load_json(sandbox / "nonexistent.json", {"default": True})
        assert_true(result == {"default": True}, "load_json returns default when file not exists")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


async def test_load_json_corrupted():
    sandbox = make_sandbox("load-corrupt")
    try:
        filepath = sandbox / "bad.json"
        filepath.write_text("not valid json {{{", encoding="utf-8")
        from lib.config import load_json
        result = load_json(filepath, {"fallback": 42})
        assert_true(result == {"fallback": 42}, "load_json returns default on corrupted file")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


async def test_load_json_valid():
    sandbox = make_sandbox("load-valid")
    try:
        filepath = sandbox / "good.json"
        data = {"key": "value", "num": 123}
        filepath.write_text(json.dumps(data), encoding="utf-8")
        from lib.config import load_json
        result = load_json(filepath, {})
        assert_true(result == data, "load_json returns parsed content from valid file")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


async def test_save_json_creates_dir():
    sandbox = make_sandbox("save-mkdir")
    try:
        filepath = sandbox / "sub" / "deep" / "file.json"
        from lib.config import save_json
        save_json(filepath, {"created": True})
        assert_true(filepath.exists(), "save_json creates parent directories")
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert_true(content == {"created": True}, "save_json writes correct content")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


async def test_save_json_overwrite():
    sandbox = make_sandbox("save-overwrite")
    try:
        filepath = sandbox / "file.json"
        from lib.config import save_json
        save_json(filepath, {"v": 1})
        save_json(filepath, {"v": 2})
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert_true(content == {"v": 2}, "save_json overwrites existing file")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


async def test_ensure_data_dir():
    sandbox = make_sandbox("ensure-data")
    try:
        os.environ["SKILL_STORE_DATA_DIR"] = str(sandbox / "data")
        import importlib
        import lib.config as cfg
        importlib.reload(cfg)

        cfg.ensure_data_dir()
        assert_true(cfg.DATA_DIR.exists(), "ensure_data_dir creates DATA_DIR")
        assert_true(cfg.REPOS_DIR.exists(), "ensure_data_dir creates REPOS_DIR")
    finally:
        os.environ.pop("SKILL_STORE_DATA_DIR", None)
        importlib.reload(cfg)
        shutil.rmtree(sandbox, ignore_errors=True)


async def test_output_result_success():
    from lib.config import output_result
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        output_result(result={"status": "ok"})
        output = sys.stdout.getvalue()
        parsed = json.loads(output)
        assert_true(parsed["result"] == {"status": "ok"}, "output_result success has correct result")
        assert_true(parsed["error"] is None, "output_result success has null error")
    finally:
        sys.stdout = old_stdout


async def test_output_result_error():
    from lib.config import output_result
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        output_result(error="something failed")
        output = sys.stdout.getvalue()
        parsed = json.loads(output)
        assert_true(parsed["result"] is None, "output_result error has null result")
        assert_true(parsed["error"] == "something failed", "output_result error has correct message")
    finally:
        sys.stdout = old_stdout


async def test_data_dir_env_override():
    sandbox = make_sandbox("env-override")
    try:
        os.environ["SKILL_STORE_DATA_DIR"] = str(sandbox / "custom")
        import importlib
        import lib.config as cfg
        importlib.reload(cfg)
        assert_true(str(cfg.DATA_DIR) == str(sandbox / "custom"), "DATA_DIR uses SKILL_STORE_DATA_DIR env var")
    finally:
        os.environ.pop("SKILL_STORE_DATA_DIR", None)
        importlib.reload(cfg)
        shutil.rmtree(sandbox, ignore_errors=True)


import asyncio

async def main():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_config.py ===")
    await test_load_json_file_not_exists()
    await test_load_json_corrupted()
    await test_load_json_valid()
    await test_save_json_creates_dir()
    await test_save_json_overwrite()
    await test_ensure_data_dir()
    await test_output_result_success()
    await test_output_result_error()
    await test_data_dir_env_override()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(1 if exit_code > 0 else 0)
