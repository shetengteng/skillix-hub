"""知识图谱模块：构建、查询、输出知识图谱。"""

import json
from pathlib import Path

from .indexer import read_index, write_index


def cmd_graph(args, data_dir: Path):
    fmt = getattr(args, "format", "json")
    center = getattr(args, "center", None)
    depth = getattr(args, "depth", 2)

    graph = _load_graph(data_dir)
    if not graph or not graph.get("nodes"):
        print("📭 知识图谱为空，请先编译 Wiki")
        print("\n💡 下一步: `kb compile` — 开始编译")
        return

    if center:
        graph = _subgraph(graph, center, depth)
        if not graph["nodes"]:
            print(f"❌ 未找到节点: {center}")
            return

    if fmt == "mermaid":
        _output_mermaid(graph)
    else:
        _output_json(graph)


def _load_graph(data_dir: Path) -> dict:
    graph_file = data_dir / "wiki" / "graph.json"
    if graph_file.exists():
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"nodes": [], "edges": []}


def _subgraph(graph: dict, center_id: str, depth: int) -> dict:
    """提取以 center_id 为中心、depth 跳范围内的子图。"""
    node_ids = set()
    edge_set = set()

    adj = {}
    for edge in graph["edges"]:
        f, t = edge["from"], edge["to"]
        adj.setdefault(f, []).append((t, edge.get("relation", "")))
        adj.setdefault(t, []).append((f, edge.get("relation", "")))

    frontier = {center_id}
    for _ in range(depth):
        next_frontier = set()
        for nid in frontier:
            node_ids.add(nid)
            for neighbor, rel in adj.get(nid, []):
                if neighbor not in node_ids:
                    next_frontier.add(neighbor)
                edge_key = (min(nid, neighbor), max(nid, neighbor))
                edge_set.add(edge_key)
        frontier = next_frontier
    node_ids.update(frontier)

    node_map = {n["id"]: n for n in graph["nodes"]}
    sub_nodes = [node_map[nid] for nid in node_ids if nid in node_map]
    sub_edges = [
        e for e in graph["edges"]
        if e["from"] in node_ids and e["to"] in node_ids
    ]

    return {"nodes": sub_nodes, "edges": sub_edges}


def _output_json(graph: dict):
    print("=== Knowledge Base: 知识图谱 (JSON) ===\n")
    print(json.dumps(graph, ensure_ascii=False, indent=2))
    print(f"\n节点: {len(graph['nodes'])} | 边: {len(graph['edges'])}")


def _output_mermaid(graph: dict):
    print("=== Knowledge Base: 知识图谱 (Mermaid) ===\n")
    print("```mermaid")
    print("graph TD")

    node_labels = {}
    for node in graph["nodes"]:
        nid = _mermaid_id(node["id"])
        label = node.get("label", node["id"])
        ntype = node.get("type", "concept")
        if ntype == "concept":
            print(f"    {nid}[\"{label}\"]")
        else:
            print(f"    {nid}([\"{label}\"])")
        node_labels[node["id"]] = nid

    for edge in graph["edges"]:
        fid = node_labels.get(edge["from"], _mermaid_id(edge["from"]))
        tid = node_labels.get(edge["to"], _mermaid_id(edge["to"]))
        rel = edge.get("relation", "")
        if rel:
            print(f"    {fid} -->|{rel}| {tid}")
        else:
            print(f"    {fid} --> {tid}")

    print("```")
    print(f"\n节点: {len(graph['nodes'])} | 边: {len(graph['edges'])}")


def _mermaid_id(raw_id: str) -> str:
    return raw_id.replace("-", "_").replace(".", "_").replace(" ", "_")


# ─── 概念管理命令 ───


def cmd_concept(args, data_dir: Path):
    action = args.action
    if action == "remove":
        _concept_remove(args, data_dir)
    elif action == "merge":
        _concept_merge(args, data_dir)
    elif action == "rename":
        _concept_rename(args, data_dir)
    elif action == "list":
        _concept_list(data_dir)
    else:
        print(f"❌ 未知操作: {action}")


