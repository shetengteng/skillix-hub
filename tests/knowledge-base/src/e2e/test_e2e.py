"""Knowledge Base Skill 端到端测试。

完整流程：创建样本文件 → index → compile dry-run → 手动创建 concepts → finalize
验证 runtime 目录下所有产出文件的格式和内容。
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = PROJECT_ROOT / "skills" / "knowledge-base"
RUNTIME_DIR = PROJECT_ROOT / "tests" / "knowledge-base" / "testdata" / "runtime"

sys.path.insert(0, str(SKILL_DIR))

from src.commands._common import A, ensure_data_dirs
from src.indexer import (
    read_index, write_index, generate_id, compute_hash,
    extract_title, detect_type, infer_category, set_project_root,
)
from src.scanner import build_pending_list, scan_entry, detect_changes
from src.compiler import _compile_finalize


SAMPLE_CONCEPTS = [
    {
        "filename": "sample-architecture.md",
        "content": """---
id: sample-architecture
title: 示例架构设计
category: architecture
tags: [设计模式, 架构]
sources: [{src_id_0}]
related: [sample-testing]
updated_at: 2026-04-08T00:00:00Z
---

# 示例架构设计

这是一个用于 E2E 测试的示例概念条目。

## 核心要点

- 三层架构：索引层、编译层、Wiki 层
- 增量编译支持

## 关联概念

- [[示例测试策略]] — 架构验证方式

## 来源资料

