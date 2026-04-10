"""Tests for session/injector.py."""

import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))

from src.session.injector import find_kb_root, load_session_mode, generate_context


def _setup_kb(tmp_path, mode="recommended", concepts=None):
    config = {"session_mode": mode}
    (tmp_path / ".kc-config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )

    wiki = tmp_path / "wiki"
    wiki.mkdir(exist_ok=True)
    (wiki / "concepts").mkdir(exist_ok=True)

    index = "# Wiki Index\n\n| Concept | Coverage |\n|---|---|\n"
    if concepts:
        for slug, meta_body in concepts.items():
            (wiki / "concepts" / f"{slug}.md").write_text(meta_body, encoding="utf-8")
            index += f"| {slug} | high |\n"
    (wiki / "INDEX.md").write_text(index, encoding="utf-8")


SAMPLE_ARTICLE = """---
id: "test-concept"
title: "Test Concept"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Test Concept

## Summary
<!-- coverage: high -->

This is a test concept article with real content.
"""


class TestFindKbRoot:
    def test_finds_root(self, tmp_path):
        (tmp_path / ".kc-config.json").write_text("{}", encoding="utf-8")
        result = find_kb_root(tmp_path)
        assert result == tmp_path

    def test_finds_parent_root(self, tmp_path):
        (tmp_path / ".kc-config.json").write_text("{}", encoding="utf-8")
        child = tmp_path / "sub" / "deep"
        child.mkdir(parents=True)
        result = find_kb_root(child)
        assert result == tmp_path

    def test_returns_none_when_missing(self, tmp_path):
        result = find_kb_root(tmp_path)
        assert result is None


class TestLoadSessionMode:
    def test_reads_mode(self, tmp_path):
        config = {"session_mode": "primary"}
        (tmp_path / ".kc-config.json").write_text(json.dumps(config), encoding="utf-8")
        assert load_session_mode(tmp_path) == "primary"

    def test_default_staging(self, tmp_path):
        (tmp_path / ".kc-config.json").write_text("{}", encoding="utf-8")
        assert load_session_mode(tmp_path) == "staging"

    def test_missing_config(self, tmp_path):
        assert load_session_mode(tmp_path) == "staging"

    def test_invalid_json(self, tmp_path):
        (tmp_path / ".kc-config.json").write_text("not json", encoding="utf-8")
        assert load_session_mode(tmp_path) == "staging"


class TestGenerateContext:
    def test_staging_mode(self, tmp_path):
        _setup_kb(tmp_path, mode="staging", concepts={"test": SAMPLE_ARTICLE})
        ctx = generate_context(tmp_path)
        assert ctx is not None
        assert "Mode: staging" in ctx
        assert "按需查阅" in ctx

    def test_recommended_mode(self, tmp_path):
        _setup_kb(tmp_path, mode="recommended", concepts={"test": SAMPLE_ARTICLE})
        ctx = generate_context(tmp_path)
        assert "Mode: recommended" in ctx
        assert "优先参考" in ctx
        assert "概念摘要" in ctx

    def test_primary_mode(self, tmp_path):
        _setup_kb(tmp_path, mode="primary", concepts={"test": SAMPLE_ARTICLE})
        ctx = generate_context(tmp_path)
        assert "Mode: primary" in ctx
        assert "主要信息源" in ctx

    def test_no_concepts_returns_none(self, tmp_path):
        _setup_kb(tmp_path, concepts=None)
        ctx = generate_context(tmp_path)
        assert ctx is None

    def test_no_index_returns_none(self, tmp_path):
        config = {"session_mode": "staging"}
        (tmp_path / ".kc-config.json").write_text(json.dumps(config), encoding="utf-8")
        ctx = generate_context(tmp_path)
        assert ctx is None

    def test_concept_count_in_context(self, tmp_path):
        _setup_kb(tmp_path, concepts={
            "a": SAMPLE_ARTICLE,
            "b": SAMPLE_ARTICLE.replace("test-concept", "b"),
        })
        ctx = generate_context(tmp_path)
        assert "Concepts: 2" in ctx
