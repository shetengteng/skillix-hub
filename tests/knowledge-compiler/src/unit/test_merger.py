"""Tests for merger.py (section-level merge)."""

import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))

from src.merger import (
    parse_sections,
    merge_sections,
    render_sections,
    generate_related_section,
    _extract_user_paragraphs,
    Section,
)


SAMPLE_BODY = """
# Test Concept

> A one-liner summary.

## Summary
<!-- coverage: high -->

This is the summary. [source: raw/test.md]

## Key Decisions
<!-- coverage: medium -->

Decision content. [source: raw/decisions/dec1.md]

User added note about deployment.

## Gotchas
<!-- coverage: low -->

待编译。

## Related

- [[other-concept]]

## Sources
- [source: raw/test.md]
"""


class TestParseSections:
    def test_parses_all_sections(self):
        sections = parse_sections(SAMPLE_BODY)
        headings = [s.heading for s in sections if s.heading]
        assert "## Summary" in headings
        assert "## Key Decisions" in headings
        assert "## Gotchas" in headings
        assert "## Related" in headings
        assert "## Sources" in headings

    def test_header_section(self):
        sections = parse_sections(SAMPLE_BODY)
        header = sections[0]
        assert header.heading == ""
        assert "Test Concept" in header.body

    def test_compiler_generated_detection(self):
        sections = parse_sections(SAMPLE_BODY)
        sec_map = {s.heading: s for s in sections}
        assert sec_map["## Summary"].is_compiler_generated is True
        assert sec_map["## Gotchas"].is_compiler_generated is False

    def test_auto_managed_detection(self):
        sections = parse_sections(SAMPLE_BODY)
        sec_map = {s.heading: s for s in sections}
        assert sec_map["## Related"].is_auto_managed is True
        assert sec_map["## Sources"].is_auto_managed is True
        assert sec_map["## Summary"].is_auto_managed is False

    def test_has_content(self):
        sections = parse_sections(SAMPLE_BODY)
        sec_map = {s.heading: s for s in sections}
        assert sec_map["## Summary"].has_content is True
        assert sec_map["## Gotchas"].has_content is False


class TestMergeSections:
    def test_preserves_user_edited_section(self):
        """用户手工编辑的 section 应被保留。"""
        old = [
            Section("", "# Title\n> Summary."),
            Section("## Summary", "\n<!-- coverage: high -->\nOld content.\n", is_compiler_generated=False),
            Section("## My Notes", "\nUser wrote this manually.\n", is_compiler_generated=False),
        ]
        new = [
            Section("", "# Title\n> Summary."),
            Section("## Summary", "\n<!-- coverage: high -->\nNew compiled content. [source: raw/a.md]\n", is_compiler_generated=True),
        ]

        merged = merge_sections(old, new)
        sec_map = {s.heading: s for s in merged}
        assert "## My Notes" in sec_map
        assert "User wrote this manually" in sec_map["## My Notes"].body

    def test_updates_compiler_generated_section(self):
        """编译器生成的 section 应被新内容替换。"""
        old = [
            Section("## Summary", "\n<!-- coverage: low -->\nOld. [source: raw/a.md]\n", is_compiler_generated=True),
        ]
        new = [
            Section("## Summary", "\n<!-- coverage: high -->\nNew. [source: raw/a.md]\n", is_compiler_generated=True),
        ]

        merged = merge_sections(old, new)
        sec_map = {s.heading: s for s in merged}
        assert "New." in sec_map["## Summary"].body

    def test_preserves_user_paragraphs_in_compiler_section(self):
        """编译器 section 中用户添加的无 [source:] 段落应被保留。"""
        old = [
            Section("## Summary",
                    "\n<!-- coverage: high -->\nCompiled. [source: raw/a.md]\n\nUser added insight.\n",
                    is_compiler_generated=True),
        ]
        new = [
            Section("## Summary",
                    "\n<!-- coverage: high -->\nNew compiled. [source: raw/a.md]\n",
                    is_compiler_generated=True),
        ]

        merged = merge_sections(old, new)
        sec_map = {s.heading: s for s in merged}
        assert "User added insight" in sec_map["## Summary"].body
        assert "New compiled" in sec_map["## Summary"].body

    def test_auto_managed_replaced(self):
        """Related/Sources 等自动管理 section 应用新版替换。"""
        old = [
            Section("## Related", "\n- [[old-concept]]\n", is_auto_managed=True),
        ]
        new = [
            Section("## Related", "\n- [[new-concept]]\n", is_auto_managed=True),
        ]

        merged = merge_sections(old, new)
        sec_map = {s.heading: s for s in merged}
        assert "new-concept" in sec_map["## Related"].body
        assert "old-concept" not in sec_map["## Related"].body

    def test_new_section_appended(self):
        """新文章独有的 section 应被追加。"""
        old = [Section("## Summary", "\nOld.\n")]
        new = [
            Section("## Summary", "\nNew. [source: raw/a.md]\n", is_compiler_generated=True),
            Section("## New Section", "\nFresh content. [source: raw/b.md]\n", is_compiler_generated=True),
        ]

        merged = merge_sections(old, new)
        headings = [s.heading for s in merged]
        assert "## New Section" in headings

    def test_old_only_user_section_preserved(self):
        """旧文章独有的用户 section 应被保留。"""
        old = [
            Section("## Summary", "\nCompiled. [source: raw/a.md]\n", is_compiler_generated=True),
            Section("## Team Notes", "\nImportant team context.\n"),
        ]
        new = [
            Section("## Summary", "\nUpdated. [source: raw/a.md]\n", is_compiler_generated=True),
        ]

        merged = merge_sections(old, new)
        headings = [s.heading for s in merged]
        assert "## Team Notes" in headings


class TestRenderSections:
    def test_roundtrip(self):
        body = "# Title\n\n## Summary\nContent.\n\n## Related\n- [[a]]\n"
        sections = parse_sections(body)
        rendered = render_sections(sections)
        assert "## Summary" in rendered
        assert "## Related" in rendered

    def test_preserves_content(self):
        sections = [
            Section("", "# Title"),
            Section("## Summary", "\nContent here.\n"),
        ]
        rendered = render_sections(sections)
        assert "# Title" in rendered
        assert "Content here." in rendered


class TestGenerateRelatedSection:
    def test_generates_links(self):
        result = generate_related_section(["api-gateway", "error-handling"])
        assert "[[api-gateway]]" in result
        assert "[[error-handling]]" in result

    def test_empty_list(self):
        result = generate_related_section([])
        assert result == ""

    def test_sorted_output(self):
        result = generate_related_section(["zebra", "alpha", "middle"])
        lines = [l for l in result.strip().split("\n") if l.startswith("- ")]
        assert "alpha" in lines[0]
        assert "zebra" in lines[2]


class TestExtractUserParagraphs:
    def test_extracts_user_content(self):
        body = "\n<!-- coverage: high -->\nCompiled. [source: raw/a.md]\n\nUser note here.\n"
        result = _extract_user_paragraphs(body)
        assert "User note here" in result
        assert "[source:" not in result

    def test_skips_coverage_and_stub(self):
        body = "\n<!-- coverage: low -->\n\n待编译。\n"
        result = _extract_user_paragraphs(body)
        assert result == ""

    def test_empty_body(self):
        result = _extract_user_paragraphs("")
        assert result == ""
