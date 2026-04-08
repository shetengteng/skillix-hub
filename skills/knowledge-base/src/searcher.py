"""搜索与状态管理模块：关键词搜索、标签筛选、健康检查。"""

import os
import re
from pathlib import Path

from .indexer import read_index, compute_hash


def cmd_search(args, data_dir: Path):
    query = args.query
    tag = getattr(args, "search_tag", None)
    category = getattr(args, "search_category", None)

    results = []

    entries = read_index(data_dir)
    for e in entries:
        if tag and tag not in e.get("tags", []):
            continue
        if category and e.get("category") != category:
            continue
        if query:
            score = _match_score(query, e)
            if score > 0:
                results.append((score, "source", e))

    concepts_dir = data_dir / "wiki" / "concepts"
    if concepts_dir.exists() and query:
        for md_file in concepts_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                score = _text_match_score(query, content)
                if score > 0:
                    title = md_file.stem
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break
                    results.append((score, "concept", {"id": md_file.stem, "title": title}))
            except Exception:
                continue

    results.sort(key=lambda x: x[0], reverse=True)

    if not results:
        print(f"📭 没有找到匹配「{query or tag or category}」的结果")
        return

    print(f"=== Knowledge Base: 搜索结果 ===\n")
    print(f"查询: {query or ''} {f'标签:{tag}' if tag else ''} {f'分类:{category}' if category else ''}\n")

    for score, rtype, item in results[:20]:
        if rtype == "source":
            status = "✅" if item.get("compiled") else "⏳"
            print(f"  📄 {status} {item['id']} | {item['title']}")
            print(f"      分类: {item.get('category', '')} | 路径: {item['path']}")
        else:
            print(f"  💡 {item['id']} | {item['title']}")
        print()

    print(f"共 {len(results)} 个结果（显示前 {min(len(results), 20)} 个）\n")
    print("💡 下一步:")
    print("  - `kb read <concept-id>` — 查看概念")
    print("  - `kb source <source-id>` — 查看资料详情")


def _match_score(query: str, entry: dict) -> int:
    score = 0
    q = query.lower()
    title = entry.get("title", "").lower()
    tags = [t.lower() for t in entry.get("tags", [])]
    category = entry.get("category", "").lower()
    path = entry.get("path", "").lower()

    if q in title:
        score += 10
    for word in q.split():
        if word in title:
            score += 5
        if word in tags:
            score += 3
        if word in category:
            score += 2
        if word in path:
            score += 1
    return score


def _text_match_score(query: str, text: str) -> int:
    score = 0
    q = query.lower()
    t = text.lower()
    if q in t:
        score += 5
    for word in q.split():
        count = t.count(word)
        score += min(count, 5)
    return score


def cmd_status(args, data_dir: Path):
    entries = read_index(data_dir)

    total = len(entries)
    compiled = sum(1 for e in entries if e.get("compiled"))
    pending = total - compiled

    valid = 0
    invalid = 0
    for e in entries:
        if e["type"] == "link" or os.path.exists(e["path"]):
            valid += 1
        else:
            invalid += 1

    concepts_dir = data_dir / "wiki" / "concepts"
    concept_count = len(list(concepts_dir.glob("*.md"))) if concepts_dir.exists() else 0

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
    print()
    print(f"📚 Wiki 统计")
    print(f"   概念条目:   {concept_count}")
    print(f"   知识图谱:   {'✅ 已生成' if has_graph else '❌ 未生成'}")
    print(f"   最近编译:   {last_compile}")
    print()

    if invalid > 0:
        print("⚠ 存在失效路径，建议执行 `kb check` 检查详情")
    if pending > 0:
        print(f"💡 有 {pending} 个待编译条目，执行 `kb compile` 开始编译")


def cmd_check(args, data_dir: Path):
    entries = read_index(data_dir)

    valid = []
    invalid = []
    changed = []

    for e in entries:
        path = e["path"]
        if e["type"] == "link":
            valid.append(e)
            continue

        if not os.path.exists(path):
            invalid.append(e)
            continue

        new_hash = compute_hash(path, e["type"])
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
