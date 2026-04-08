"""渐进式浏览模块：按层级输出知识库内容。"""

import json
import os
import re
from pathlib import Path

from .indexer import read_index


def cmd_browse(args, data_dir: Path):
    category = getattr(args, "category", None)
    if category:
        _browse_category(data_dir, category)
    else:
        _browse_overview(data_dir)


def _browse_overview(data_dir: Path):
    """L1: 知识地图概览。"""
    index_md = data_dir / "wiki" / "index.md"
    if index_md.exists():
        print(index_md.read_text(encoding="utf-8"))
        print()
        print("💡 下一步:")
        print("  - `kb browse <category>` — 查看分类下的概念")
        print("  - `kb search \"关键词\"` — 搜索知识库")
        print("  - `kb graph --format mermaid` — 查看知识图谱")
        return

    entries = read_index(data_dir)
    if not entries:
        print("📭 知识库为空，请先添加资料")
        print("\n💡 下一步:")
        print("  - `kb add <path>` — 添加资料")
        print("  - `kb import-project` — 导入项目 design/ 目录")
        return

    by_cat = {}
    for e in entries:
        cat = e.get("category", "uncategorized")
        by_cat.setdefault(cat, []).append(e)

    compiled = sum(1 for e in entries if e.get("compiled"))
    pending = len(entries) - compiled

    concepts_dir = data_dir / "wiki" / "concepts"
    concept_count = len(list(concepts_dir.glob("*.md"))) if concepts_dir.exists() else 0

    print("=== Knowledge Base: 知识地图 ===\n")
    for cat, items in sorted(by_cat.items()):
        print(f"📂 {cat} ({len(items)} 个资料)")
    print(f"\n共 {len(entries)} 个资料 | {concept_count} 个概念 | {pending} 个待编译\n")
    print("💡 下一步:")
    print("  - `kb browse <category>` — 查看分类下的概念")
    if pending > 0:
        print("  - `kb compile` — 编译待处理条目")
    print("  - `kb search \"关键词\"` — 搜索知识库")


def _browse_category(data_dir: Path, category: str):
    """L2: 查看分类下的概念和资料。"""
    cat_file = data_dir / "wiki" / "categories" / f"{category}.md"
    if cat_file.exists():
        print(cat_file.read_text(encoding="utf-8"))
        print()

    entries = read_index(data_dir)
    cat_entries = [e for e in entries if e.get("category") == category]

    if not cat_entries and not cat_file.exists():
        print(f"❌ 未找到分类: {category}")
        cats = sorted(set(e.get("category", "uncategorized") for e in entries))
        if cats:
            print(f"   可用分类: {', '.join(cats)}")
        return

    if cat_entries:
        print(f"\n📂 {category} — 资料索引 ({len(cat_entries)} 个)\n")
        for e in cat_entries:
            status = "✅" if e.get("compiled") else "⏳"
            print(f"   {status} {e['id']} | {e['title']}")

    print(f"\n💡 下一步:")
    print(f"  - `kb read <concept-id>` — 查看概念条目")
    print(f"  - `kb source <source-id>` — 查看原始资料")


def cmd_read(args, data_dir: Path):
    """L3: 查看具体概念条目。"""
    concept_id = args.id
    concept_file = data_dir / "wiki" / "concepts" / f"{concept_id}.md"

    if not concept_file.exists():
        print(f"❌ 未找到概念: {concept_id}")
        concepts_dir = data_dir / "wiki" / "concepts"
        if concepts_dir.exists():
            available = [f.stem for f in concepts_dir.glob("*.md")]
            if available:
                print(f"   可用概念: {', '.join(available[:10])}")
                if len(available) > 10:
                    print(f"   ... 共 {len(available)} 个")
        return

    print(concept_file.read_text(encoding="utf-8"))

    backlinks = _load_backlinks(data_dir)
    if concept_id in backlinks:
        refs = backlinks[concept_id].get("referenced_by", [])
        if refs:
            print(f"\n📎 被引用: {', '.join(refs)}")

    print(f"\n💡 下一步:")
    print(f"  - `kb source <source-id>` — 查看来源资料")
    print(f"  - `kb browse` — 返回知识地图")


def cmd_source(args, data_dir: Path):
    """L4: 查看原始资料信息。"""
    source_id = args.id
    entries = read_index(data_dir)

    matched = [e for e in entries if e["id"] == source_id]
    if not matched:
        print(f"❌ 未找到资料: {source_id}")
        return

    entry = matched[0]
    print(f"=== 资料详情: {entry['title']} ===\n")
    print(f"ID:       {entry['id']}")
    print(f"类型:     {entry['type']}")
    print(f"分类:     {entry['category']}")
    print(f"标签:     {', '.join(entry.get('tags', [])) or '无'}")
    print(f"路径:     {entry['path']}")
    print(f"已编译:   {'是' if entry.get('compiled') else '否'}")
    print(f"创建时间: {entry.get('created_at', '未知')}")

    path_exists = os.path.exists(entry["path"])
    print(f"路径有效: {'✅ 是' if path_exists else '❌ 否'}")

    if path_exists and entry["type"] == "markdown":
        try:
            content = Path(entry["path"]).read_text(encoding="utf-8", errors="replace")
            preview = content[:500]
            print(f"\n--- 内容预览 ---\n{preview}")
            if len(content) > 500:
                print(f"\n... (共 {len(content)} 字)")
        except Exception:
            pass

    print(f"\n💡 下一步:")
    print(f"  - 直接读取原始文件: Read {entry['path']}")


def _load_backlinks(data_dir: Path) -> dict:
    bl_file = data_dir / "wiki" / "backlinks.json"
    if bl_file.exists():
        try:
            with open(bl_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}
