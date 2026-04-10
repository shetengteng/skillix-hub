"""indexer.py 单元测试。"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"))

from src.indexer import generate_index, update_index


ARTICLE_HIGH = """---
id: "concept-a"
title: "Concept A"
sources:
  - raw/a.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Concept A

## Summary
<!-- coverage: high -->
Good content.

## Details
<!-- coverage: medium -->
Some details.
"""

ARTICLE_LOW = """---
id: "concept-b"
title: "Concept B"
sources:
  - raw/b.md
  - raw/c.md
created: "2026-04-09"
updated: "2026-04-09"
---

# Concept B

## Summary
<!-- coverage: low -->
Sparse content.
"""

SCHEMA_CONTENT = """## Topic Taxonomy

### Architecture
- concept-a

### Uncategorized
- concept-b
"""


def _setup_kb(tmp_path, articles, schema_content=""):
    wiki_dir = tmp_path / "wiki"
    concepts_dir = wiki_dir / "concepts"
    concepts_dir.mkdir(parents=True)

    if schema_content:
        (wiki_dir / "schema.md").write_text(schema_content, encoding="utf-8")

    for slug, content in articles.items():
        (concepts_dir / f"{slug}.md").write_text(content, encoding="utf-8")


class TestGenerateIndex:
    def test_contains_stats(self, tmp_path):
        _setup_kb(tmp_path,
            {"concept-a": ARTICLE_HIGH, "concept-b": ARTICLE_LOW},
            SCHEMA_CONTENT)

        index = generate_index(tmp_path)
        assert "Total concepts: 2" in index
        assert "High coverage:" in index

    def test_grouped_by_category(self, tmp_path):
        _setup_kb(tmp_path,
            {"concept-a": ARTICLE_HIGH, "concept-b": ARTICLE_LOW},
            SCHEMA_CONTENT)

        index = generate_index(tmp_path)
        assert "## Architecture" in index
        assert "[[concept-a]]" in index

    def test_uncategorized_section(self, tmp_path):
        _setup_kb(tmp_path,
            {"concept-a": ARTICLE_HIGH, "concept-b": ARTICLE_LOW},
            SCHEMA_CONTENT)

        index = generate_index(tmp_path)
        assert "## Uncategorized" in index
        assert "[[concept-b]]" in index

    def test_coverage_format(self, tmp_path):
        _setup_kb(tmp_path,
            {"concept-a": ARTICLE_HIGH},
            SCHEMA_CONTENT)

        index = generate_index(tmp_path)
        assert "1H/1M/0L" in index

    def test_updated_date_from_frontmatter(self, tmp_path):
        _setup_kb(tmp_path,
            {"concept-b": ARTICLE_LOW},
            SCHEMA_CONTENT)

        index = generate_index(tmp_path)
        assert "2026-04-09" in index


class TestUpdateIndex:
    def test_writes_file(self, tmp_path):
        _setup_kb(tmp_path,
            {"concept-a": ARTICLE_HIGH},
            SCHEMA_CONTENT)

        update_index(tmp_path)

        index_path = tmp_path / "wiki" / "INDEX.md"
        assert index_path.exists()
        content = index_path.read_text(encoding="utf-8")
        assert "Wiki Index" in content

    def test_empty_kb(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        concepts_dir = wiki_dir / "concepts"
        concepts_dir.mkdir(parents=True)

        update_index(tmp_path)

        content = (wiki_dir / "INDEX.md").read_text(encoding="utf-8")
        assert "Total concepts: 0" in content
