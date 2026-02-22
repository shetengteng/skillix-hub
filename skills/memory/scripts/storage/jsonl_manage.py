"""
JSONL 管理操作：读取全部、筛选、软删除、恢复、物理删除、统计、审计
"""
import json
import os
import glob
from .jsonl import read_jsonl
from core.utils import iso_now


def read_all_entries(daily_dir: str, sessions_path: str, scope: str = "all",
                     include_deleted: bool = False) -> list:
    """
    读取指定 scope 内的全部条目。
    scope: "daily" | "sessions" | "all"
    """
    entries = []
    if scope in ("daily", "all") and os.path.isdir(daily_dir):
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            for e in read_jsonl(fpath):
                e["_source_file"] = os.path.basename(fpath)
                entries.append(e)
    if scope in ("sessions", "all") and os.path.isfile(sessions_path):
        for e in read_jsonl(sessions_path):
            e["_source_file"] = os.path.basename(sessions_path)
            entries.append(e)
    if not include_deleted:
        entries = [e for e in entries if not e.get("deleted_at")]
    return entries


def filter_entries(entries: list, keyword: str = None, entry_id: str = None,
                   entry_type: str = None, date_from: str = None,
                   date_to: str = None, before: str = None) -> list:
    """按条件筛选条目"""
    result = entries
    if entry_id:
        result = [e for e in result if e.get("id") == entry_id]
    if entry_type:
        result = [e for e in result if e.get("type") == entry_type]
    if keyword:
        kw = keyword.lower()
        result = [e for e in result if kw in e.get("content", "").lower()
                  or kw in json.dumps(e.get("entities", []), ensure_ascii=False).lower()]
    if before:
        result = [e for e in result if (e.get("timestamp", "") or "")[:10] <= before]
    if date_from:
        result = [e for e in result if (e.get("timestamp", "") or "")[:10] >= date_from]
    if date_to:
        result = [e for e in result if (e.get("timestamp", "") or "")[:10] <= date_to]
    return result


def _rewrite_jsonl(filepath: str, entries: list):
    """原子重写 JSONL 文件"""
    tmp = filepath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for e in entries:
            clean = {k: v for k, v in e.items() if not k.startswith("_")}
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, filepath)


def soft_delete_entries(daily_dir: str, sessions_path: str,
                        ids_to_delete: set, actor: str = "agent") -> dict:
    """软删除：为匹配 ID 的条目添加 deleted_at / deleted_by 标记"""
    affected_files = []
    deleted = 0
    now = iso_now()

    if os.path.isdir(daily_dir):
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            entries = read_jsonl(fpath)
            changed = False
            for e in entries:
                if e.get("id") in ids_to_delete and not e.get("deleted_at"):
                    e["deleted_at"] = now
                    e["deleted_by"] = actor
                    changed = True
                    deleted += 1
            if changed:
                _rewrite_jsonl(fpath, entries)
                affected_files.append(os.path.basename(fpath))

    if os.path.isfile(sessions_path):
        entries = read_jsonl(sessions_path)
        changed = False
        for e in entries:
            if e.get("id") in ids_to_delete and not e.get("deleted_at"):
                e["deleted_at"] = now
                e["deleted_by"] = actor
                changed = True
                deleted += 1
        if changed:
            _rewrite_jsonl(sessions_path, entries)
            affected_files.append(os.path.basename(sessions_path))

    return {"deleted": deleted, "affected_files": affected_files}


def restore_entries(daily_dir: str, sessions_path: str, ids_to_restore: set) -> dict:
    """移除 deleted_at / deleted_by 标记，恢复软删除的条目"""
    restored = 0

    if os.path.isdir(daily_dir):
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            entries = read_jsonl(fpath)
            changed = False
            for e in entries:
                if e.get("id") in ids_to_restore and e.get("deleted_at"):
                    e.pop("deleted_at", None)
                    e.pop("deleted_by", None)
                    changed = True
                    restored += 1
            if changed:
                _rewrite_jsonl(fpath, entries)

    if os.path.isfile(sessions_path):
        entries = read_jsonl(sessions_path)
        changed = False
        for e in entries:
            if e.get("id") in ids_to_restore and e.get("deleted_at"):
                e.pop("deleted_at", None)
                e.pop("deleted_by", None)
                changed = True
                restored += 1
        if changed:
            _rewrite_jsonl(sessions_path, entries)

    return {"restored": restored}


def purge_entries(daily_dir: str, sessions_path: str, ids_to_purge: set) -> dict:
    """物理删除：从 JSONL 文件中移除匹配 ID 的条目"""
    purged = 0
    affected_files = []

    if os.path.isdir(daily_dir):
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            entries = read_jsonl(fpath)
            before_count = len(entries)
            entries = [e for e in entries if e.get("id") not in ids_to_purge]
            removed = before_count - len(entries)
            if removed:
                _rewrite_jsonl(fpath, entries)
                purged += removed
                affected_files.append(os.path.basename(fpath))

    if os.path.isfile(sessions_path):
        entries = read_jsonl(sessions_path)
        before_count = len(entries)
        entries = [e for e in entries if e.get("id") not in ids_to_purge]
        removed = before_count - len(entries)
        if removed:
            _rewrite_jsonl(sessions_path, entries)
            purged += removed
            affected_files.append(os.path.basename(sessions_path))

    return {"purged": purged, "affected_files": affected_files}


def count_by_type(daily_dir: str, sessions_path: str) -> dict:
    """按类型统计条目数量"""
    counts = {}
    entries = read_all_entries(daily_dir, sessions_path, scope="all", include_deleted=True)
    for e in entries:
        t = e.get("type", "unknown")
        counts.setdefault(t, {"total": 0, "active": 0, "deleted": 0})
        counts[t]["total"] += 1
        if e.get("deleted_at"):
            counts[t]["deleted"] += 1
        else:
            counts[t]["active"] += 1
    return counts


def write_audit_entry(memory_dir: str, entry: dict):
    """写入审计日志"""
    audit_dir = os.path.join(memory_dir, "audit")
    os.makedirs(audit_dir, exist_ok=True)
    audit_file = os.path.join(audit_dir, "operations.jsonl")
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
