#!/usr/bin/env python3
"""Unit tests for scripts/hook.py"""

import json
import os
import shutil
import sys
import importlib
from datetime import datetime, timezone, timedelta
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


def setup_env(sandbox):
    os.environ["SKILL_STORE_DATA_DIR"] = str(sandbox)
    import lib.config as cfg
    importlib.reload(cfg)
    cfg.ensure_data_dir()
    return cfg


def teardown_env(sandbox):
    os.environ.pop("SKILL_STORE_DATA_DIR", None)
    import lib.config as cfg
    importlib.reload(cfg)
    shutil.rmtree(sandbox, ignore_errors=True)


def test_already_synced_today():
    sandbox = make_sandbox("hook-today")
    try:
        cfg = setup_env(sandbox)
        now = datetime.now(timezone.utc).isoformat()
        cfg.save_status({
            "last_sync": now,
            "sync_in_progress": False,
            "pending_updates": [],
            "orphaned_skills": [],
            "sync_errors": []
        })

        from scripts.hook import _already_synced_today
        importlib.reload(sys.modules["scripts.hook"])
        from scripts.hook import _already_synced_today
        status = cfg.load_status()
        assert_true(_already_synced_today(status), "today sync: returns True")
    finally:
        teardown_env(sandbox)


def test_not_synced_today():
    sandbox = make_sandbox("hook-yesterday")
    try:
        cfg = setup_env(sandbox)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        cfg.save_status({
            "last_sync": yesterday,
            "sync_in_progress": False,
            "pending_updates": [],
            "orphaned_skills": [],
            "sync_errors": []
        })

        importlib.reload(sys.modules.get("scripts.hook", sys.modules[__name__]))
        from scripts.hook import _already_synced_today
        status = cfg.load_status()
        assert_true(not _already_synced_today(status), "yesterday sync: returns False")
    finally:
        teardown_env(sandbox)


def test_null_last_sync():
    sandbox = make_sandbox("hook-null")
    try:
        cfg = setup_env(sandbox)
        cfg.save_status({
            "last_sync": None,
            "sync_in_progress": False,
            "pending_updates": [],
            "orphaned_skills": [],
            "sync_errors": []
        })

        from scripts.hook import _already_synced_today
        status = cfg.load_status()
        assert_true(not _already_synced_today(status), "null last_sync: returns False")
    finally:
        teardown_env(sandbox)


def test_config_not_exists():
    sandbox = make_sandbox("hook-noconfig")
    try:
        cfg = setup_env(sandbox)
        config_file = cfg.CONFIG_FILE
        if config_file.exists():
            config_file.unlink()

        from scripts.hook import main as hook_main
        hook_main()
        assert_true(True, "no config: hook exits gracefully")
    finally:
        teardown_env(sandbox)


def test_pid_file_stale():
    sandbox = make_sandbox("hook-stale-pid")
    try:
        cfg = setup_env(sandbox)

        if "scripts.hook" in sys.modules:
            del sys.modules["scripts.hook"]
        from scripts.hook import _read_pid, WORKER_PID_FILE as hook_pid_file

        pid_file = cfg.WORKER_PID_FILE
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text("999999999")

        result = _read_pid()
        assert_true(result is None, "stale PID: returns None (process not alive)")
        assert_true(not pid_file.exists(), "stale PID: file cleaned up")
    finally:
        teardown_env(sandbox)


def test_display_pending_updates():
    sandbox = make_sandbox("hook-display")
    try:
        cfg = setup_env(sandbox)
        cfg.save_status({
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "sync_in_progress": False,
            "pending_updates": [
                {"name": "test-skill", "installed_commit": "abc1234",
                 "latest_commit": "def5678", "scope": "global",
                 "target_path": "~/.cursor/skills/test-skill"}
            ],
            "orphaned_skills": [],
            "sync_errors": []
        })

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        from scripts.hook import _display_status
        status = cfg.load_status()
        _display_status(status)

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert_true("test-skill" in output, "display: contains skill name")
        assert_true("abc1234"[:7] in output, "display: contains old commit")
        assert_true("def5678"[:7] in output, "display: contains new commit")
    finally:
        teardown_env(sandbox)


def main():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_hook.py ===")
    test_already_synced_today()
    test_not_synced_today()
    test_null_last_sync()
    test_config_not_exists()
    test_pid_file_stale()
    test_display_pending_updates()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main() > 0 else 0)
