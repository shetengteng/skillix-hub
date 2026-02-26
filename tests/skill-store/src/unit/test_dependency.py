#!/usr/bin/env python3
"""Unit tests for lib/dependency.py"""

import json
import os
import shutil
import sys
import importlib
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


def setup_sandbox_env(sandbox):
    os.environ["SKILL_STORE_DATA_DIR"] = str(sandbox)
    import lib.config as cfg
    importlib.reload(cfg)
    cfg.ensure_data_dir()
    return cfg


def teardown_sandbox_env(sandbox):
    os.environ.pop("SKILL_STORE_DATA_DIR", None)
    import lib.config as cfg
    importlib.reload(cfg)
    shutil.rmtree(sandbox, ignore_errors=True)


def write_index(cfg, skills):
    cfg.save_index({"updated_at": "2026-01-01T00:00:00Z", "skills": skills})


def write_installed(cfg, installations):
    cfg.save_installed({"installations": installations})


def test_no_dependencies():
    sandbox = make_sandbox("dep-none")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": [],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        assert_true(len(order) == 1, "no deps: install_order has 1 entry")
        assert_true(order[0]["name"] == "skill-a", "no deps: entry is skill-a")
        assert_true(len(warnings) == 0, "no deps: no warnings")
    finally:
        teardown_sandbox_env(sandbox)


def test_single_dependency():
    sandbox = make_sandbox("dep-single")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": ["skill-b"],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True},
            {"name": "skill-b", "description": "B", "dependencies": [],
             "registry_alias": "r1", "relative_path": "skills/skill-b",
             "commit_hash": "bbb", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        names = [s["name"] for s in order]
        assert_true(names == ["skill-b", "skill-a"], "single dep: B installed before A")
        assert_true(len(warnings) == 0, "single dep: no warnings")
    finally:
        teardown_sandbox_env(sandbox)


def test_multi_level_dependency():
    sandbox = make_sandbox("dep-multi")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": ["skill-b"],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True},
            {"name": "skill-b", "description": "B", "dependencies": ["skill-c"],
             "registry_alias": "r1", "relative_path": "skills/skill-b",
             "commit_hash": "bbb", "commit_date": None, "has_skill_md": True},
            {"name": "skill-c", "description": "C", "dependencies": [],
             "registry_alias": "r1", "relative_path": "skills/skill-c",
             "commit_hash": "ccc", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        names = [s["name"] for s in order]
        assert_true(names == ["skill-c", "skill-b", "skill-a"], "multi dep: C→B→A order")
    finally:
        teardown_sandbox_env(sandbox)


def test_circular_dependency():
    sandbox = make_sandbox("dep-circular")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": ["skill-b"],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True},
            {"name": "skill-b", "description": "B", "dependencies": ["skill-a"],
             "registry_alias": "r1", "relative_path": "skills/skill-b",
             "commit_hash": "bbb", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        has_circular = any("Circular" in w or "circular" in w.lower() for w in warnings)
        assert_true(has_circular, "circular dep: warning contains 'Circular'")
    finally:
        teardown_sandbox_env(sandbox)


def test_dependency_already_installed():
    sandbox = make_sandbox("dep-installed")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": ["skill-b"],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True},
            {"name": "skill-b", "description": "B", "dependencies": [],
             "registry_alias": "r1", "relative_path": "skills/skill-b",
             "commit_hash": "bbb", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [
            {"name": "skill-b", "registry_alias": "r1", "source_commit": "bbb",
             "target_path": "/tmp/fake", "scope": "global"}
        ])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        names = [s["name"] for s in order]
        assert_true("skill-b" not in names, "installed dep: skill-b skipped")
        assert_true("skill-a" in names, "installed dep: skill-a included")
    finally:
        teardown_sandbox_env(sandbox)


def test_dependency_not_found():
    sandbox = make_sandbox("dep-notfound")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": ["skill-x"],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        has_not_found = any("not found" in w.lower() for w in warnings)
        assert_true(has_not_found, "missing dep: warning contains 'not found'")
    finally:
        teardown_sandbox_env(sandbox)


def test_multi_registry_same_name():
    sandbox = make_sandbox("dep-multi-reg")
    try:
        cfg = setup_sandbox_env(sandbox)
        write_index(cfg, [
            {"name": "skill-a", "description": "A", "dependencies": ["skill-b"],
             "registry_alias": "r1", "relative_path": "skills/skill-a",
             "commit_hash": "aaa", "commit_date": None, "has_skill_md": True},
            {"name": "skill-b", "description": "B from r1", "dependencies": [],
             "registry_alias": "r1", "relative_path": "skills/skill-b",
             "commit_hash": "bbb1", "commit_date": None, "has_skill_md": True},
            {"name": "skill-b", "description": "B from r2", "dependencies": [],
             "registry_alias": "r2", "relative_path": "skills/skill-b",
             "commit_hash": "bbb2", "commit_date": None, "has_skill_md": True}
        ])
        write_installed(cfg, [])

        import lib.dependency as dep
        importlib.reload(dep)
        order, warnings = dep.resolve_dependencies("skill-a", "r1")
        b_entry = next((s for s in order if s["name"] == "skill-b"), None)
        assert_true(b_entry is not None, "multi-reg: skill-b resolved")
        assert_true(b_entry["registry_alias"] == "r1", "multi-reg: prefers same registry")
    finally:
        teardown_sandbox_env(sandbox)


def main():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_dependency.py ===")
    test_no_dependencies()
    test_single_dependency()
    test_multi_level_dependency()
    test_circular_dependency()
    test_dependency_already_installed()
    test_dependency_not_found()
    test_multi_registry_same_name()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main() > 0 else 0)
