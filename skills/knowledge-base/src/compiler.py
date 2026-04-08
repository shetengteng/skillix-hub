"""编译流程编排：生成待编译清单、输出编译 prompt、后处理。"""

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .indexer import read_index, write_index
from .scanner import build_pending_list, detect_changes


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    prompt_file = PROMPTS_DIR / f"{name}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return ""


def cmd_compile(args, data_dir: Path):
    if args.dry_run:
        _compile_dry_run(args, data_dir)
    elif args.finalize:
        _compile_finalize(data_dir)
    else:
        _compile_prepare(args, data_dir)


def _compile_dry_run(args, data_dir: Path):
    """预览待编译清单。"""
    full = getattr(args, "full", False)
    pending = build_pending_list(data_dir, full=full)

    if not pending:
        print("✅ 没有待编译的条目")
        return

    by_cat = {}
    for item in pending:
        cat = item.get("category", "uncategorized")
        by_cat.setdefault(cat, []).append(item)

    print("=== Knowledge Base: 待编译清单 ===\n")
    for cat, items in sorted(by_cat.items()):
        print(f"📂 {cat} ({len(items)} 个)")
        for item in items:
            print(f"   {item['id']} | {item['title']}")
        print()

    print(f"共 {len(pending)} 个条目待编译\n")
    print("💡 下一步:")
    print("  - `kb compile` — 开始编译（生成 prompt 供 Agent 执行）")


def _backup_wiki(data_dir: Path):
    """编译前备份 wiki/ 到 wiki.bak/。"""
    wiki_dir = data_dir / "wiki"
    backup_dir = data_dir / "wiki.bak"
    if wiki_dir.exists() and any(wiki_dir.iterdir()):
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(wiki_dir, backup_dir)


def _compile_prepare(args, data_dir: Path):
    """准备编译：扫描内容、生成 pending.json、输出编译 prompt。"""
    _backup_wiki(data_dir)
    full = getattr(args, "full", False)
    target_id = getattr(args, "target_id", None)

    if target_id:
        entries = read_index(data_dir)
        matched = [e for e in entries if e["id"] == target_id]
        if not matched:
            print(f"❌ 未找到 ID: {target_id}")
            return
        from .scanner import scan_entry
        pending = [scan_entry(matched[0])]
    else:
        pending = build_pending_list(data_dir, full=full)

    if not pending:
        print("✅ 没有待编译的条目，知识库已是最新")
        return

    # 写入 pending.json
    pending_file = data_dir / "compile" / "pending.json"
    pending_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pending_file, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)

    # 读取已有概念
    existing_concepts = _load_existing_concepts(data_dir)

    # 生成编译 prompt
    prompt = _build_compile_prompt(pending, existing_concepts)

    print(f"=== Knowledge Base: 编译准备完成 ===\n")
    print(f"待编译: {len(pending)} 个条目")
    print(f"已有概念: {len(existing_concepts)} 个")
    print(f"待编译清单: {pending_file}\n")
    print("=" * 60)
    print("请按以下步骤完成编译：\n")
    print("【Step 2: 概念提取】\n")
    print(prompt)
    print("\n" + "=" * 60)
    print("\n完成概念提取和条目编写后，执行：")
    print("  `kb compile --finalize` — 更新反向链接和知识图谱")


def _build_compile_prompt(pending: list, existing_concepts: list) -> str:
    template = _load_prompt("extract_concepts")
    if not template:
        template = _default_extract_prompt()

    pending_text = ""
    for item in pending:
        pending_text += f"\n### {item['id']}: {item['title']}\n"
        pending_text += f"类型: {item['type']} | 分类: {item['category']}\n"
        tags = ", ".join(item.get("tags", []))
        if tags:
            pending_text += f"标签: {tags}\n"
        preview = item.get("content_preview", "")
        if preview:
            pending_text += f"\n{preview[:1500]}\n"

    existing_text = ""
    if existing_concepts:
        for c in existing_concepts:
            existing_text += f"- {c['id']}: {c.get('title', c['id'])}\n"
    else:
        existing_text = "（暂无已有概念）"

    result = template.replace("{{pending_list}}", pending_text)
    result = result.replace("{{existing_concepts}}", existing_text)
    return result


