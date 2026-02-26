#!/usr/bin/env python3
"""Unit tests for scripts/index.py (parse_skill_md and search)"""

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


def test_parse_normal_skill_md():
    sandbox = make_sandbox("parse-normal")
    try:
        skill_md = sandbox / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: A test skill for unit testing
---

# Test Skill
""", encoding="utf-8")
        from scripts.index import parse_skill_md
        result = parse_skill_md(skill_md)
        assert_true(result is not None, "parse normal: returns dict")
        assert_true(result["name"] == "test-skill", "parse normal: correct name")
        assert_true("test skill" in result["description"].lower(), "parse normal: correct description")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_parse_multiline_description():
    sandbox = make_sandbox("parse-multiline")
    try:
        skill_md = sandbox / "SKILL.md"
        skill_md.write_text("""---
name: multi-desc
description: |
  First line of description.
  Second line of description.
---

# Multi
""", encoding="utf-8")
        from scripts.index import parse_skill_md
        result = parse_skill_md(skill_md)
        assert_true(result is not None, "parse multiline: returns dict")
        assert_true("First line" in result["description"], "parse multiline: contains first line")
        assert_true("Second line" in result["description"], "parse multiline: contains second line")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_parse_with_dependencies():
    sandbox = make_sandbox("parse-deps")
    try:
        skill_md = sandbox / "SKILL.md"
        skill_md.write_text("""---
name: dep-skill
description: Skill with dependencies
dependencies:
  - playwright
  - agent-interact
---

# Dep Skill
""", encoding="utf-8")
        from scripts.index import parse_skill_md
        result = parse_skill_md(skill_md)
        assert_true(result is not None, "parse deps: returns dict")
        assert_true("dependencies" in result, "parse deps: has dependencies key")
        assert_true(result["dependencies"] == ["playwright", "agent-interact"],
                    "parse deps: correct dependency list")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_parse_no_frontmatter():
    sandbox = make_sandbox("parse-nofm")
    try:
        skill_md = sandbox / "SKILL.md"
        skill_md.write_text("# Just Markdown\n\nNo frontmatter here.", encoding="utf-8")
        from scripts.index import parse_skill_md
        result = parse_skill_md(skill_md)
        assert_true(result is None, "parse no frontmatter: returns None")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_parse_missing_name():
    sandbox = make_sandbox("parse-noname")
    try:
        skill_md = sandbox / "SKILL.md"
        skill_md.write_text("""---
description: Has description but no name
---
""", encoding="utf-8")
        from scripts.index import parse_skill_md
        result = parse_skill_md(skill_md)
        assert_true(result is None, "parse missing name: returns None")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_parse_missing_description():
    sandbox = make_sandbox("parse-nodesc")
    try:
        skill_md = sandbox / "SKILL.md"
        skill_md.write_text("""---
name: no-desc-skill
---
""", encoding="utf-8")
        from scripts.index import parse_skill_md
        result = parse_skill_md(skill_md)
        assert_true(result is None, "parse missing description: returns None")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_parse_file_not_exists():
    sandbox = make_sandbox("parse-nofile")
    try:
        from scripts.index import parse_skill_md
        result = parse_skill_md(sandbox / "nonexistent" / "SKILL.md")
        assert_true(result is None, "parse nonexistent file: returns None")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def test_search_keyword_match_name():
    sandbox = make_sandbox("search-name")
    try:
        cfg = _setup_env(sandbox)
        cfg.save_index({
            "updated_at": "2026-01-01",
            "skills": [
                {"name": "pdf-processor", "description": "Process PDF files",
                 "registry_alias": "r1", "relative_path": "skills/pdf-processor"},
                {"name": "web-scraper", "description": "Scrape web pages",
                 "registry_alias": "r1", "relative_path": "skills/web-scraper"}
            ]
        })

        from scripts.index import search_index
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        search_index("pdf")
        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        results = output["result"]["results"]
        assert_true(len(results) >= 1, "search name: at least 1 result")
        assert_true(results[0]["name"] == "pdf-processor", "search name: pdf-processor is first")
    finally:
        _teardown_env(sandbox)


def test_search_keyword_match_description():
    sandbox = make_sandbox("search-desc")
    try:
        cfg = _setup_env(sandbox)
        cfg.save_index({
            "updated_at": "2026-01-01",
            "skills": [
                {"name": "doc-tool", "description": "Extract text from documents",
                 "registry_alias": "r1", "relative_path": "skills/doc-tool"},
                {"name": "other", "description": "Something else",
                 "registry_alias": "r1", "relative_path": "skills/other"}
            ]
        })

        from scripts.index import search_index
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        search_index("extract text")
        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        results = output["result"]["results"]
        assert_true(len(results) >= 1, "search desc: at least 1 result")
        assert_true(results[0]["name"] == "doc-tool", "search desc: doc-tool matched")
    finally:
        _teardown_env(sandbox)


def test_search_no_match():
    sandbox = make_sandbox("search-nomatch")
    try:
        cfg = _setup_env(sandbox)
        cfg.save_index({
            "updated_at": "2026-01-01",
            "skills": [
                {"name": "skill-a", "description": "Does something",
                 "registry_alias": "r1", "relative_path": "skills/a"}
            ]
        })

        from scripts.index import search_index
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        search_index("zzzzzzzzz")
        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        results = output["result"]["results"]
        assert_true(len(results) == 0, "search no match: empty results")
    finally:
        _teardown_env(sandbox)


def _setup_env(sandbox):
    os.environ["SKILL_STORE_DATA_DIR"] = str(sandbox)
    import lib.config as cfg
    importlib.reload(cfg)
    cfg.ensure_data_dir()
    return cfg


def _teardown_env(sandbox):
    os.environ.pop("SKILL_STORE_DATA_DIR", None)
    import lib.config as cfg
    importlib.reload(cfg)
    shutil.rmtree(sandbox, ignore_errors=True)


def main():
    TESTDATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=== test_index.py ===")
    test_parse_normal_skill_md()
    test_parse_multiline_description()
    test_parse_with_dependencies()
    test_parse_no_frontmatter()
    test_parse_missing_name()
    test_parse_missing_description()
    test_parse_file_not_exists()
    test_search_keyword_match_name()
    test_search_keyword_match_description()
    test_search_no_match()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main() > 0 else 0)
