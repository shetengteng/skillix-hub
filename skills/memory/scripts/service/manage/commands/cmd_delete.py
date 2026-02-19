"""delete / restore 子命令"""
import sys
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import SESSIONS_FILE
from storage.jsonl_manage import read_all_entries, filter_entries, soft_delete_entries, restore_entries, purge_entries
from core.file_lock import FileLock

from ._helpers import _json_out, _paths, _lock_path, _backup, _audit, _sync_index


def cmd_delete(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)
    scope = args.scope or "daily"
    include_deleted = False

    entries = read_all_entries(daily_dir, sessions_path, scope=scope, include_deleted=include_deleted)
    if args.all_flag:
        matched = entries
    else:
        matched = filter_entries(
            entries, keyword=args.keyword, entry_id=args.id, entry_type=args.type,
            date_from=getattr(args, "from_date", None), date_to=args.to, before=args.before,
        )

    if not matched:
        _json_out("ok", "delete", {"total": 0, "message": "无匹配记录"})
        return

    if not args.confirm:
        records = [{"id": e.get("id"), "type": e.get("type"), "content": (e.get("content") or "")[:80],
                     "timestamp": e.get("timestamp"), "source_file": e.get("_source_file")} for e in matched[:20]]
        mode = "purge" if args.purge else "soft"
        _json_out("preview", "delete", {
            "total": len(matched),
            "mode": mode,
            "records": records,
            "message": f"将{'物理删除' if args.purge else '软删除'} {len(matched)} 条记录",
        })
        return

    ids = {e.get("id") for e in matched if e.get("id")}
    affected = list({e.get("_source_file") for e in matched if e.get("_source_file")})

    with FileLock(_lock_path(memory_dir)):
        backup_path = _backup(memory_dir, affected, daily_dir, sessions_path)
        before_count = len(entries)

        if args.purge:
            result = purge_entries(daily_dir, sessions_path, ids)
            mode = "purge"
            count = result["purged"]
        else:
            result = soft_delete_entries(daily_dir, sessions_path, ids)
            mode = "soft"
            count = result["deleted"]

        after_entries = read_all_entries(daily_dir, sessions_path, scope=scope, include_deleted=False)

    synced = False
    if not args.no_sync:
        synced = _sync_index(project_path)

    _audit(memory_dir, f"delete({mode})", scope, before_count, len(after_entries), backup_path)

    _json_out("ok", "delete", {
        "deleted": count,
        "mode": mode,
        "affected_files": result.get("affected_files", []),
        "backup_path": os.path.relpath(backup_path, memory_dir),
        "index_synced": synced,
    })


def cmd_restore(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)

    if args.from_backup:
        backup_dir = os.path.join(memory_dir, "backups", args.from_backup)
        if not os.path.isdir(backup_dir):
            _json_out("error", "restore", error={"code": "BACKUP_NOT_FOUND", "message": f"备份不存在: {args.from_backup}"})
            sys.exit(4)
        with FileLock(_lock_path(memory_dir)):
            restored = 0
            daily_bk = os.path.join(backup_dir, "daily")
            if os.path.isdir(daily_bk):
                for f in os.listdir(daily_bk):
                    src = os.path.join(daily_bk, f)
                    dst = os.path.join(daily_dir, f)
                    shutil.copy2(src, dst)
                    restored += 1
            sess_bk = os.path.join(backup_dir, SESSIONS_FILE)
            if os.path.isfile(sess_bk):
                shutil.copy2(sess_bk, sessions_path)
                restored += 1
        synced = _sync_index(project_path)
        _audit(memory_dir, "restore(backup)", "all", 0, 0, args.from_backup)
        _json_out("ok", "restore", {"restored_files": restored, "mode": "from-backup", "index_synced": synced})
        return

    entries = read_all_entries(daily_dir, sessions_path, scope="all", include_deleted=True)
    deleted_entries = [e for e in entries if e.get("deleted_at")]

    if args.id:
        to_restore = [e for e in deleted_entries if e.get("id") == args.id]
    elif getattr(args, "from_date", None):
        to_restore = [e for e in deleted_entries if (e.get("deleted_at") or "")[:10] >= args.from_date]
    else:
        to_restore = deleted_entries

    if not to_restore:
        _json_out("ok", "restore", {"restored": 0, "message": "无可恢复的记录"})
        return

    ids = {e.get("id") for e in to_restore if e.get("id")}
    with FileLock(_lock_path(memory_dir)):
        result = restore_entries(daily_dir, sessions_path, ids)

    synced = _sync_index(project_path) if not args.no_sync else False
    _audit(memory_dir, "restore(soft-undelete)", "all", 0, result["restored"])
    _json_out("ok", "restore", {"restored": result["restored"], "mode": "soft-undelete", "index_synced": synced})