- [设计文档](source://{src_id_0})
""",
    },
    {
        "filename": "sample-testing.md",
        "content": """---
id: sample-testing
title: 示例测试策略
category: testing
tags: [测试, 质量]
sources: [{src_id_1}]
related: [sample-architecture]
updated_at: 2026-04-08T00:00:00Z
---

# 示例测试策略

端到端测试验证完整编译流程。

## 核心要点

- 单元测试：隔离沙箱
- E2E 测试：真实数据流

## 关联概念

- [[示例架构设计]] — 被测对象

## 来源资料

- [测试指南](source://{src_id_1})
""",
    },
]


@pytest.fixture(scope="module")
def sample_dir(tmp_path_factory):
    """创建样本源文件目录。"""
    d = tmp_path_factory.mktemp("e2e_sources") / "design" / "e2e-test"
    d.mkdir(parents=True)
    (d / "architecture.md").write_text(
        "# 架构设计文档\n\n详细的系统架构说明。\n\n## 分层\n\n- 索引层\n- 编译层\n- Wiki 层\n"
    )
    (d / "testing-guide.md").write_text(
        "# 测试指南\n\n如何编写有效的测试。\n\n## 策略\n\n- 单元测试\n- 集成测试\n- E2E 测试\n"
    )
    (d / "config.yaml").write_text("name: e2e-test\nversion: 1.0\n")
    return d


@pytest.fixture(scope="module", autouse=True)
def clean_runtime():
    """每次 E2E 模块运行前清空 runtime 目录。"""
    if RUNTIME_DIR.exists():
        shutil.rmtree(RUNTIME_DIR)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    ensure_data_dirs(RUNTIME_DIR)
    yield
    # 保留 runtime 供用户查看


class TestE2EIndexFlow:
    """阶段 1：索引流程。"""

    def test_index_sample_files(self, sample_dir):
        set_project_root(sample_dir.parent.parent)

        entries = []
        for f in sorted(sample_dir.rglob("*")):
            if f.is_file():
                abs_path = str(f.resolve())
                entry_type = detect_type(abs_path)
                entries.append({
                    "id": generate_id(),
                    "title": extract_title(abs_path, entry_type),
                    "type": entry_type,
                    "path": abs_path,
                    "tags": ["e2e-test"],
                    "category": infer_category(abs_path),
                    "summary": "",
                    "content_hash": compute_hash(abs_path, entry_type),
                    "created_at": "2026-04-08T00:00:00Z",
                    "updated_at": "2026-04-08T00:00:00Z",
                    "compiled": False,
                })

        write_index(RUNTIME_DIR, entries)
        stored = read_index(RUNTIME_DIR)

        assert len(stored) == 3
        types = {e["type"] for e in stored}
        assert "markdown" in types
        assert "config" in types

    def test_index_jsonl_format(self):
        index_file = RUNTIME_DIR / "raw" / "index.jsonl"
        assert index_file.exists()
        lines = index_file.read_text().strip().split("\n")
        for line in lines:
            entry = json.loads(line)
            assert "id" in entry
            assert "title" in entry
            assert "type" in entry
            assert "path" in entry
            assert "content_hash" in entry
            assert "compiled" in entry
            assert entry["compiled"] is False


class TestE2EScanFlow:
    """阶段 2：扫描流程。"""

    def test_detect_changes_all_new(self):
        changes = detect_changes(RUNTIME_DIR)
        assert len(changes["new"]) == 3
        assert len(changes["changed"]) == 0

    def test_build_pending_list(self):
        pending = build_pending_list(RUNTIME_DIR, full=False)
        assert len(pending) == 3
        for item in pending:
            assert "id" in item
            assert "content_preview" in item
            assert item["status"] == "ok"

    def test_scan_individual_entry(self):
        entries = read_index(RUNTIME_DIR)
        md_entry = next(e for e in entries if e["type"] == "markdown")
        result = scan_entry(md_entry)
        assert result["status"] == "ok"
        assert len(result["content_preview"]) > 0


class TestE2ECompileFlow:
    """阶段 3：编译流程（模拟 LLM 输出 + finalize）。"""

    def test_create_concept_files(self):
        entries = read_index(RUNTIME_DIR)
        src_ids = [e["id"] for e in entries if e["type"] == "markdown"]

        concepts_dir = RUNTIME_DIR / "wiki" / "concepts"
        concepts_dir.mkdir(parents=True, exist_ok=True)

        for i, concept in enumerate(SAMPLE_CONCEPTS):
            content = concept["content"]
            content = content.replace("{src_id_0}", src_ids[0] if len(src_ids) > 0 else "kb-test-000")
            content = content.replace("{src_id_1}", src_ids[1] if len(src_ids) > 1 else "kb-test-001")
            (concepts_dir / concept["filename"]).write_text(content)

        files = list(concepts_dir.glob("*.md"))
        assert len(files) == 2

    def test_compile_finalize(self):
        _compile_finalize(RUNTIME_DIR)

        assert (RUNTIME_DIR / "wiki" / "graph.json").exists()
        assert (RUNTIME_DIR / "wiki" / "index.md").exists()
        assert (RUNTIME_DIR / "compile" / "history.jsonl").exists()
        assert not (RUNTIME_DIR / "compile" / "pending.json").exists()
        assert not (RUNTIME_DIR / "wiki" / "backlinks.json").exists()

    def test_graph_json_format(self):
        graph = json.loads((RUNTIME_DIR / "wiki" / "graph.json").read_text())
        assert "nodes" in graph
        assert "edges" in graph

        concept_nodes = [n for n in graph["nodes"] if n["type"] == "concept"]
        source_nodes = [n for n in graph["nodes"] if n["type"] == "source"]
        assert len(concept_nodes) == 2
        assert len(source_nodes) >= 1

        describes_edges = [e for e in graph["edges"] if e["relation"] == "describes"]
        related_edges = [e for e in graph["edges"] if e["relation"] == "related_to"]
        assert len(describes_edges) >= 2
        assert len(related_edges) >= 2

        for node in graph["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "type" in node
        for edge in graph["edges"]:
            assert "from" in edge
            assert "to" in edge
            assert "relation" in edge

    def test_index_md_format(self):
        content = (RUNTIME_DIR / "wiki" / "index.md").read_text()
        assert "# 知识地图" in content
        assert "示例架构设计" in content
        assert "示例测试策略" in content
        assert "concepts/" in content

    def test_category_indexes(self):
        cats_dir = RUNTIME_DIR / "wiki" / "categories"
        assert cats_dir.exists()
        cat_files = list(cats_dir.glob("*.md"))
        assert len(cat_files) >= 2

        for f in cat_files:
            content = f.read_text()
            assert content.startswith("# ")
            assert "../concepts/" in content

    def test_history_jsonl_format(self):
        history_file = RUNTIME_DIR / "compile" / "history.jsonl"
        lines = history_file.read_text().strip().split("\n")
        assert len(lines) >= 1
        record = json.loads(lines[-1])
        assert "timestamp" in record
        assert "concepts_count" in record
        assert record["action"] == "finalize"
        assert record["concepts_count"] == 2

    def test_compiled_flag_updated(self):
        entries = read_index(RUNTIME_DIR)
        md_entries = [e for e in entries if e["type"] == "markdown"]
        compiled_count = sum(1 for e in md_entries if e.get("compiled"))
        assert compiled_count >= 1


class TestE2EDataStructure:
    """阶段 4：验证最终目录结构。"""

    def test_runtime_dir_structure(self):
        assert (RUNTIME_DIR / "raw").is_dir()
        assert (RUNTIME_DIR / "raw" / "index.jsonl").is_file()
        assert not (RUNTIME_DIR / "raw" / "cache").exists()

        assert (RUNTIME_DIR / "wiki").is_dir()
        assert (RUNTIME_DIR / "wiki" / "index.md").is_file()
        assert (RUNTIME_DIR / "wiki" / "graph.json").is_file()
        assert (RUNTIME_DIR / "wiki" / "concepts").is_dir()
        assert (RUNTIME_DIR / "wiki" / "categories").is_dir()
        assert not (RUNTIME_DIR / "wiki" / "backlinks.json").exists()

        assert (RUNTIME_DIR / "compile").is_dir()
        assert (RUNTIME_DIR / "compile" / "history.jsonl").is_file()
        assert not (RUNTIME_DIR / "compile" / "pending.json").exists()

    def test_no_stale_artifacts(self):
        """确认没有已废弃的数据产物。"""
        assert not (RUNTIME_DIR / "raw" / "cache").exists()
        assert not (RUNTIME_DIR / "wiki" / "backlinks.json").exists()
