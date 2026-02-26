#!/usr/bin/env python3
"""Unit tests for lib/git_ops.py"""

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


def test_run_git_version():
    from lib.git_ops import run_git
    code, stdout, stderr = run_git(["--version"])
    assert_true(code == 0, "run_git --version returns code 0")
    assert_true("git version" in stdout, "run_git --version output contains 'git version'")


def test_run_git_invalid_command():
    from lib.git_ops import run_git
    code, stdout, stderr = run_git(["not-a-real-command-xyz"])
    assert_true(code != 0, "run_git with invalid command returns non-zero code")


def test_is_git_repo_true():
    sandbox = make_sandbox("is-git-true")
    try:
        (sandbox / ".git").mkdir()
        from lib.git_ops import is_git_repo
        assert_true(is_git_repo(sandbox), "is_git_repo returns True when .git exists")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_is_git_repo_false():
    sandbox = make_sandbox("is-git-false")
    try:
        from lib.git_ops import is_git_repo
        assert_true(not is_git_repo(sandbox), "is_git_repo returns False when no .git")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_get_latest_commit_no_repo():
    import tempfile
    sandbox = Path(tempfile.mkdtemp(prefix="skill-store-test-"))
    try:
        from lib.git_ops import get_latest_commit
        result = get_latest_commit(sandbox)
        assert_true(result is None, "get_latest_commit returns None for non-git dir")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_clone_invalid_url():
    sandbox = make_sandbox("clone-invalid")
    try:
        from lib.git_ops import clone
        success, msg = clone("https://invalid-url-that-does-not-exist.example.com/repo.git",
                             sandbox / "target", depth=1, branch="main")
        assert_true(not success, "clone returns False for invalid URL")
        assert_true(len(msg) > 0, "clone returns error message for invalid URL")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def main():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_git_ops.py ===")
    test_run_git_version()
    test_run_git_invalid_command()
    test_is_git_repo_true()
    test_is_git_repo_false()
    test_get_latest_commit_no_repo()
    test_clone_invalid_url()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main() > 0 else 0)
