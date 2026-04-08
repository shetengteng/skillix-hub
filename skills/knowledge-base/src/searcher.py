"""搜索与状态管理模块：Agent-native 知识导航、健康检查。"""

import json
import os
from pathlib import Path

from .indexer import read_index, compute_hash, resolve_path


def cmd_search(args, data_dir: Path):
    """输出完整 Wiki 知识结构，供 Agent LLM 自主语义导航。"""
    query = args.query
    tag = getattr(args, "search_tag", None)
    category = getattr(args, "search_category", None)

    concepts_dir = data_dir / "wiki" / "concepts"
    concepts = _load_concepts(concepts_dir) if concepts_dir.exists() else []

    if tag:
        concepts = [c for c in concepts if tag in c.get("tags", [])]
    if category:
        concepts = [c for c in concepts if c.get("category") == category]

    if not concepts:
        entries = read_index(data_dir)
        if not entries:
            print("📭 知识库为空，请先添加资料并编译")
            print("\n💡 下一步:")
            print("  - `kb add <path>` — 添加资料")
            print("  - `kb import-project` — 导入项目 design/ 目录")
            return
        _show_raw_fallback(entries, query, tag, category)
        return

    by_cat: dict[str, list] = {}
    for c in concepts:
        cat = c.get("category", "uncategorized")
        by_cat.setdefault(cat, []).append(c)

    print("=== Knowledge Base: 知识导航 ===\n")
    if query:
        print(f"🔍 查询: {query}\n")

    for cat, items in sorted(by_cat.items()):
        print(f"📂 {cat} ({len(items)} 个概念)")
        for c in items:
            print(f"   💡 {c['id']} | {c['title']}")
        print()

    print(f"共 {len(concepts)} 个概念 | {len(by_cat)} 个分类\n")
    print("💡 根据查询意图，选择相关概念深入阅读:")
    print("  - `kb read <concept-id>` — 读取概念全文")
    print("  - `kb browse <category>` — 查看分类详情和资料列表")
    print("  - `kb graph --center <id> --depth 2` — 查看概念关联")


def _load_concepts(concepts_dir: Path) -> list:
    """从 wiki/concepts/*.md 的 frontmatter 中加载概念元数据。"""
    concepts = []
    for md_file in sorted(concepts_dir.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text, md_file.stem)
            concepts.append(meta)
        except Exception:
            continue
    return concepts


def _parse_frontmatter(text: str, fallback_id: str) -> dict:
    """解析 Markdown frontmatter（--- ... ---）。"""
    meta: dict = {"id": fallback_id, "title": fallback_id, "category": "uncategorized", "tags": []}
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        for line in lines:
            if line.startswith("# "):
                meta["title"] = line[2:].strip()
                break
        return meta

    in_fm = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm and ":" in stripped:
            key, val = stripped.split(":", 1)
            key, val = key.strip(), val.strip()
            if key == "id":
                meta["id"] = val
            elif key == "title":
                meta["title"] = val
            elif key == "category":
                meta["category"] = val
            elif key == "tags":
                val = val.strip("[]")
                meta["tags"] = [t.strip().strip("'\"") for t in val.split(",") if t.strip()]
    return meta


def _show_raw_fallback(entries: list, query: str, tag: str | None, category: str | None):
    """Wiki 未编译时，输出原始索引结构作为导航依据。"""
    if tag:
        entries = [e for e in entries if tag in e.get("tags", [])]
    if category:
        entries = [e for e in entries if e.get("category") == category]

    if not entries:
        print(f"📭 没有匹配的索引条目")
        return

    by_cat: dict[str, list] = {}
    for e in entries:
        cat = e.get("category", "uncategorized")
        by_cat.setdefault(cat, []).append(e)

    print("=== Knowledge Base: 知识导航（原始索引） ===\n")
    if query:
        print(f"🔍 查询: {query}\n")
    print("⚠ Wiki 尚未编译，显示原始索引结构。编译后可获得更丰富的概念导航。\n")

    for cat, items in sorted(by_cat.items()):
        print(f"📂 {cat} ({len(items)} 个资料)")
        for e in items:
            status = "✅" if e.get("compiled") else "⏳"
            print(f"   {status} {e['id']} | {e['title']}")
        print()

    print(f"共 {len(entries)} 个资料 | {len(by_cat)} 个分类\n")
    print("💡 下一步:")
    print("  - `kb source <source-id>` — 查看资料详情")
    print("  - `kb compile` — 编译生成概念索引后可获得更好的导航")


