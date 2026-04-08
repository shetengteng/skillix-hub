"""浏览与搜索模块单元测试。"""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))

from src.indexer import write_index
from src.searcher import _match_score, _text_match_score


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


class TestMatchScore:
    def test_title_match(self):
        entry = {"title": "Memory Architecture", "tags": [], "category": "memory", "path": "/a.md"}
        assert _match_score("memory", entry) > 0

    def test_tag_match(self):
        entry = {"title": "Doc", "tags": ["architecture"], "category": "test", "path": "/a.md"}
        assert _match_score("architecture", entry) > 0

    def test_no_match(self):
        entry = {"title": "Unrelated", "tags": ["other"], "category": "misc", "path": "/a.md"}
        assert _match_score("zzzzz", entry) == 0

    def test_title_exact_scores_higher(self):
        entry = {"title": "memory architecture design", "tags": [], "category": "x", "path": "/a.md"}
        full_score = _match_score("memory architecture", entry)
        partial_score = _match_score("memory", entry)
        assert full_score > partial_score


class TestTextMatchScore:
    def test_exact_phrase(self):
        assert _text_match_score("hello world", "the hello world example") > 0

    def test_word_count(self):
        text = "memory memory memory other"
        assert _text_match_score("memory", text) >= 3

    def test_no_match(self):
        assert _text_match_score("zzzzz", "nothing relevant here") == 0


class TestSearchCmd:
    def test_search_finds_results(self, data_dir, populated_index, capsys):
        from src.searcher import cmd_search

        class FakeArgs:
            query = "Document"
            search_tag = None
            search_category = None

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "搜索结果" in captured.out

    def test_search_no_results(self, data_dir, capsys):
        write_index(data_dir, [])
        from src.searcher import cmd_search

        class FakeArgs:
            query = "nonexistent"
            search_tag = None
            search_category = None

        cmd_search(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "没有找到" in captured.out


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
