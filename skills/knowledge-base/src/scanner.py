"""内容扫描模块：读取资料内容、计算哈希、检测变更、生成摘要缓存。"""

import hashlib
import json
import os
from pathlib import Path

from .indexer import read_index, write_index, compute_hash, TEXT_READABLE_TYPES


def scan_entry(entry: dict) -> dict:
    """扫描单个索引条目，提取内容预览。"""
    path = entry["path"]
    entry_type = entry["type"]
    result = {
        "id": entry["id"],
        "title": entry["title"],
        "type": entry_type,
        "category": entry.get("category", "uncategorized"),
        "tags": entry.get("tags", []),
        "path": path,
    }

    if not os.path.exists(path) and entry_type != "link":
        result["content_preview"] = f"[路径不存在: {path}]"
        result["status"] = "invalid"
        return result

    result["status"] = "ok"
    result["content_preview"] = _extract_content(path, entry_type)
    return result


def _extract_content(path: str, entry_type: str, max_chars: int = 2000) -> str:
    p = Path(path)

    if entry_type in TEXT_READABLE_TYPES:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            return text[:max_chars]
        except Exception:
            return f"[读取失败: {path}]"

    elif entry_type == "repo":
        lines = [f"[代码仓库: {p.name}]"]
        readme = p / "README.md"
        if readme.exists():
            try:
                text = readme.read_text(encoding="utf-8", errors="replace")
                lines.append(f"\n## README\n{text[:max_chars - 200]}")
            except Exception:
                lines.append("[README 读取失败]")
        try:
            tree = _dir_tree(p, depth=3, max_items=30)
            lines.append(f"\n## 目录结构\n{tree}")
        except Exception:
            pass
        return "\n".join(lines)[:max_chars]

    elif entry_type == "image":
        desc = f"[图片: {p.name}, 大小: {p.stat().st_size} bytes]"
        return desc

    elif entry_type == "binary":
        try:
            stat = p.stat()
            return f"[二进制文件: {p.name}, 大小: {stat.st_size} bytes]"
        except Exception:
            return f"[二进制文件: {p.name}]"

    elif entry_type == "link":
        return f"[外部链接: {path}]"

    elif entry_type == "directory":
        try:
            tree = _dir_tree(p, depth=2, max_items=50)
            return tree[:max_chars]
        except Exception:
            return f"[目录: {path}]"

    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except Exception:
        return f"[无法读取: {p.name}]"


def _dir_tree(root: Path, depth: int = 3, max_items: int = 30, prefix: str = "") -> str:
    if depth < 0:
        return ""
    lines = []
    try:
        items = sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name))
    except PermissionError:
        return f"{prefix}[权限不足]"

    count = 0
    for item in items:
        if item.name.startswith("."):
            continue
        count += 1
        if count > max_items:
            lines.append(f"{prefix}... ({len(list(root.iterdir())) - max_items} more)")
            break
        if item.is_dir():
            lines.append(f"{prefix}{item.name}/")
            if depth > 1:
                sub = _dir_tree(item, depth - 1, max_items=10, prefix=prefix + "  ")
                if sub:
                    lines.append(sub)
        else:
            lines.append(f"{prefix}{item.name}")
    return "\n".join(lines)


def detect_changes(data_dir: Path) -> dict:
    """检测索引中哪些条目发生了变更。

    Returns:
        {
            "new": [...],       # compiled=false 的新条目
            "changed": [...],   # content_hash 变化的条目
            "invalid": [...],   # 路径失效的条目
            "unchanged": [...]  # 无变化的条目
        }
    """
    entries = read_index(data_dir)
    result = {"new": [], "changed": [], "invalid": [], "unchanged": []}

    for entry in entries:
        path = entry["path"]
        entry_type = entry["type"]

        if not os.path.exists(path) and entry_type != "link":
            result["invalid"].append(entry)
            continue

        if not entry.get("compiled", False):
            result["new"].append(entry)
            continue

        new_hash = compute_hash(path, entry_type)
        if new_hash and new_hash != entry.get("content_hash", ""):
            result["changed"].append(entry)
        else:
            result["unchanged"].append(entry)

    return result


def build_pending_list(data_dir: Path, full: bool = False) -> list:
    """构建待编译清单。

    Args:
        full: True 则全量编译（所有有效条目），False 则增量（new + changed）
    """
    if full:
        entries = read_index(data_dir)
        pending = []
        for entry in entries:
            if not os.path.exists(entry["path"]) and entry["type"] != "link":
                continue
            scanned = scan_entry(entry)
            if scanned["status"] == "ok":
                pending.append(scanned)
        return pending

    changes = detect_changes(data_dir)
    pending = []
    for entry in changes["new"] + changes["changed"]:
        scanned = scan_entry(entry)
        if scanned["status"] == "ok":
            pending.append(scanned)
    return pending


def update_hashes(data_dir: Path, entry_ids: list = None):
    """更新指定条目的 content_hash。如果 entry_ids 为 None 则更新所有。"""
    entries = read_index(data_dir)
    updated = 0
    for entry in entries:
        if entry_ids and entry["id"] not in entry_ids:
            continue
        path = entry["path"]
        if os.path.exists(path) or entry["type"] == "link":
            new_hash = compute_hash(path, entry["type"])
            if new_hash != entry.get("content_hash", ""):
                entry["content_hash"] = new_hash
                updated += 1
    if updated:
        write_index(data_dir, entries)
    return updated


def cache_content(data_dir: Path, entry_id: str, content: str):
    """缓存条目的内容摘要。"""
    cache_dir = data_dir / "raw" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{entry_id}.txt"
    cache_file.write_text(content, encoding="utf-8")


def get_cached_content(data_dir: Path, entry_id: str) -> str | None:
    cache_file = data_dir / "raw" / "cache" / f"{entry_id}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    return None