def _default_extract_prompt() -> str:
    return """请分析以下资料，提取关键概念并建立关系。

## 待分析资料

{{pending_list}}

## 已有概念（避免重复）

{{existing_concepts}}

## 输出要求

1. 从资料中提取关键概念（每个概念是一个可独立理解的知识单元）
2. 为每个概念编写 Wiki 条目（Markdown 格式，含 frontmatter）
3. 条目文件写入 `skills/knowledge-base-data/wiki/concepts/<concept-id>.md`

每个条目格式：

```markdown
---
id: concept-xxx
title: 概念名称
category: 分类
tags: [标签1, 标签2]
sources: [来源ID1, 来源ID2]
related: [关联概念ID1]
updated_at: 当前时间
---

# 概念名称

一段话概要。

## 核心要点

- 要点 1
- 要点 2

## 关联概念

- [[关联概念名]] — 关系说明

## 来源资料

- [资料标题](source://来源ID)
```

完成后执行 `python3 skills/knowledge-base/main.py compile --finalize` 更新索引。"""


def _load_existing_concepts(data_dir: Path) -> list:
    concepts_dir = data_dir / "wiki" / "concepts"
    if not concepts_dir.exists():
        return []

    concepts = []
    for md_file in concepts_dir.glob("*.md"):
        meta = _parse_frontmatter(md_file)
        if meta:
            concepts.append(meta)
    return concepts


def _parse_frontmatter(md_file: Path) -> dict | None:
    try:
        text = md_file.read_text(encoding="utf-8")
    except Exception:
        return None

    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None

    meta = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            meta[key] = value
    return meta


def _compile_finalize(data_dir: Path):
    """编译后处理：解析 Wiki 条目，构建反向链接和知识图谱。"""
    concepts_dir = data_dir / "wiki" / "concepts"
    if not concepts_dir.exists():
        print("⚠ wiki/concepts/ 目录为空，请先完成概念编写")
        return

    concept_files = list(concepts_dir.glob("*.md"))
    if not concept_files:
        print("⚠ 没有概念条目，请先完成概念编写")
        return

    # 解析所有概念条目
    concepts = []
    for md_file in concept_files:
        meta = _parse_frontmatter(md_file)
        if meta:
            meta["_file"] = str(md_file)
            concepts.append(meta)

    # 质量验证
    warnings = _validate_concepts(data_dir, concepts)
    if warnings:
        print(f"⚠ 概念质量检查发现 {len(warnings)} 个问题:\n")
        for w in warnings:
            print(f"   {w}")
        print()

    # 检测孤立概念
    orphans = _detect_orphan_concepts(data_dir, concepts)
    if orphans:
        print(f"⚠ 发现 {len(orphans)} 个孤立概念（来源已不存在）:\n")
        for o in orphans:
            print(f"   {o}")
        print()

    # 构建知识图谱
    graph = {"nodes": [], "edges": []}
    for c in concepts:
        graph["nodes"].append({
            "id": c.get("id", ""),
            "label": c.get("title", c.get("id", "")),
            "type": "concept",
            "category": c.get("category", ""),
        })

    # 添加 source 节点和边
    source_ids = set()
    for c in concepts:
        sources = c.get("sources", [])
        if isinstance(sources, str):
            sources = [sources]
        for sid in sources:
            if sid not in source_ids:
                source_ids.add(sid)
                graph["nodes"].append({
                    "id": sid, "label": sid, "type": "source", "category": "",
                })
            graph["edges"].append({
                "from": sid, "to": c.get("id", ""), "relation": "describes",
            })

        related = c.get("related", [])
        if isinstance(related, str):
            related = [related]
        for rid in related:
            graph["edges"].append({
                "from": c.get("id", ""), "to": rid, "relation": "related_to",
            })

    graph_file = data_dir / "wiki" / "graph.json"
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    # 重建知识地图 index.md
    _rebuild_index_md(data_dir, concepts)

    # 标记已编译
    _mark_compiled(data_dir, concepts)

    # 记录编译历史
    _record_history(data_dir, len(concepts))

    # 清理编译临时产物
    pending_file = data_dir / "compile" / "pending.json"
    if pending_file.exists():
        pending_file.unlink()

    print(f"=== Knowledge Base: 编译后处理完成 ===\n")
    print(f"概念条目: {len(concepts)} 个")
    print(f"知识图谱: {graph_file}")
    print(f"知识地图: {data_dir / 'wiki' / 'index.md'}")


