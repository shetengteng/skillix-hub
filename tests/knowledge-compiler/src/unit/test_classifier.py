"""Tests for classifier.py (Phase 2)."""

from pathlib import Path

from src.classifier import (
    classify,
    _title_to_slug,
    _extract_title,
    _extract_preview,
    _resolve_deprecated,
    _find_best_match,
)
from src.schema import Schema


class TestTitleToSlug:
    def test_simple_title(self):
        assert _title_to_slug("Transformer Architecture") == "transformer-architecture"

    def test_with_special_chars(self):
        slug = _title_to_slug("RAG: Overview & Trade-offs")
        assert slug == "rag-overview--trade-offs" or "rag" in slug

    def test_chinese_title(self):
        slug = _title_to_slug("知识编译器设计")
        assert len(slug) > 0

    def test_empty_title(self):
        assert _title_to_slug("") == "untitled"


class TestExtractTitle:
    def test_h1_title(self):
        content = "# My Title\n\nSome content."
        assert _extract_title(content, "file.md") == "My Title"

    def test_no_h1_uses_filename(self):
        content = "Some content without heading."
        title = _extract_title(content, "my-design-doc.md")
        assert "My" in title or "Design" in title

    def test_skips_h2(self):
        content = "## Not This\n\n# This One\n"
        assert _extract_title(content, "f.md") == "This One"

    def test_frontmatter_ignored(self):
        content = "---\ntitle: FM Title\n---\n# Real Title\n"
        assert _extract_title(content, "f.md") == "Real Title"


class TestClassify:
    def test_classify_new_files(self, kc_root, sample_docs):
        files = list(sample_docs.values())
        topic_map = classify(files, kc_root)

        assert len(topic_map) == 3
        slugs = list(topic_map.keys())
        assert any("transformer" in s for s in slugs)
        assert any("rag" in s for s in slugs)
        assert any("postgresql" in s.lower() or "decision" in s for s in slugs)

    def test_classify_merges_existing(self, kc_root, sample_docs):
        concepts_dir = kc_root / "wiki" / "concepts"
        (concepts_dir / "transformer-architecture.md").write_text(
            "---\nid: transformer-architecture\ntitle: Transformer Architecture\n---\n# Transformer Architecture\n"
        )

        files = [sample_docs["transformer"]]
        topic_map = classify(files, kc_root)

        assert "transformer-architecture" in topic_map

    def test_classify_single_file(self, kc_root, sample_docs):
        files = [sample_docs["rag"]]
        topic_map = classify(files, kc_root)
        assert len(topic_map) == 1

    def test_classify_deprecated_slug_redirects(self, kc_root):
        """废弃主题自动映射到合并目标。"""
        schema_content = """## Topic Taxonomy

### Architecture
- api-gateway

### Uncategorized

## Deprecated Topics

| Old Slug | Merged Into | Date |
|----------|-------------|------|
| old-api-gateway | api-gateway | 2026-04-01 |
"""
        (kc_root / "wiki" / "schema.md").write_text(schema_content, encoding="utf-8")

        doc = kc_root / "raw" / "research" / "old-api-gateway.md"
        doc.write_text("# Old Api Gateway\n\nDeprecated content about api gateway.\n")

        topic_map = classify([doc], kc_root)
        assert "api-gateway" in topic_map
        assert "old-api-gateway" not in topic_map

    def test_classify_preview_matching(self, kc_root):
        """标题不匹配但 preview 含已有概念关键词时应匹配。"""
        concepts_dir = kc_root / "wiki" / "concepts"
        (concepts_dir / "error-handling.md").write_text(
            "---\nid: error-handling\ntitle: Error Handling\n---\n# Error Handling\n"
        )

        doc = kc_root / "raw" / "research" / "retry-strategy.md"
        doc.write_text(
            "# Retry Strategy\n\n"
            "When error handling fails, we need retry logic.\n"
            "The error and handling mechanism must be robust.\n"
        )

        topic_map = classify([doc], kc_root)
        assert "error-handling" in topic_map


class TestResolveDeprecated:
    def test_deprecated_returns_merged_target(self):
        schema = Schema(deprecated={"old-api": "new-api"})
        assert _resolve_deprecated("old-api", schema) == "new-api"

    def test_non_deprecated_returns_self(self):
        schema = Schema(deprecated={"old-api": "new-api"})
        assert _resolve_deprecated("new-api", schema) == "new-api"

    def test_empty_merge_target(self):
        schema = Schema(deprecated={"old-api": ""})
        assert _resolve_deprecated("old-api", schema) == "old-api"


class TestFindBestMatchWithPreview:
    def test_exact_match(self):
        existing = {"api-gateway": "API Gateway"}
        assert _find_best_match("api-gateway", "API Gateway", "", existing) == "api-gateway"

    def test_slug_word_overlap(self):
        existing = {"api-gateway-design": "API Gateway Design"}
        result = _find_best_match("api-gateway", "API Gateway", "", existing)
        assert result == "api-gateway-design"

    def test_preview_fallback(self):
        existing = {"error-handling": "Error Handling"}
        result = _find_best_match(
            "retry-strategy", "Retry Strategy",
            "This discusses error and handling approaches.", existing)
        assert result == "error-handling"

    def test_no_match(self):
        existing = {"api-gateway": "API Gateway"}
        result = _find_best_match("database-migration", "Database Migration", "unrelated", existing)
        assert result is None


class TestExtractPreview:
    def test_basic_preview(self):
        content = "Some content here about topics."
        preview = _extract_preview(content, 20)
        assert len(preview) <= 20
        assert preview == "Some content here ab"

    def test_skips_frontmatter(self):
        content = "---\ntitle: Test\n---\nActual content."
        preview = _extract_preview(content)
        assert "Actual content" in preview
        assert "title:" not in preview
