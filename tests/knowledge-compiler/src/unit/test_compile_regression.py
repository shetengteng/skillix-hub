"""Compile regression tests — 重编译场景验证。

验证关键场景：
1. 重编译时用户手工编辑被保留
2. frontmatter 生命周期正确 (created/updated/compile_count)
3. section merge 策略正确
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))

from src.compiler import create_stub_article, _parse_frontmatter, _render_frontmatter
from src.merger import parse_sections, merge_sections, render_sections


class TestFrontmatterLifecycle:
    def test_created_preserved_on_recompile(self, kc_root, sample_docs):
        """重编译时 created 日期应保持不变。"""
        files = [sample_docs["transformer"]]
        first = create_stub_article("transformer-arch", files, kc_root)
        meta1, _ = _parse_frontmatter(first)

        second = create_stub_article("transformer-arch", files, kc_root, first)
        meta2, _ = _parse_frontmatter(second)

        assert meta2["created"] == meta1["created"]

    def test_updated_changes_on_recompile(self, kc_root, sample_docs):
        """重编译时 updated 应为当前日期。"""
        files = [sample_docs["transformer"]]
        stub = create_stub_article("transformer-arch", files, kc_root)
        meta, _ = _parse_frontmatter(stub)
        assert meta["updated"] == date.today().isoformat()

    def test_compile_count_increments(self, kc_root, sample_docs):
        """每次编译 compile_count 应递增。"""
        files = [sample_docs["transformer"]]
        first = create_stub_article("transformer-arch", files, kc_root)
        meta1, _ = _parse_frontmatter(first)
        assert meta1["compile_count"] == 1

        second = create_stub_article("transformer-arch", files, kc_root, first)
        meta2, _ = _parse_frontmatter(second)
        assert meta2["compile_count"] == 2

        third = create_stub_article("transformer-arch", files, kc_root, second)
        meta3, _ = _parse_frontmatter(third)
        assert meta3["compile_count"] == 3

    def test_title_preserved_on_recompile(self, kc_root, sample_docs):
        """用户修改 title 后重编译应保留。"""
        files = [sample_docs["transformer"]]
        first = create_stub_article("transformer-arch", files, kc_root)
        meta, body = _parse_frontmatter(first)
        meta["title"] = "Custom Title By User"
        modified = _render_frontmatter(meta) + "\n" + body

        second = create_stub_article("transformer-arch", files, kc_root, modified)
        meta2, _ = _parse_frontmatter(second)
        assert meta2["title"] == "Custom Title By User"


class TestUserEditPreservation:
    def test_user_section_preserved(self):
        """用户手工添加的 section 应在 merge 后保留。"""
        old_body = """
# Test

## Summary
<!-- coverage: low -->

待编译。

## User Notes

This is my personal analysis of the problem.
It took me 3 days to figure this out.

## Sources
- [source: raw/test.md]
"""
        new_body = """
# Test

## Summary
<!-- coverage: high -->

New compiled summary. [source: raw/test.md]

## Sources
- [source: raw/test.md]
"""
        old_sections = parse_sections(old_body)
        new_sections = parse_sections(new_body)
        merged = merge_sections(old_sections, new_sections)
        result = render_sections(merged)

        assert "User Notes" in result
        assert "personal analysis" in result
        assert "New compiled summary" in result

    def test_user_paragraph_in_compiler_section_preserved(self):
        """编译器 section 中用户添加的段落（无 [source:]）应被保留。"""
        old_body = """
# Test

## Summary
<!-- coverage: high -->

Compiled content. [source: raw/test.md]

I noticed this also applies to caching scenarios.

## Sources
- [source: raw/test.md]
"""
        new_body = """
# Test

## Summary
<!-- coverage: high -->

Updated compiled content. [source: raw/test.md]

## Sources
- [source: raw/test.md]
"""
        old_sections = parse_sections(old_body)
        new_sections = parse_sections(new_body)
        merged = merge_sections(old_sections, new_sections)
        result = render_sections(merged)

        assert "Updated compiled content" in result
        assert "caching scenarios" in result

    def test_empty_user_section_not_blocking(self):
        """空的用户 section 不应阻止编译器更新。"""
        old_body = """
# Test

## Summary
<!-- coverage: low -->

待编译。

## Sources
"""
        new_body = """
# Test

## Summary
<!-- coverage: high -->

Real content. [source: raw/test.md]

## Sources
- [source: raw/test.md]
"""
        old_sections = parse_sections(old_body)
        new_sections = parse_sections(new_body)
        merged = merge_sections(old_sections, new_sections)
        result = render_sections(merged)

        assert "Real content" in result


class TestSourcesUpdate:
    def test_sources_updated_on_recompile(self, kc_root, sample_docs):
        """重编译时 sources 列表应更新为最新来源。"""
        files1 = [sample_docs["transformer"]]
        first = create_stub_article("test", files1, kc_root)
        meta1, _ = _parse_frontmatter(first)
        assert len(meta1["sources"]) == 1

        files2 = [sample_docs["transformer"], sample_docs["rag"]]
        second = create_stub_article("test", files2, kc_root, first)
        meta2, _ = _parse_frontmatter(second)
        assert len(meta2["sources"]) == 2
