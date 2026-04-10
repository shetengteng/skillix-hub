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


    def test_stale_source_detected(self, tmp_path):
        """来源文件比编译状态新时应触发 stale_source 警告。"""
        import json, time

        raw_path = tmp_path / "raw" / "test.md"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("content", encoding="utf-8")

        old_mtime = raw_path.stat().st_mtime - 100
        state = {"files": {"raw/test.md": {"mtime": old_mtime}}}
        (tmp_path / ".compile-state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )

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
Content. [source: raw/test.md]
"""
        _setup_kb(tmp_path, articles={"test": article})

        report = verify(tmp_path)
        stale = [r for r in report.soft_results if r.check_name == "stale_source"]
        assert any(not r.passed for r in stale)

    def test_stale_source_ok(self, tmp_path):
        """来源文件与编译状态一致时不应触发 stale_source 警告。"""
        import json

        raw_path = tmp_path / "raw" / "test.md"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("content", encoding="utf-8")

        current_mtime = raw_path.stat().st_mtime + 100
        state = {"files": {"raw/test.md": {"mtime": current_mtime}}}
        (tmp_path / ".compile-state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )

        _setup_kb(tmp_path,
            articles={"test": VALID_ARTICLE},
            schema_content=SCHEMA_WITH_TOPIC)

        report = verify(tmp_path)
        stale = [r for r in report.soft_results if r.check_name == "stale_source"]
        assert all(r.passed for r in stale)

    def test_missing_cross_refs_detected(self, tmp_path):
        """文章正文提到其他概念但未用 [[]] 链接时应触发警告。"""
        article_a = """---
id: "api-design"
title: "API Design"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# API Design

## Summary
<!-- coverage: high -->
This relates to error handling patterns.
"""
        article_b = """---
id: "error-handling"
title: "Error Handling"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Error Handling

## Summary
<!-- coverage: high -->
Standard error handling content.
"""
        schema = """## Topic Taxonomy

### Uncategorized
- api-design
- error-handling
"""
        _setup_kb(tmp_path,
            articles={"api-design": article_a, "error-handling": article_b},
            schema_content=schema,
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        xref = [r for r in report.soft_results
                if r.check_name == "missing_cross_refs" and r.article == "api-design"]
        assert any(not r.passed for r in xref)

    def test_missing_cross_refs_ok_when_linked(self, tmp_path):
        """文章正文提到其他概念且已用 [[]] 链接时不应触发警告。"""
        article = """---
id: "api-design"
title: "API Design"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# API Design

## Summary
<!-- coverage: high -->
This relates to [[error-handling]] patterns.
"""
        article_b = """---
id: "error-handling"
title: "Error Handling"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Error Handling

## Summary
<!-- coverage: high -->
Standard content.
"""
        schema = """## Topic Taxonomy

### Uncategorized
- api-design
- error-handling
"""
        _setup_kb(tmp_path,
            articles={"api-design": article, "error-handling": article_b},
            schema_content=schema,
            source_files={"raw/test.md": "content"})

        report = verify(tmp_path)
        xref = [r for r in report.soft_results
                if r.check_name == "missing_cross_refs" and r.article == "api-design"]
        assert all(r.passed for r in xref)


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
