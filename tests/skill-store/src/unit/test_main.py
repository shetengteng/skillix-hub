#!/usr/bin/env python3
"""Unit tests for main.py (install/update/uninstall)"""

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


def test_install_to_new_dir():
    sandbox = make_sandbox("main-install")
    try:
        target = sandbox / "installed-skill-store"
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        from main import install
        install(str(target))

        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        assert_true(output["error"] is None, "install: no error")
        assert_true(target.exists(), "install: target directory created")
        assert_true((target / "SKILL.md").exists(), "install: SKILL.md copied")
        assert_true((target / "main.py").exists(), "install: main.py copied")
        assert_true((target / "scripts").is_dir(), "install: scripts/ copied")
        assert_true((target / "lib").is_dir(), "install: lib/ copied")

        data_dir = target.parent / "skill-store-data"
        assert_true(data_dir.exists(), "install: data dir created")
        assert_true((data_dir / "config.json").exists(), "install: config.json initialized")
        assert_true((data_dir / "repos").is_dir(), "install: repos/ created")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_install_excludes_pycache():
    sandbox = make_sandbox("main-exclude")
    try:
        pycache = SKILL_DIR / "__pycache__"
        pycache.mkdir(exist_ok=True)
        (pycache / "test.pyc").write_text("fake")

        target = sandbox / "installed"
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        from main import install
        install(str(target))
        sys.stdout = old_stdout

        assert_true(not (target / "__pycache__").exists(), "install: __pycache__ excluded")
    finally:
        pycache = SKILL_DIR / "__pycache__"
        if pycache.exists():
            shutil.rmtree(pycache)
        shutil.rmtree(sandbox, ignore_errors=True)


def test_update_preserves_data():
    sandbox = make_sandbox("main-update")
    try:
        target = sandbox / "skill-store"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("old content")

        data_dir = sandbox / "skill-store-data"
        data_dir.mkdir(parents=True)
        (data_dir / "config.json").write_text(json.dumps({"registries": [{"alias": "test"}]}))

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        from main import update
        update(str(target))

        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        assert_true(output["error"] is None, "update: no error")
        assert_true((target / "SKILL.md").exists(), "update: SKILL.md exists after update")

        config = json.loads((data_dir / "config.json").read_text())
        assert_true(config["registries"][0]["alias"] == "test", "update: data preserved")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_uninstall_removes_data():
    sandbox = make_sandbox("main-uninstall-rm")
    try:
        target = sandbox / "skill-store"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("content")

        data_dir = sandbox / "skill-store-data"
        data_dir.mkdir(parents=True)
        (data_dir / "config.json").write_text("{}")

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        from main import uninstall
        uninstall(str(target), keep_data=False)

        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        assert_true(output["error"] is None, "uninstall: no error")
        assert_true(not target.exists(), "uninstall: target removed")
        assert_true(not data_dir.exists(), "uninstall: data dir removed")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_uninstall_keeps_data():
    sandbox = make_sandbox("main-uninstall-keep")
    try:
        target = sandbox / "skill-store"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("content")

        data_dir = sandbox / "skill-store-data"
        data_dir.mkdir(parents=True)
        (data_dir / "config.json").write_text("{}")

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        from main import uninstall
        uninstall(str(target), keep_data=True)

        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        assert_true(not target.exists(), "uninstall keep: target removed")
        assert_true(data_dir.exists(), "uninstall keep: data dir preserved")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def main_test():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_main.py ===")
    test_install_to_new_dir()
    test_install_excludes_pycache()
    test_update_preserves_data()
    test_uninstall_removes_data()
    test_uninstall_keeps_data()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main_test() > 0 else 0)
