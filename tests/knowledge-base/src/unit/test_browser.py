"""浏览与搜索模块单元测试。"""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))

from src.indexer import write_index
from src.searcher import _parse_frontmatter, _load_concepts


class TestBrowseOverview:
    def test_empty_index(self, data_dir, capsys):
        from src.browser import _browse_overview
        _browse_overview(data_dir)
        captured = capsys.readouterr()
        assert "知识库为空" in captured.out

    def test_with_entries(self, data_dir, populated_index, capsys):
        from src.browser import _browse_overview
        _browse_overview(data_dir)
        captured = capsys.readouterr()
        assert "test-skill" in captured.out
        assert "5 个资料" in captured.out

    def test_with_wiki_index(self, data_dir, capsys):
        index_md = data_dir / "wiki" / "index.md"
        index_md.write_text("# 知识地图\n\nWiki content here.\n")
        from src.browser import _browse_overview
        _browse_overview(data_dir)
        captured = capsys.readouterr()
        assert "知识地图" in captured.out


class TestBrowseCategory:
    def test_existing_category(self, data_dir, populated_index, capsys):
        from src.browser import _browse_category
        _browse_category(data_dir, "test-skill")
        captured = capsys.readouterr()
        assert "test-skill" in captured.out
        assert "5 个" in captured.out

    def test_nonexistent_category(self, data_dir, populated_index, capsys):
        from src.browser import _browse_category
        _browse_category(data_dir, "nonexistent")
        captured = capsys.readouterr()
        assert "未找到分类" in captured.out


class TestSource:
    def test_existing_source(self, data_dir, populated_index, capsys):
        from src.browser import cmd_source

        class FakeArgs:
            id = "kb-test-000"

        cmd_source(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "Document 0" in captured.out
        assert "markdown" in captured.out

    def test_nonexistent_source(self, data_dir, capsys):
        write_index(data_dir, [])
        from src.browser import cmd_source

        class FakeArgs:
            id = "nonexistent"

        cmd_source(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "未找到" in captured.out


class TestParseFrontmatter:
    def test_with_frontmatter(self):
        text = "---\nid: test-concept\ntitle: Test Concept\ncategory: test\ntags: [a, b]\n---\n# Test\n"
        meta = _parse_frontmatter(text, "fallback")
        assert meta["id"] == "test-concept"
        assert meta["title"] == "Test Concept"
        assert meta["category"] == "test"
        assert "a" in meta["tags"]
        assert "b" in meta["tags"]

    def test_without_frontmatter(self):
        text = "# Just a Title\n\nSome content.\n"
        meta = _parse_frontmatter(text, "fallback-id")
        assert meta["id"] == "fallback-id"
        assert meta["title"] == "Just a Title"

    def test_empty_text(self):
        meta = _parse_frontmatter("", "fallback")
        assert meta["id"] == "fallback"
        assert meta["title"] == "fallback"


class TestLoadConcepts:
    def test_loads_concept_files(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        (concepts_dir / "c1.md").write_text(
            "---\nid: c1\ntitle: Concept One\ncategory: cat1\ntags: [x]\n---\n# Concept One\n"
        )
        (concepts_dir / "c2.md").write_text(
            "---\nid: c2\ntitle: Concept Two\ncategory: cat2\n---\n# Concept Two\n"
        )
        result = _load_concepts(concepts_dir)
        assert len(result) == 2
        ids = {c["id"] for c in result}
        assert "c1" in ids
        assert "c2" in ids

    def test_empty_dir(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        result = _load_concepts(concepts_dir)
        assert result == []


class TestSearchCmd:
    def _make_concepts(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        (concepts_dir / "mem-arch.md").write_text(
            "---\nid: mem-arch\ntitle: Memory 四层架构\ncategory: memory\ntags: [memory]\n---\n"
        )
        (concepts_dir / "kb-three.md").write_text(
            "---\nid: kb-three\ntitle: KB 三层架构\ncategory: knowledge-base\ntags: [kb]\n---\n"
        )

    def test_search_shows_knowledge_nav(self, data_dir, capsys):
        self._make_concepts(data_dir)
        from src.searcher import cmd_search

        class FakeArgs:
            query = "记忆"
            search_tag = None
            search_category = None

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "知识导航" in captured.out
        assert "mem-arch" in captured.out
        assert "kb-three" in captured.out

    def test_search_with_category_filter(self, data_dir, capsys):
        self._make_concepts(data_dir)
        from src.searcher import cmd_search

        class FakeArgs:
            query = ""
            search_tag = None
            search_category = "memory"

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "mem-arch" in captured.out
        assert "kb-three" not in captured.out

    def test_search_with_tag_filter(self, data_dir, capsys):
        self._make_concepts(data_dir)
        from src.searcher import cmd_search

        class FakeArgs:
            query = ""
            search_tag = "kb"
            search_category = None

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "kb-three" in captured.out
        assert "mem-arch" not in captured.out

    def test_search_empty_kb(self, data_dir, capsys):
        write_index(data_dir, [])
        from src.searcher import cmd_search

        class FakeArgs:
            query = "anything"
            search_tag = None
            search_category = None

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "知识库为空" in captured.out

    def test_search_fallback_to_raw_index(self, data_dir, populated_index, capsys):
        from src.searcher import cmd_search

        class FakeArgs:
            query = "test"
            search_tag = None
            search_category = None

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "原始索引" in captured.out
        assert "test-skill" in captured.out


class TestStatus:
    def test_status_output(self, data_dir, populated_index, capsys):
        from src.searcher import cmd_status

        class FakeArgs:
            pass

        cmd_status(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "状态总览" in captured.out
        assert "总条目:" in captured.out
        assert "5" in captured.out


class TestCheck:
    def test_all_valid(self, data_dir, populated_index, capsys):
        from src.searcher import cmd_check

        class FakeArgs:
            pass

        cmd_check(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "有效: 5" in captured.out
        assert "失效: 0" in captured.out

    def test_with_invalid(self, data_dir, capsys):
        entries = [
            {"id": "kb-bad", "title": "Bad", "type": "markdown",
             "path": "/nonexistent.md", "content_hash": "x", "compiled": True},
        ]
        write_index(data_dir, entries)

        from src.searcher import cmd_check

        class FakeArgs:
            pass

        cmd_check(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "失效: 1" in captured.out