def _concept_list(data_dir: Path):
    concepts_dir = data_dir / "wiki" / "concepts"
    if not concepts_dir.exists():
        print("📭 没有概念条目")
        return

    files = sorted(concepts_dir.glob("*.md"))
    if not files:
        print("📭 没有概念条目")
        return

    print(f"=== Knowledge Base: 概念列表 ({len(files)} 个) ===\n")
    for f in files:
        print(f"  {f.stem}")


def _concept_remove(args, data_dir: Path):
    concept_id = args.concept_id
    concept_file = data_dir / "wiki" / "concepts" / f"{concept_id}.md"

    if not concept_file.exists():
        print(f"❌ 未找到概念: {concept_id}")
        return

    concept_file.unlink()
    print(f"✅ 已删除概念: {concept_id}")
    print("💡 执行 `kb compile --finalize` 更新索引")


def _concept_merge(args, data_dir: Path):
    id1, id2 = args.concept_id, args.concept_id2
    concepts_dir = data_dir / "wiki" / "concepts"
    file1 = concepts_dir / f"{id1}.md"
    file2 = concepts_dir / f"{id2}.md"

    if not file1.exists():
        print(f"❌ 未找到概念: {id1}")
        return
    if not file2.exists():
        print(f"❌ 未找到概念: {id2}")
        return

    content1 = file1.read_text(encoding="utf-8")
    content2 = file2.read_text(encoding="utf-8")

    print(f"=== 概念合并预览 ===\n")
    print(f"保留: {id1}")
    print(f"删除: {id2}")
    print(f"\n将 {id2} 的内容追加到 {id1} 的「来源资料」和「关联概念」中。")
    print(f"请手动编辑 {file1} 完成合并，然后执行 `kb compile --finalize`。")
    print(f"\n已附加 {id2} 的内容到 {id1} 末尾：")

    with open(file1, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n> 以下内容来自已合并的概念 `{id2}`：\n\n")
        f.write(content2)

    file2.unlink()
    print(f"\n✅ {id2} 已删除，内容已追加到 {id1}")


def _concept_rename(args, data_dir: Path):
    concept_id = args.concept_id
    new_title = args.new_title
    concepts_dir = data_dir / "wiki" / "concepts"
    concept_file = concepts_dir / f"{concept_id}.md"

    if not concept_file.exists():
        print(f"❌ 未找到概念: {concept_id}")
        return

    content = concept_file.read_text(encoding="utf-8")
    import re
    content = re.sub(r"^(title:\s*).*$", f"\\1{new_title}", content, count=1, flags=re.MULTILINE)
    content = re.sub(r"^#\s+.*$", f"# {new_title}", content, count=1, flags=re.MULTILINE)
    concept_file.write_text(content, encoding="utf-8")

    print(f"✅ 已重命名: {concept_id} → {new_title}")


# ─── 分类管理命令 ───


def cmd_category(args, data_dir: Path):
    action = args.action
    if action == "list":
        _category_list(data_dir)
    elif action == "rename":
        _category_rename(args, data_dir)
    else:
        print(f"❌ 未知操作: {action}")


def _category_list(data_dir: Path):
    entries = read_index(data_dir)
    by_cat = {}
    for e in entries:
        cat = e.get("category", "uncategorized")
        by_cat.setdefault(cat, 0)
        by_cat[cat] += 1

    print("=== Knowledge Base: 分类列表 ===\n")
    for cat, count in sorted(by_cat.items()):
        print(f"  📂 {cat} ({count} 个资料)")
    print(f"\n共 {len(by_cat)} 个分类")


def _category_rename(args, data_dir: Path):
    old_name = args.old_name
    new_name = args.new_name
    entries = read_index(data_dir)

    renamed = 0
    for e in entries:
        if e.get("category") == old_name:
            e["category"] = new_name
            renamed += 1

    if renamed == 0:
        print(f"❌ 未找到分类: {old_name}")
        return

    write_index(data_dir, entries)

    # 同时重命名分类索引文件
    cats_dir = data_dir / "wiki" / "categories"
    old_file = cats_dir / f"{old_name}.md"
    new_file = cats_dir / f"{new_name}.md"
    if old_file.exists():
        old_file.rename(new_file)

    print(f"✅ 分类重命名: {old_name} → {new_name} ({renamed} 个条目)")
