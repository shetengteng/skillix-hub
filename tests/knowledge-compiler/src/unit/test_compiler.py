"""Tests for compiler.py (Phase 3)."""

from pathlib import Path

from src.compiler import (
    generate_compile_prompt,
    create_stub_article,
    _parse_frontmatter,
    _render_frontmatter,
)


class TestParseFrontmatter:
    def test_parse_valid(self):
        content = '---\nid: "test"\ntitle: "Test"\n---\n# Body\n'
        meta, body = _parse_frontmatter(content)
        assert meta["id"] == "test"
        assert "# Body" in body

    def test_parse_no_frontmatter(self):
        content = "# Just Body\n"
        meta, body = _parse_frontmatter(content)
        assert meta == {}
        assert "# Just Body" in body

    def test_parse_empty(self):
        meta, body = _parse_frontmatter("")
        assert meta == {}


class TestCreateStubArticle:
    def test_stub_has_frontmatter(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        stub = create_stub_article("transformer-architecture", files, kc_root)

        assert "---" in stub
        assert 'id: "transformer-architecture"' in stub
        assert "sources:" in stub
        assert "raw/research/transformer.md" in stub

    def test_stub_has_coverage_tags(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        stub = create_stub_article("transformer-architecture", files, kc_root)

        assert "<!-- coverage: low -->" in stub

    def test_stub_has_source_refs(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        stub = create_stub_article("transformer-architecture", files, kc_root)

        assert "[source: raw/research/transformer.md]" in stub

    def test_stub_has_preview(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        stub = create_stub_article("transformer-architecture", files, kc_root)

        assert "Transformer" in stub
        assert "self-attention" in stub

    def test_stub_multiple_sources(self, kc_root, sample_docs):
        extra = kc_root / "raw" / "research" / "transformer2.md"
        extra.write_text("# More Transformer Info\n\nAdditional details.\n")

        files = [sample_docs["transformer"], extra]
        stub = create_stub_article("transformer-architecture", files, kc_root)

        assert "transformer.md" in stub
        assert "transformer2.md" in stub


class TestGenerateCompilePrompt:
    def test_prompt_contains_sources(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        prompt = generate_compile_prompt("transformer-architecture", files, kc_root)

        assert "raw/research/transformer.md" in prompt
        assert "self-attention" in prompt

    def test_prompt_contains_instructions(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        prompt = generate_compile_prompt("transformer-architecture", files, kc_root)

        assert "coverage: high" in prompt
        assert "coverage: medium" in prompt
        assert "coverage: low" in prompt

    def test_prompt_with_existing_article(self, kc_root, sample_docs):
        files = [sample_docs["transformer"]]
        existing = "# Old Article\n\nUser added this paragraph.\n"
        prompt = generate_compile_prompt(
            "transformer-architecture", files, kc_root, existing
        )

        assert "User added this paragraph" in prompt
        assert "保留" in prompt
