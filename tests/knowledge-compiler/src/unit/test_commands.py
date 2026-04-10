"""Tests for commands layer (init, add, lint, status, browse)."""

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))

import typer
from src.commands import init, add, lint, status, browse


@pytest.fixture
def cli_app():
    app = typer.Typer()
    for mod in [init, add, lint, status, browse]:
        mod.register(app)
    return app


@pytest.fixture
def runner():
    return CliRunner()


class TestInitCommand:
    def test_init_creates_structure(self, runner, cli_app, tmp_path):
        result = runner.invoke(cli_app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / ".kc-config.json").exists()
        assert (tmp_path / "raw" / "designs").is_dir()
        assert (tmp_path / "raw" / "decisions").is_dir()
        assert (tmp_path / "raw" / "research").is_dir()
        assert (tmp_path / "raw" / "notes").is_dir()
        assert (tmp_path / "wiki" / "concepts").is_dir()
        assert (tmp_path / "wiki" / "INDEX.md").exists()
        assert (tmp_path / "wiki" / "schema.md").exists()
        assert (tmp_path / "wiki" / "log.md").exists()

    def test_init_fails_if_exists(self, runner, cli_app, tmp_path):
        (tmp_path / ".kc-config.json").write_text("{}", encoding="utf-8")
        result = runner.invoke(cli_app, ["init", str(tmp_path)])
        assert result.exit_code == 1
        assert "已存在" in result.output


class TestAddCommand:
    def test_add_file(self, runner, cli_app, kc_root, tmp_path):
        src = tmp_path / "doc.md"
        src.write_text("# Test Doc\nContent.", encoding="utf-8")

        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["add", str(src)])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "已添加" in result.output

    def test_add_nonexistent(self, runner, cli_app, kc_root):
        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["add", "/nonexistent/file.md"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1


class TestLintCommand:
    def test_lint_empty_kb(self, runner, cli_app, kc_root):
        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["lint"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

    def test_lint_with_articles(self, runner, cli_app, kc_root):
        article = """---
id: "test"
title: "Test"
sources:
  - raw/research/transformer.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Test

## Summary
<!-- coverage: high -->

Content. [source: raw/research/transformer.md]
"""
        (kc_root / "wiki" / "concepts" / "test.md").write_text(article, encoding="utf-8")

        schema = """## Topic Taxonomy

### Uncategorized
- test
"""
        (kc_root / "wiki" / "schema.md").write_text(schema, encoding="utf-8")
        (kc_root / "raw" / "research" / "transformer.md").write_text("content", encoding="utf-8")

        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["lint"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Hard Gate" in result.output or "Soft Gate" in result.output or "概念" in result.output


class TestStatusCommand:
    def test_status_empty_kb(self, runner, cli_app, kc_root):
        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["status"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

    def test_status_with_source_files(self, runner, cli_app, kc_root, sample_docs):
        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["status"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0


class TestBrowseCommand:
    def test_browse_empty(self, runner, cli_app, kc_root):
        import os
        old_cwd = os.getcwd()
        os.chdir(kc_root)
        try:
            result = runner.invoke(cli_app, ["browse"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
