"""知识图谱与概念/分类管理模块单元测试。"""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))

from src.graph import _load_graph, _subgraph, _mermaid_id
from src.indexer import read_index, write_index


def _write_graph(data_dir, graph):
    graph_file = data_dir / "wiki" / "graph.json"
    graph_file.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")


SAMPLE_GRAPH = {
    "nodes": [
        {"id": "concept-a", "label": "A", "type": "concept", "category": "test"},
        {"id": "concept-b", "label": "B", "type": "concept", "category": "test"},
        {"id": "concept-c", "label": "C", "type": "concept", "category": "test"},
        {"id": "kb-001", "label": "Source 1", "type": "source", "category": "test"},
    ],
    "edges": [
        {"from": "kb-001", "to": "concept-a", "relation": "describes"},
        {"from": "concept-a", "to": "concept-b", "relation": "related_to"},
        {"from": "concept-b", "to": "concept-c", "relation": "related_to"},
    ],
}


class TestLoadGraph:
    def test_empty(self, data_dir):
        graph = _load_graph(data_dir)
        assert graph["nodes"] == []
        assert graph["edges"] == []

    def test_with_data(self, data_dir):
        _write_graph(data_dir, SAMPLE_GRAPH)
        graph = _load_graph(data_dir)
        assert len(graph["nodes"]) == 4
        assert len(graph["edges"]) == 3


class TestSubgraph:
    def test_center_depth_1(self):
        sub = _subgraph(SAMPLE_GRAPH, "concept-a", depth=1)
        node_ids = {n["id"] for n in sub["nodes"]}
        assert "concept-a" in node_ids
        assert "concept-b" in node_ids
        assert "kb-001" in node_ids
        assert "concept-c" not in node_ids

    def test_center_depth_2(self):
        sub = _subgraph(SAMPLE_GRAPH, "concept-a", depth=2)
        node_ids = {n["id"] for n in sub["nodes"]}
        assert "concept-c" in node_ids

    def test_nonexistent_center(self):
        sub = _subgraph(SAMPLE_GRAPH, "nonexistent", depth=2)
        assert len(sub["nodes"]) == 0


class TestMermaidId:
    def test_replaces_dashes(self):
        assert _mermaid_id("concept-test-name") == "concept_test_name"

    def test_replaces_dots(self):
        assert _mermaid_id("v1.2.3") == "v1_2_3"


class TestCategoryManagement:
    def test_category_rename(self, data_dir):
        entries = [
            {"id": "kb-1", "category": "old-name", "type": "markdown", "path": "/a.md"},
            {"id": "kb-2", "category": "old-name", "type": "markdown", "path": "/b.md"},
            {"id": "kb-3", "category": "other", "type": "markdown", "path": "/c.md"},
        ]
        write_index(data_dir, entries)

        from src.graph import _category_rename

        class FakeArgs:
            old_name = "old-name"
            new_name = "new-name"

        _category_rename(FakeArgs(), data_dir)

        got = read_index(data_dir)
        cats = [e["category"] for e in got]
        assert cats.count("new-name") == 2
        assert cats.count("other") == 1
        assert "old-name" not in cats

    def test_rename_nonexistent(self, data_dir, capsys):
        write_index(data_dir, [])

        from src.graph import _category_rename

        class FakeArgs:
            old_name = "nope"
            new_name = "new"

        _category_rename(FakeArgs(), data_dir)
        captured = capsys.readouterr()
        assert "未找到分类" in captured.out


class TestConceptManagement:
    def test_concept_remove(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        (concepts_dir / "concept-x.md").write_text("---\nid: concept-x\n---\n# X\n")

        from src.graph import _concept_remove

        class FakeArgs:
            concept_id = "concept-x"

        _concept_remove(FakeArgs(), data_dir)
        assert not (concepts_dir / "concept-x.md").exists()

    def test_concept_rename(self, data_dir):
        concepts_dir = data_dir / "wiki" / "concepts"
        (concepts_dir / "concept-y.md").write_text(
            "---\nid: concept-y\ntitle: Old Title\n---\n\n# Old Title\n"
        )

        from src.graph import _concept_rename

        class FakeArgs:
            concept_id = "concept-y"
            new_title = "New Title"

        _concept_rename(FakeArgs(), data_dir)

        content = (concepts_dir / "concept-y.md").read_text()
        assert "New Title" in content
        assert "Old Title" not in content
