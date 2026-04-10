"""verifier.py 单元测试。"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"))

from src.verifier import verify


def _setup_kb(tmp_path, articles=None, schema_content=None, source_files=None):
    """设置测试知识库。"""
    wiki_dir = tmp_path / "wiki"
    concepts_dir = wiki_dir / "concepts"
    concepts_dir.mkdir(parents=True)

    if schema_content:
        (wiki_dir / "schema.md").write_text(schema_content, encoding="utf-8")

    if source_files:
        for rel_path, content in source_files.items():
            p = tmp_path / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

    if articles:
        for slug, content in articles.items():
            (concepts_dir / f"{slug}.md").write_text(content, encoding="utf-8")


VALID_ARTICLE = """---
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

Real content here. [source: raw/test.md]

## Sources
- [source: raw/test.md]
"""

SCHEMA_WITH_TOPIC = """## Topic Taxonomy

### Uncategorized
- test-concept
"""


class TestHardGates:
    def test_complete_frontmatter_passes(self, tmp_path):
        _setup_kb(tmp_path,
            articles={"test-concept": VALID_ARTICLE},
            schema_content=SCHEMA_WITH_TOPIC,
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        fm_results = [r for r in report.hard_results if r.check_name == "frontmatter_complete"]
        assert all(r.passed for r in fm_results)

    def test_missing_frontmatter_fails(self, tmp_path):
        article = "# No frontmatter\n\n## Summary\n<!-- coverage: low -->\nContent.\n"
        _setup_kb(tmp_path, articles={"bad": article})

        report = verify(tmp_path)
        fm_results = [r for r in report.hard_results if r.check_name == "frontmatter_complete"]
        assert any(not r.passed for r in fm_results)

    def test_invalid_source_ref_fails(self, tmp_path):
        article = """---
id: "test"
title: "Test"
sources:
  - raw/nonexistent.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Test

## Summary
<!-- coverage: low -->

[source: raw/nonexistent.md]
"""
        _setup_kb(tmp_path, articles={"test": article})

        report = verify(tmp_path)
        ref_results = [r for r in report.hard_results if r.check_name == "source_refs_valid"]
        assert any(not r.passed for r in ref_results)

    def test_schema_consistency(self, tmp_path):
        _setup_kb(tmp_path,
            articles={"test-concept": VALID_ARTICLE},
            schema_content=SCHEMA_WITH_TOPIC,
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        schema_results = [r for r in report.hard_results if r.check_name == "schema_consistent"]
        assert all(r.passed for r in schema_results)

    def test_not_in_schema_fails(self, tmp_path):
        _setup_kb(tmp_path,
            articles={"test-concept": VALID_ARTICLE},
            schema_content="## Topic Taxonomy\n\n### Uncategorized\n",
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        schema_results = [r for r in report.hard_results if r.check_name == "schema_consistent"]
        assert any(not r.passed for r in schema_results)


class TestSoftGates:
    def test_orphan_concept(self, tmp_path):
        article = """---
id: "orphan"
title: "Orphan"
sources: []
created: "2026-04-10"
updated: "2026-04-10"
---

# Orphan

## Summary
<!-- coverage: low -->
Content.
"""
        _setup_kb(tmp_path, articles={"orphan": article})

        report = verify(tmp_path)
        orphan_results = [r for r in report.soft_results if r.check_name == "orphan_concept"]
        assert any(not r.passed for r in orphan_results)

    def test_broken_wiki_link(self, tmp_path):
        article = """---
id: "test"
title: "Test"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Test

## Summary
<!-- coverage: high -->
See [[nonexistent-concept]] for details.
"""
        _setup_kb(tmp_path,
            articles={"test": article},
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        link_results = [r for r in report.soft_results if r.check_name == "broken_links"]
        assert any(not r.passed for r in link_results)

    def test_aging_concept(self, tmp_path):
        article = """---
id: "old"
title: "Old"
sources:
  - raw/test.md
created: "2025-01-01"
updated: "2025-01-01"
---

# Old

## Summary
<!-- coverage: high -->
Ancient content.
"""
        _setup_kb(tmp_path,
            articles={"old": article},
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        aging_results = [r for r in report.soft_results if r.check_name == "aging"]
        assert any(not r.passed for r in aging_results)


class TestVerifyReport:
    def test_empty_kb(self, tmp_path):
        report = verify(tmp_path)
        assert report.hard_pass
        assert report.hard_results == []

    def test_summary_format(self, tmp_path):
        _setup_kb(tmp_path,
            articles={"test-concept": VALID_ARTICLE},
            schema_content=SCHEMA_WITH_TOPIC,
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        summary = report.summary()
        assert "Hard:" in summary
        assert "Soft:" in summary
