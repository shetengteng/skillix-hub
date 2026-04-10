"""Tests for query.py (kc query command)."""

import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))

from src.commands.query import _save_query_concept, _score_relevance, _extract_low_coverage_sections
from src.compiler import _parse_frontmatter


def _make_concept(slug, title, body, tags=None, sources=None):
    return {
        "slug": slug,
        "title": title,
        "tags": tags or [],
        "sources": sources or [],
        "body": body,
        "meta": {"id": slug, "title": title},
        "path": Path(f"wiki/concepts/{slug}.md"),
    }


class TestSaveQueryConcept:
    def test_saves_new_concept(self, tmp_path):
        """--save 应创建新的概念文件。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        relevant = [
            _make_concept("api-gateway", "API Gateway", "Gateway content."),
            _make_concept("microservice", "Microservice", "Microservice content."),
        ]

        _save_query_concept("How does API routing work", relevant, tmp_path)

        expected_slug = "how-does-api-routing-work"
        target = concepts_dir / f"{expected_slug}.md"
        assert target.exists()

        content = target.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)
        assert meta["id"] == expected_slug
        assert "api-gateway" in meta.get("relations", {}).get("related", [])
        assert "microservice" in meta.get("relations", {}).get("related", [])
        assert meta["compile_count"] == 0

    def test_skips_existing_concept(self, tmp_path, capsys):
        """--save 应跳过已存在的概念。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        slug = "existing-topic"
        (concepts_dir / f"{slug}.md").write_text("existing", encoding="utf-8")

        relevant = [_make_concept("other", "Other", "Content.")]
        _save_query_concept("Existing Topic", relevant, tmp_path)

        content = (concepts_dir / f"{slug}.md").read_text(encoding="utf-8")
        assert content == "existing"

    def test_concept_has_wiki_links(self, tmp_path):
        """保存的概念应包含 [[]] 风格的关联链接。"""
        concepts_dir = tmp_path / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True)

        relevant = [_make_concept("db-migration", "DB Migration", "Migration info.")]
        _save_query_concept("Database Strategy", relevant, tmp_path)

        slug = "database-strategy"
        content = (concepts_dir / f"{slug}.md").read_text(encoding="utf-8")
        assert "[[db-migration]]" in content


class TestScoreRelevance:
    def test_title_match_scores_high(self):
        concept = _make_concept("api-gateway", "API Gateway Design", "some body")
        score = _score_relevance("API gateway", concept)
        assert score >= 10

    def test_no_match_scores_zero(self):
        concept = _make_concept("api-gateway", "API Gateway", "gateway content")
        score = _score_relevance("database migration", concept)
        assert score == 0


class TestExtractLowCoverage:
    def test_finds_low_sections(self):
        body = "## Summary\n<!-- coverage: high -->\nGood.\n\n## Gotchas\n<!-- coverage: low -->\nWeak."
        sections = _extract_low_coverage_sections(body)
        assert "Gotchas" in sections
        assert "Summary" not in sections

    def test_no_low_sections(self):
        body = "## Summary\n<!-- coverage: high -->\nGood content."
        sections = _extract_low_coverage_sections(body)
        assert sections == []
