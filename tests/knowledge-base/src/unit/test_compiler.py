"""编译流程模块单元测试。"""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))

from src.compiler import _load_existing_concepts, _parse_frontmatter, _compile_finalize
from src.indexer import read_index, write_index


class TestParseFrontmatter:
    def test_valid_frontmatter(self, tmp_path):
        md = tmp_path / "concept.md"
        md.write_text(
            "---\n"
            "id: concept-test\n"
            "title: Test Concept\n"
            "category: testing\n"
            "tags: [unit, test]\n"
            "sources: [kb-001, kb-002]\n"
            "related: [concept-other]\n"
            "---\n"
            "\n# Test Concept\n\nContent here.\n"
        )
        meta = _parse_frontmatter(md)
        assert meta is not None
        assert meta["id"] == "concept-test"
        assert meta["title"] == "Test Concept"
        assert meta["category"] == "testing"
        assert isinstance(meta["tags"], list)
        assert "unit" in meta["tags"]

    def test_no_frontmatter(self, tmp_path):
        md = tmp_path / "no_fm.md"
        md.write_text("# Just a heading\n\nNo frontmatter.\n")
        assert _parse_frontmatter(md) is None

    def test_nonexistent_file(self, tmp_path):
        assert _parse_frontmatter(tmp_path / "nope.md") is None


class TestLoadExistingConcepts:
    def test_empty_dir(self, data_dir):
        concepts = _load_existing_concepts(data_dir)
        assert concepts == []

    def test_with_concepts(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        for i in range(3):
            (concepts_dir / f"concept-{i}.md").write_text(
                f"---\nid: concept-{i}\ntitle: Concept {i}\n---\n\n# Concept {i}\n"
            )
        concepts = _load_existing_concepts(data_dir)
        assert len(concepts) == 3


class TestCompileFinalize:
    def test_builds_backlinks_and_graph(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        (concepts_dir / "concept-a.md").write_text(
            "---\nid: concept-a\ntitle: Concept A\n"
            "category: test\ntags: [a]\nsources: [kb-001]\n"
            "related: [concept-b]\n---\n\n# Concept A\n"
        )
        (concepts_dir / "concept-b.md").write_text(
            "---\nid: concept-b\ntitle: Concept B\n"
            "category: test\ntags: [b]\nsources: [kb-002]\n"
            "related: [concept-a]\n---\n\n# Concept B\n"
        )

        entries = [
            {"id": "kb-001", "type": "markdown", "path": "/a.md",
             "compiled": False, "category": "test",
             "updated_at": "2026-01-01T00:00:00Z"},
            {"id": "kb-002", "type": "markdown", "path": "/b.md",
             "compiled": False, "category": "test",
             "updated_at": "2026-01-01T00:00:00Z"},
        ]
        write_index(data_dir, entries)

        class FakeArgs:
            pass
        _compile_finalize(data_dir)

        backlinks_file = data_dir / "wiki" / "backlinks.json"
        assert backlinks_file.exists()
        bl = json.loads(backlinks_file.read_text())
        assert "concept-a" in bl
        assert "concept-b" in bl["concept-a"]["referenced_by"]

        graph_file = data_dir / "wiki" / "graph.json"
        assert graph_file.exists()
        graph = json.loads(graph_file.read_text())
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 2

        index_md = data_dir / "wiki" / "index.md"
        assert index_md.exists()
        content = index_md.read_text()
        assert "Concept A" in content

        history_file = data_dir / "compile" / "history.jsonl"
        assert history_file.exists()

    def test_marks_compiled(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        (concepts_dir / "concept-x.md").write_text(
            "---\nid: concept-x\ntitle: X\n"
            "sources: [kb-src-1]\n---\n\n# X\n"
        )

        entries = [
            {"id": "kb-src-1", "type": "markdown", "path": "/x.md",
             "compiled": False, "updated_at": "2026-01-01T00:00:00Z"},
            {"id": "kb-src-2", "type": "markdown", "path": "/y.md",
             "compiled": False, "updated_at": "2026-01-01T00:00:00Z"},
        ]
        write_index(data_dir, entries)

        _compile_finalize(data_dir)

        entries = read_index(data_dir)
        compiled_ids = {e["id"] for e in entries if e.get("compiled")}
        assert "kb-src-1" in compiled_ids
        assert "kb-src-2" not in compiled_ids

    def test_empty_concepts_dir(self, data_dir, capsys):
        _compile_finalize(data_dir)
        captured = capsys.readouterr()
        assert "没有概念条目" in captured.out
