"""list / stats 子命令"""
import sys
import os
import glob
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import get_config
from service.config import SESSIONS_FILE, INDEX_DB, MEMORY_MD
from storage.jsonl import read_jsonl
from storage.jsonl_manage import read_all_entries, filter_entries

from ._helpers import _json_out, _paths


def cmd_list(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)
    scope = args.scope or "all"
    include_deleted = getattr(args, "include_deleted", False)

    entries = read_all_entries(daily_dir, sessions_path, scope=scope, include_deleted=include_deleted)
    entries = filter_entries(
        entries,
        keyword=args.keyword,
        entry_id=args.id,
        entry_type=args.type,
        date_from=getattr(args, "from_date", None),
        date_to=args.to,
        before=args.before,
    )

    days = getattr(args, "days", None)
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        entries = [e for e in entries if (e.get("timestamp", "") or "")[:10] >= cutoff]

    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(entries)

    offset = args.offset or 0
    limit = args.limit or 50
    page = entries[offset:offset + limit]

    records = []
    for e in page:
        rec = {
            "id": e.get("id"),
            "type": e.get("type"),
            "memory_type": e.get("memory_type"),
            "content": e.get("content", e.get("summary", e.get("topic", ""))),
            "entities": e.get("entities", []),
            "confidence": e.get("confidence"),
            "timestamp": e.get("timestamp"),
            "source_file": e.get("_source_file"),
        }
        if e.get("deleted_at"):
            rec["deleted_at"] = e["deleted_at"]
        records.append(rec)

    _json_out("ok", "list", {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": records,
    })


def cmd_stats(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)

    disk_kb = 0
    for root, dirs, files in os.walk(memory_dir):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                disk_kb += os.path.getsize(fp)
    disk_kb = round(disk_kb / 1024, 1)

    daily_files = sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))) if os.path.isdir(daily_dir) else []
    daily_data = {"file_count": len(daily_files), "facts": 0, "system_events": 0, "deleted": 0, "total": 0}
    if daily_files:
        dates = [os.path.basename(f).replace(".jsonl", "") for f in daily_files]
        daily_data["date_range"] = [dates[0], dates[-1]]
    for fpath in daily_files:
        for e in read_jsonl(fpath):
            daily_data["total"] += 1
            if e.get("deleted_at"):
                daily_data["deleted"] += 1
            elif e.get("type") in ("fact", None):
                daily_data["facts"] += 1
            else:
                daily_data["system_events"] += 1

    sess_entries = read_jsonl(sessions_path) if os.path.isfile(sessions_path) else []
    sess_data = {"count": len(sess_entries)}
    if sess_entries:
        last = sess_entries[-1]
        sess_data["latest_topic"] = last.get("topic", "")

    memory_md_path = os.path.join(memory_dir, MEMORY_MD)
    md_data = {}
    if os.path.isfile(memory_md_path):
        sz = os.path.getsize(memory_md_path)
        md_data["size_kb"] = round(sz / 1024, 1)
        with open(memory_md_path, "r", encoding="utf-8") as f:
            md_data["lines"] = sum(1 for _ in f)

    idx_path = os.path.join(memory_dir, INDEX_DB)
    idx_data = {}
    if os.path.isfile(idx_path):
        idx_data["size_kb"] = round(os.path.getsize(idx_path) / 1024, 1)
        try:
            conn = sqlite3.connect(idx_path)
            idx_data["chunks"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            row = conn.execute("SELECT value FROM meta WHERE key='last_sync'").fetchone()
            if row:
                idx_data["last_sync"] = row[0]
            row = conn.execute("SELECT value FROM meta WHERE key='embedding_model'").fetchone()
            if row:
                idx_data["embedding_model"] = row[0]
            conn.close()
        except Exception:
            pass

    cfg = get_config(project_path)
    cache_dir = os.path.expanduser(cfg.get("embedding.cache_dir"))
    model_data = {"path": cache_dir, "models": []}
    if os.path.isdir(cache_dir):
        model_data["models"] = [d.replace("models--", "").replace("--", "/")
                                for d in os.listdir(cache_dir)
                                if d.startswith("models--")]

    _json_out("ok", "stats", {
        "disk_usage_kb": disk_kb,
        "daily": daily_data,
        "sessions": sess_data,
        "memory_md": md_data,
        "index": idx_data,
        "model_cache": model_data,
    })
