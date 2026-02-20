"""edit / export / cleanup 子命令"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import SESSIONS_FILE, MEMORY_MD
from storage.jsonl import read_jsonl
from storage.jsonl_manage import read_all_entries, _rewrite_jsonl, soft_delete_entries, purge_entries
from core.utils import iso_now
from core.file_lock import FileLock

from ._helpers import _json_out, _paths, _lock_path, _backup, _audit, _sync_index


def cmd_edit(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)

    if not args.id:
        _json_out("error", "edit", error={"code": "MISSING_ID", "message": "必须指定 --id"})
        sys.exit(2)

    entries = read_all_entries(daily_dir, sessions_path, scope="all")
    target = None
    for e in entries:
        if e.get("id") == args.id:
            target = e
            break

    if not target:
        _json_out("error", "edit", error={"code": "NOT_FOUND", "message": f"未找到 ID: {args.id}"})
        sys.exit(1)

    updates = {}
    if args.content is not None:
        updates["content"] = args.content
    if args.memory_type is not None:
        if args.memory_type not in ("W", "B", "O"):
            _json_out("error", "edit", error={"code": "INVALID_TYPE", "message": "memory_type 只能是 W/B/O"})
            sys.exit(2)
        updates["memory_type"] = args.memory_type
    if args.confidence is not None:
        if not 0.0 <= args.confidence <= 1.0:
            _json_out("error", "edit", error={"code": "INVALID_CONFIDENCE", "message": "confidence 需在 0.0~1.0"})
            sys.exit(2)
        updates["confidence"] = args.confidence
    if args.entities is not None:
        updates["entities"] = [e.strip() for e in args.entities.split(",")]

    if not updates:
        _json_out("error", "edit", error={"code": "NO_UPDATES", "message": "未指定修改字段"})
        sys.exit(2)

    source_file = target.get("_source_file", "")
    with FileLock(_lock_path(memory_dir)):
        _backup(memory_dir, [source_file], daily_dir, sessions_path)

        if source_file == SESSIONS_FILE:
            all_entries = read_jsonl(sessions_path)
            for e in all_entries:
                if e.get("id") == args.id:
                    e.update(updates)
            _rewrite_jsonl(sessions_path, all_entries)
        else:
            fpath = os.path.join(daily_dir, source_file)
            all_entries = read_jsonl(fpath)
            for e in all_entries:
                if e.get("id") == args.id:
                    e.update(updates)
            _rewrite_jsonl(fpath, all_entries)

    synced = _sync_index(project_path) if not args.no_sync else False
    _audit(memory_dir, "edit", "daily", 1, 1)
    _json_out("ok", "edit", {"id": args.id, "updated_fields": list(updates.keys()), "index_synced": synced})


def cmd_export(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)
    scope = args.scope or "all"

    entries = read_all_entries(daily_dir, sessions_path, scope=scope, include_deleted=False)
    if args.type:
        entries = [e for e in entries if e.get("type") == args.type]

    days = getattr(args, "days", None)
    if days:
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        entries = [e for e in entries if (e.get("timestamp", "") or "")[:10] >= cutoff]
    from_date = getattr(args, "from_date", None)
    if from_date:
        entries = [e for e in entries if (e.get("timestamp", "") or "")[:10] >= from_date]
    to_date = getattr(args, "to", None)
    if to_date:
        entries = [e for e in entries if (e.get("timestamp", "") or "")[:10] <= to_date]

    records = []
    for e in entries:
        clean = {k: v for k, v in e.items() if not k.startswith("_")}
        records.append(clean)

    core_memory = ""
    memory_md_path = os.path.join(memory_dir, MEMORY_MD)
    if os.path.isfile(memory_md_path):
        with open(memory_md_path, "r", encoding="utf-8") as f:
            core_memory = f.read()

    export_data = {
        "exported_at": iso_now(),
        "scope": scope,
        "core_memory": core_memory,
        "records": records,
        "total": len(records),
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        _json_out("ok", "export", {"file": args.output, "total": len(records)})
    else:
        _json_out("ok", "export", export_data)


def cmd_cleanup(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)
    scope = args.scope or "daily"

    entries = read_all_entries(daily_dir, sessions_path, scope=scope, include_deleted=False)

    if args.purge_deleted:
        all_entries = read_all_entries(daily_dir, sessions_path, scope=scope, include_deleted=True)
        matched = [e for e in all_entries if e.get("deleted_at")]
    elif args.system_events:
        matched = [e for e in entries if e.get("type") in ("session_start", "session_end")]
    elif args.older_than:
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=args.older_than)).strftime("%Y-%m-%d")
        matched = [e for e in entries if (e.get("timestamp", "") or "")[:10] < cutoff]
    else:
        _json_out("error", "cleanup", error={"code": "MISSING_CRITERIA", "message": "需指定清理条件"})
        sys.exit(2)

    if not matched:
        _json_out("ok", "cleanup", {"total": 0, "message": "无匹配记录"})
        return

    if not args.confirm:
        _json_out("preview", "cleanup", {
            "total": len(matched),
            "mode": "purge" if args.purge_deleted else "soft",
            "message": f"将清理 {len(matched)} 条记录",
        })
        return

    ids = {e.get("id") for e in matched if e.get("id")}
    affected = list({e.get("_source_file") for e in matched if e.get("_source_file")})

    with FileLock(_lock_path(memory_dir)):
        backup_path = _backup(memory_dir, affected, daily_dir, sessions_path)
        if args.purge_deleted:
            result = purge_entries(daily_dir, sessions_path, ids)
            count = result["purged"]
        else:
            result = soft_delete_entries(daily_dir, sessions_path, ids)
            count = result["deleted"]

    synced = _sync_index(project_path) if not args.no_sync else False
    _audit(memory_dir, "cleanup", scope, len(entries), len(entries) - count, os.path.relpath(backup_path, memory_dir))
    _json_out("ok", "cleanup", {"cleaned": count, "backup_path": os.path.relpath(backup_path, memory_dir), "index_synced": synced})
