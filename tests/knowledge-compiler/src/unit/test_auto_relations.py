"""Tests for _auto_fill_relations in compile.py."""

import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))

from src.commands.compile import _auto_fill_relations
from src.compiler import _parse_frontmatter


def _write_article(concepts_dir, slug, body, relations=None):
    meta_lines = [
        "---",
        f'id: "{slug}"',
        f'title: "{slug.replace("-", " ").title()}"',
        "sources:",
        "  - raw/test.md",
    ]
    if relations:
        meta_lines.append("relations:")
        meta_lines.append("  related:")
        for r in relations.get("related", []):
            meta_lines.append(f"    - {r}")
        meta_lines.append("  depends_on: []")
    else:
        meta_lines.append("relations:")
        meta_lines.append("  related: []")
        meta_lines.append("  depends_on: []")
    meta_lines.extend([
        'created: "2026-04-10"',
        'updated: "2026-04-10"',
        "---",
    ])
    content = "\n".join(meta_lines) + "\n" + body
    (concepts_dir / f"{slug}.md").write_text(content, encoding="utf-8")


class TestAutoFillRelations:
    def test_detects_slug_in_body(self, tmp_path):
        """正文中提到其他概念 slug 时应自动加入 relations.related。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        _write_article(concepts_dir, "api-design",
                        "\n# API Design\n\nThis relates to error-handling patterns.\n")
        _write_article(concepts_dir, "error-handling",
                        "\n# Error Handling\n\nStandard approach.\n")

        _auto_fill_relations(tmp_path, concepts_dir)

        content = (concepts_dir / "api-design.md").read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(content)
        assert "error-handling" in meta["relations"]["related"]

    def test_detects_wiki_link(self, tmp_path):
        """正文中使用 [[slug]] 引用时应加入 relations.related。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        _write_article(concepts_dir, "overview",
                        "\n# Overview\n\nSee [[deployment-guide]] for details.\n")
        _write_article(concepts_dir, "deployment-guide",
                        "\n# Deployment Guide\n\nSteps here.\n")

        _auto_fill_relations(tmp_path, concepts_dir)

        content = (concepts_dir / "overview.md").read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(content)
        assert "deployment-guide" in meta["relations"]["related"]

    def test_preserves_existing_relations(self, tmp_path):
        """已有的 relations 应该被保留，不被覆盖。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        _write_article(concepts_dir, "api-design",
                        "\n# API Design\n\nUses error-handling.\n",
                        relations={"related": ["existing-concept"]})
        _write_article(concepts_dir, "error-handling",
                        "\n# Error Handling\n\nBasic.\n")
        _write_article(concepts_dir, "existing-concept",
                        "\n# Existing Concept\n\nContent.\n")

        _auto_fill_relations(tmp_path, concepts_dir)

        content = (concepts_dir / "api-design.md").read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(content)
        related = meta["relations"]["related"]
        assert "existing-concept" in related
        assert "error-handling" in related

    def test_no_self_reference(self, tmp_path):
        """不应将自身加入 relations.related。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        _write_article(concepts_dir, "api-design",
                        "\n# API Design\n\nThe api-design pattern is important.\n")

        _auto_fill_relations(tmp_path, concepts_dir)

        content = (concepts_dir / "api-design.md").read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(content)
        assert "api-design" not in meta["relations"].get("related", [])

    def test_no_change_when_no_mentions(self, tmp_path):
        """正文不包含其他概念 slug 时文件不应被修改。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        _write_article(concepts_dir, "api-design",
                        "\n# API Design\n\nPure standalone content.\n")
        _write_article(concepts_dir, "database-migration",
                        "\n# Database Migration\n\nUnrelated content.\n")

        original_a = (concepts_dir / "api-design.md").read_text(encoding="utf-8")
        _auto_fill_relations(tmp_path, concepts_dir)
        after = (concepts_dir / "api-design.md").read_text(encoding="utf-8")

        assert original_a == after

    def test_empty_concepts_dir(self, tmp_path):
        """空的 concepts 目录不应报错。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)
        _auto_fill_relations(tmp_path, concepts_dir)

    def test_nonexistent_dir(self, tmp_path):
        """不存在的目录不应报错。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        _auto_fill_relations(tmp_path, concepts_dir)
