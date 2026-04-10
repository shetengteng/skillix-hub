"""Tests for classifier.py (Phase 2)."""

from pathlib import Path

from src.classifier import classify, _title_to_slug, _extract_title


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