def cmd_status(args, data_dir: Path):
    entries = read_index(data_dir)

    total = len(entries)
    compiled = sum(1 for e in entries if e.get("compiled"))
    pending = total - compiled

    valid = 0
    invalid = 0
    for e in entries:
        if e["type"] == "link" or os.path.exists(resolve_path(e["path"])):
            valid += 1
        else:
            invalid += 1

    concepts_dir = data_dir / "wiki" / "concepts"
    concept_count = len(list(concepts_dir.glob("*.md"))) if concepts_dir.exists() else 0

    stale_count = _count_stale_sources(entries)

    graph_file = data_dir / "wiki" / "graph.json"
    has_graph = graph_file.exists()

    history_file = data_dir / "compile" / "history.jsonl"
    last_compile = "从未编译"
    if history_file.exists():
        try:
            lines = history_file.read_text(encoding="utf-8").strip().split("\n")
            if lines:
                import json
                last = json.loads(lines[-1])
                last_compile = last.get("timestamp", "未知")
        except Exception:
            pass

    print("=== Knowledge Base: 状态总览 ===\n")
    print(f"📊 索引统计")
    print(f"   总条目:     {total}")
    print(f"   已编译:     {compiled}")
    print(f"   待编译:     {pending}")
    print(f"   路径有效:   {valid}")
    print(f"   路径失效:   {invalid}")
    print(f"   来源已变更: {stale_count}")
    print()
    print(f"📚 Wiki 统计")
    print(f"   概念条目:   {concept_count}")
    print(f"   知识图谱:   {'✅ 已生成' if has_graph else '❌ 未生成'}")
    print(f"   最近编译:   {last_compile}")
    print()

    if invalid > 0:
        print("⚠ 存在失效路径，建议执行 `kb check` 检查详情")
    if stale_count > 0:
        print(f"🔄 有 {stale_count} 个已编译条目的来源已变更，概念可能过期")
        print(f"   执行 `kb compile` 重新编译以更新知识")
    if pending > 0:
        print(f"💡 有 {pending} 个待编译条目，执行 `kb compile` 开始编译")


def _count_stale_sources(entries: list) -> int:
    """统计已编译但来源内容已变更的条目数。"""
    count = 0
    for e in entries:
        if not e.get("compiled"):
            continue
        abs_path = resolve_path(e["path"])
        if e["type"] == "link" or not os.path.exists(abs_path):
            continue
        current_hash = compute_hash(abs_path, e["type"])
        if current_hash and current_hash != e.get("content_hash", ""):
            count += 1
    return count


def cmd_check(args, data_dir: Path):
    entries = read_index(data_dir)

    valid = []
    invalid = []
    changed = []

    for e in entries:
        abs_path = resolve_path(e["path"])
        if e["type"] == "link":
            valid.append(e)
            continue

        if not os.path.exists(abs_path):
            invalid.append(e)
            continue

        new_hash = compute_hash(abs_path, e["type"])
        if new_hash and new_hash != e.get("content_hash", ""):
            changed.append(e)
        else:
            valid.append(e)

    print("=== Knowledge Base: 路径检查 ===\n")

    if invalid:
        print(f"❌ 失效路径 ({len(invalid)} 个):\n")
        for e in invalid:
            print(f"   {e['id']} | {e['title']}")
            print(f"   路径: {e['path']}\n")

    if changed:
        print(f"🔄 内容已变更 ({len(changed)} 个):\n")
        for e in changed:
            print(f"   {e['id']} | {e['title']}")

    print(f"\n✅ 有效: {len(valid)} | ❌ 失效: {len(invalid)} | 🔄 变更: {len(changed)}")

    if invalid:
        print(f"\n💡 建议:")
        print(f"  - `kb remove <id>` — 移除失效条目")
        print(f"  - `kb edit <id> --title ...` — 更新条目信息")
    if changed:
        print(f"\n💡 有内容变更，执行 `kb compile` 重新编译")
