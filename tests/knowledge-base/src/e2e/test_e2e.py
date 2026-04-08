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
        assert len(lines) == 3

        required_fields = {"id", "title", "type", "path", "tags", "category",
                           "summary", "content_hash", "created_at", "updated_at", "compiled"}
        for line in lines:
            entry = json.loads(line)
            assert required_fields.issubset(entry.keys()), f"缺少字段: {required_fields - entry.keys()}"
            assert entry["id"].startswith("kb-"), f"ID 格式错误: {entry['id']}"
            assert entry["title"], "标题不能为空"
            assert entry["type"] in {"markdown", "config", "code", "text", "image", "dataset", "binary", "link", "repo", "directory"}
            assert entry["content_hash"], f"content_hash 不能为空: {entry['id']}"
            assert len(entry["content_hash"]) == 8, f"content_hash 应为 8 字符: {entry['content_hash']}"
            assert entry["compiled"] is False
            assert isinstance(entry["tags"], list)


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

        concept_ids = {n["id"] for n in concept_nodes}
        assert "sample-architecture" in concept_ids
        assert "sample-testing" in concept_ids

        for cn in concept_nodes:
            assert cn["label"], f"概念节点 label 不能为空: {cn['id']}"
            assert cn["category"], f"概念节点 category 不能为空: {cn['id']}"

        describes_edges = [e for e in graph["edges"] if e["relation"] == "describes"]
        related_edges = [e for e in graph["edges"] if e["relation"] == "related_to"]
        assert len(describes_edges) == 2
        assert len(related_edges) == 2

        node_ids = {n["id"] for n in graph["nodes"]}
        for edge in graph["edges"]:
            assert "from" in edge and "to" in edge and "relation" in edge
            assert edge["from"] in node_ids, f"边 from '{edge['from']}' 引用了不存在的节点"
            assert edge["to"] in node_ids, f"边 to '{edge['to']}' 引用了不存在的节点"

        arch_related = [e for e in related_edges if e["from"] == "sample-architecture"]
        assert any(e["to"] == "sample-testing" for e in arch_related), "architecture → testing 关联缺失"
        test_related = [e for e in related_edges if e["from"] == "sample-testing"]
        assert any(e["to"] == "sample-architecture" for e in test_related), "testing → architecture 关联缺失"

    def test_index_md_format(self):
        content = (RUNTIME_DIR / "wiki" / "index.md").read_text()
        assert content.startswith("# 知识地图"), "必须以 '# 知识地图' 开头"
        assert "2 个概念" in content, "概念数统计错误"
        assert "2 个分类" in content, "分类数统计错误"

        assert "## 分类导航" in content, "缺少分类导航区域"
        assert "[architecture](categories/architecture.md)" in content, "缺少 architecture 分类链接"
        assert "[testing](categories/testing.md)" in content, "缺少 testing 分类链接"

        assert "[示例架构设计](concepts/sample-architecture.md)" in content
        assert "[示例测试策略](concepts/sample-testing.md)" in content

        assert "## architecture" in content
        assert "## testing" in content

    def test_category_indexes(self):
        cats_dir = RUNTIME_DIR / "wiki" / "categories"
        assert cats_dir.exists()
        cat_files = {f.stem: f for f in cats_dir.glob("*.md")}
        assert "architecture" in cat_files, "缺少 architecture 分类索引"
        assert "testing" in cat_files, "缺少 testing 分类索引"

        arch_content = cat_files["architecture"].read_text()
        assert arch_content.startswith("# architecture"), "分类索引标题错误"
        assert "[示例架构设计](../concepts/sample-architecture.md)" in arch_content

        test_content = cat_files["testing"].read_text()
        assert test_content.startswith("# testing"), "分类索引标题错误"
        assert "[示例测试策略](../concepts/sample-testing.md)" in test_content

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
        assert len(md_entries) == 2

        compiled_md = [e for e in md_entries if e.get("compiled")]
        assert len(compiled_md) == 2, "两个 markdown 条目都应被标记为已编译"
        for e in compiled_md:
            assert e["updated_at"] != "2026-04-08T00:00:00Z", f"{e['id']} updated_at 应被更新"

        config_entries = [e for e in entries if e["type"] == "config"]
        assert len(config_entries) == 1
        assert config_entries[0].get("compiled") is False, "config 条目不应被标记为已编译"


    def test_concept_files_content(self):
        """验证 concept 文件的 frontmatter 和内容完整性。"""
        import re
        concepts_dir = RUNTIME_DIR / "wiki" / "concepts"

        for concept_file in concepts_dir.glob("*.md"):
            text = concept_file.read_text()
            match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
            assert match, f"{concept_file.name} 缺少 frontmatter"

            frontmatter = match.group(1)
            assert "id:" in frontmatter, f"{concept_file.name} frontmatter 缺少 id"
            assert "title:" in frontmatter, f"{concept_file.name} frontmatter 缺少 title"
            assert "category:" in frontmatter, f"{concept_file.name} frontmatter 缺少 category"
            assert "tags:" in frontmatter, f"{concept_file.name} frontmatter 缺少 tags"
            assert "sources:" in frontmatter, f"{concept_file.name} frontmatter 缺少 sources"

            body = text[match.end():]
            assert "# " in body, f"{concept_file.name} 缺少正文标题"
            assert len(body.strip()) > 50, f"{concept_file.name} 正文过短"

    def test_graph_edge_completeness(self):
        """验证图谱边覆盖所有 concept 的 sources 和 related 关系。"""
        graph = json.loads((RUNTIME_DIR / "wiki" / "graph.json").read_text())
        edges = graph["edges"]

        arch_described = [e for e in edges if e["to"] == "sample-architecture" and e["relation"] == "describes"]
        assert len(arch_described) == 1, "sample-architecture 应有 1 条 describes 边"

        test_described = [e for e in edges if e["to"] == "sample-testing" and e["relation"] == "describes"]
        assert len(test_described) == 1, "sample-testing 应有 1 条 describes 边"


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