def _rebuild_index_md(data_dir: Path, concepts: list):
    by_cat = {}
    for c in concepts:
        cat = c.get("category", "uncategorized")
        by_cat.setdefault(cat, []).append(c)

    lines = ["# 知识地图\n"]
    lines.append(f"> 共 {len(concepts)} 个概念 | {len(by_cat)} 个分类 | 最近更新: {datetime.now().strftime('%Y-%m-%d')}\n")

    lines.append("\n## 分类导航\n")
    for cat in sorted(by_cat.keys()):
        lines.append(f"- [{cat}](categories/{cat}.md) ({len(by_cat[cat])} 个概念)")

    for cat, items in sorted(by_cat.items()):
        lines.append(f"\n## {cat} ({len(items)} 个概念)\n")
        for c in items:
            title = c.get("title", c.get("id", ""))
            cid = c.get("id", "")
            lines.append(f"- [{title}](concepts/{cid}.md)")

    index_file = data_dir / "wiki" / "index.md"
    index_file.write_text("\n".join(lines), encoding="utf-8")

    # 同时生成分类索引
    cats_dir = data_dir / "wiki" / "categories"
    cats_dir.mkdir(parents=True, exist_ok=True)
    for cat, items in by_cat.items():
        cat_lines = [f"# {cat}\n"]
        for c in items:
            title = c.get("title", c.get("id", ""))
            cid = c.get("id", "")
            tags = c.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            tags_str = f" [{', '.join(tags)}]" if tags else ""
            cat_lines.append(f"- [{title}](../concepts/{cid}.md){tags_str}")
        cat_file = cats_dir / f"{cat}.md"
        cat_file.write_text("\n".join(cat_lines), encoding="utf-8")


def _mark_compiled(data_dir: Path, concepts: list):
    """标记已编译的索引条目。"""
    compiled_sources = set()
    for c in concepts:
        sources = c.get("sources", [])
        if isinstance(sources, str):
            sources = [sources]
        compiled_sources.update(sources)

    entries = read_index(data_dir)
    changed = False
    for entry in entries:
        if entry["id"] in compiled_sources and not entry.get("compiled"):
            entry["compiled"] = True
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            changed = True
    if changed:
        write_index(data_dir, entries)


def _record_history(data_dir: Path, concept_count: int, max_records: int = 50):
    history_file = data_dir / "compile" / "history.jsonl"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "concepts_count": concept_count,
        "action": "finalize",
    }
    lines = []
    if history_file.exists():
        lines = [l for l in history_file.read_text(encoding="utf-8").strip().split("\n") if l]
    lines.append(json.dumps(record, ensure_ascii=False))
    if len(lines) > max_records:
        lines = lines[-max_records:]
    history_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_concepts(data_dir: Path, concepts: list) -> list[str]:
    """验证概念条目的 frontmatter 质量。"""
    entries = read_index(data_dir)
    index_ids = {e["id"] for e in entries}
    concept_ids = {c.get("id", "") for c in concepts}
    warnings = []

    for c in concepts:
        cid = c.get("id", "")
        fname = Path(c.get("_file", "")).name

        if not cid:
            warnings.append(f"❌ {fname}: 缺少 id 字段")
        if not c.get("title"):
            warnings.append(f"❌ {fname}: 缺少 title 字段")
        if not c.get("category"):
            warnings.append(f"⚠ {cid or fname}: 缺少 category 字段")

        sources = c.get("sources", [])
        if isinstance(sources, str):
            sources = [sources]
        for sid in sources:
            if sid and sid not in index_ids:
                warnings.append(f"⚠ {cid}: source '{sid}' 不存在于索引中")

        related = c.get("related", [])
        if isinstance(related, str):
            related = [related]
        for rid in related:
            if rid and rid not in concept_ids:
                warnings.append(f"⚠ {cid}: related '{rid}' 引用的概念不存在")

    return warnings


def _detect_orphan_concepts(data_dir: Path, concepts: list) -> list[str]:
    """检测所有 sources 均不存在于索引中的孤立概念。"""
    entries = read_index(data_dir)
    index_ids = {e["id"] for e in entries}
    orphans = []

    for c in concepts:
        cid = c.get("id", "")
        sources = c.get("sources", [])
        if isinstance(sources, str):
            sources = [sources]
        if sources and all(sid not in index_ids for sid in sources if sid):
            orphans.append(f"{cid} (sources: {', '.join(sources)})")

    return orphans
