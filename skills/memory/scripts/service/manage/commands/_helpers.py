"""公共辅助函数，供各 cmd_* 模块使用"""
import sys
import os
import json
import time
import shutil
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import get_config
from service.config import _DEFAULTS, _get_dotpath, SESSIONS_FILE, INDEX_DB, MEMORY_MD, DAILY_DIR_NAME
from storage.jsonl_manage import write_audit_entry
from core.utils import iso_now, ts_id

_SCRIPTS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")


def _json_out(status, command, data=None, error=None):
    out = {"status": status, "command": command}
    if data is not None:
        out["data"] = data
    if error is not None:
        out["error"] = error
    print(json.dumps(out, ensure_ascii=False, indent=2))


def _paths(project_path):
    """返回 memory_dir, daily_dir, sessions_path"""
    cfg = get_config(project_path)
    data_dir = cfg.get("paths.data_dir")
    memory_dir = os.path.join(project_path, data_dir)
    daily_dir = os.path.join(memory_dir, DAILY_DIR_NAME)
    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    return memory_dir, daily_dir, sessions_path


def _lock_path(memory_dir):
    return os.path.join(memory_dir, ".manage.lock")


def _backup(memory_dir, affected_files, daily_dir, sessions_path):
    """自动备份受影响的文件到 backups/ 目录"""
    ts = time.strftime("%Y-%m-%d-%H%M%S")
    backup_dir = os.path.join(memory_dir, "backups", ts)
    os.makedirs(backup_dir, exist_ok=True)
    for fname in affected_files:
        if fname == SESSIONS_FILE:
            src = sessions_path
        else:
            src = os.path.join(daily_dir, fname)
        if os.path.isfile(src):
            dst_dir = backup_dir if fname == SESSIONS_FILE else os.path.join(backup_dir, "daily")
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src, os.path.join(dst_dir, os.path.basename(fname)))
    return backup_dir


def _audit(memory_dir, command, scope, before_count, after_count, backup_path=None, success=True, error_msg=None):
    write_audit_entry(memory_dir, {
        "op_id": f"op-{ts_id()}",
        "timestamp": iso_now(),
        "actor": "agent",
        "command": command,
        "scope": scope,
        "before_count": before_count,
        "after_count": after_count,
        "backup_path": backup_path,
        "success": success,
        "error": error_msg,
    })


def _sync_index(project_path, full=False):
    """触发索引同步"""
    sync_script = os.path.join(_SCRIPTS_ROOT, "service", "memory", "sync_index.py")
    cmd = [sys.executable, sync_script, "--project-path", project_path]
    if full:
        cmd.append("--rebuild")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


def _parse_value(raw):
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _all_dotpaths(d, prefix=""):
    paths = []
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            paths.extend(_all_dotpaths(v, path))
        else:
            paths.append(path)
    return paths
