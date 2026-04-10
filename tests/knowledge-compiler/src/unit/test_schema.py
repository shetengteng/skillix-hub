"""schema.py 单元测试。"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"))

from src.schema import load_schema, update_schema, _parse_taxonomy, _parse_deprecated, _parse_cross_refs


SAMPLE_SCHEMA = """---
title: Wiki Schema
updated: "2026-04-10"
---

# Wiki Schema

## Topic Taxonomy

### Architecture
- api-gateway-design
- microservice-patterns

### Database
- db-migration-strategy

### Uncategorized

## Naming Conventions

- Topic slugs: `lowercase-kebab-case`

## Cross-Reference Rules

api-gateway-design <-> microservice-patterns

## Deprecated Topics

| Old Slug | Merged Into | Date |
|----------|-------------|------|
| old-api | api-gateway-design | 2026-04-01 |

## Notes
"""


class TestParseTaxonomy:
    def test_parse_categories(self):
        taxonomy = _parse_taxonomy(SAMPLE_SCHEMA)
        assert "Architecture" in taxonomy
        assert "Database" in taxonomy
        assert "api-gateway-design" in taxonomy["Architecture"]
        assert "microservice-patterns" in taxonomy["Architecture"]
        assert "db-migration-strategy" in taxonomy["Database"]

    def test_empty_category(self):
        taxonomy = _parse_taxonomy(SAMPLE_SCHEMA)
        assert taxonomy.get("Uncategorized", []) == []


class TestParseDeprecated:
    def test_parse_deprecated(self):
        deprecated = _parse_deprecated(SAMPLE_SCHEMA)
        assert "old-api" in deprecated
        assert deprecated["old-api"] == "api-gateway-design"

    def test_empty_deprecated(self):
        content = "## Deprecated Topics\n\n| Old Slug | Merged Into | Date |\n|----------|-------------|------|\n"
        deprecated = _parse_deprecated(content)
        assert deprecated == {}


class TestParseCrossRefs:
    def test_parse_cross_refs(self):
        refs = _parse_cross_refs(SAMPLE_SCHEMA)
        assert ("api-gateway-design", "microservice-patterns") in refs

    def test_no_cross_refs(self):
        content = "## Cross-Reference Rules\n\nNo rules yet.\n"
        refs = _parse_cross_refs(content)
        assert refs == []


class TestLoadSchema:
    def test_load_from_file(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "schema.md").write_text(SAMPLE_SCHEMA, encoding="utf-8")

        schema = load_schema(tmp_path)
        assert "Architecture" in schema.taxonomy
        assert schema.is_deprecated("old-api")
        assert not schema.is_deprecated("api-gateway-design")
        assert schema.find_category("api-gateway-design") == "Architecture"
        assert schema.find_category("nonexistent") is None

    def test_load_missing_file(self, tmp_path):
        schema = load_schema(tmp_path)
        assert schema.taxonomy == {}
        assert schema.all_known_slugs == set()

    def test_all_known_slugs(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "schema.md").write_text(SAMPLE_SCHEMA, encoding="utf-8")

        schema = load_schema(tmp_path)
        slugs = schema.all_known_slugs
        assert "api-gateway-design" in slugs
        assert "microservice-patterns" in slugs
        assert "db-migration-strategy" in slugs


class TestUpdateSchema:
    def test_add_new_topics(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "schema.md").write_text(SAMPLE_SCHEMA, encoding="utf-8")

        schema = load_schema(tmp_path)
        update_schema(tmp_path, ["new-concept", "another-concept"], schema)

        content = (wiki_dir / "schema.md").read_text(encoding="utf-8")
        assert "- new-concept" in content
        assert "- another-concept" in content

    def test_skip_existing_topics(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "schema.md").write_text(SAMPLE_SCHEMA, encoding="utf-8")

        schema = load_schema(tmp_path)
        update_schema(tmp_path, ["api-gateway-design"], schema)

        content = (wiki_dir / "schema.md").read_text(encoding="utf-8")
        taxonomy_section = content[content.index("## Topic Taxonomy"):content.index("## Naming")]
        assert taxonomy_section.count("api-gateway-design") == 1

    def test_skip_deprecated_topics(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "schema.md").write_text(SAMPLE_SCHEMA, encoding="utf-8")

        schema = load_schema(tmp_path)
        update_schema(tmp_path, ["old-api"], schema)

        content = (wiki_dir / "schema.md").read_text(encoding="utf-8")
        assert "### Uncategorized" in content
        uncategorized_section = content[content.index("### Uncategorized"):]
        assert "- old-api" not in uncategorized_section
