#!/usr/bin/env python3
"""
会话结束 Hook 脚本（sessionEnd）

在 Composer 会话彻底关闭后触发（stop 之后），执行后台清理任务：
1. 增量同步 JSONL → SQLite 索引（此时 Agent 已完成所有写入）
2. 记录会话元数据（结束原因、持续时间）到 daily.jsonl
3. 清理超期日志文件

这是 fire-and-forget Hook，输出不被使用。
"""
import sys
import json
import os
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_project_path, _DEFAULTS
from service.config import get_memory_dir
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger

log = get_logger("end_session")

_MEMORY_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory"))


def sync_index(project_path: str):
    """调用 sync_index.py 增量同步 JSONL 到 SQLite"""
    sync_script = os.path.join(_MEMORY_DIR, "sync_index.py")
    try:
        proc = subprocess.run(
            [sys.executable, sync_script, "--project-path", project_path],
            capture_output=True, text=True, timeout=25,
        )
        if proc.returncode == 0:
            log.info("索引同步完成")
        else:
            log.warning("索引同步失败 (exit=%d): %s", proc.returncode, proc.stderr[:200])
    except subprocess.TimeoutExpired:
        log.warning("索引同步超时")
    except Exception as e:
        log.warning("索引同步异常: %s", e)


def log_session_end(memory_dir: str, event: dict):
    """将会话结束元数据写入 daily.jsonl"""
    daily_dir = os.path.join(memory_dir, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")

    entry = {
        "id": f"log-{ts_id()}",
        "type": "session_end",
        "reason": event.get("reason", "unknown"),
        "duration_ms": event.get("duration_ms"),
        "session_id": event.get("conversation_id", ""),
        "timestamp": iso_now(),
    }
    error_msg = event.get("error_message")
    if error_msg:
        entry["error"] = error_msg

    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info("记录会话结束 reason=%s duration=%sms",
             entry["reason"], entry.get("duration_ms"))


def clean_old_logs():
    """清理超过保留天数的日志文件"""
    import glob
    from datetime import datetime, timedelta

    log_dir = os.path.join(os.getcwd(), _DEFAULTS["paths"]["data_dir"], "logs")
    if not os.path.isdir(log_dir):
        return

    cutoff = datetime.now() - timedelta(days=_DEFAULTS["log"]["retain_days"])
    removed = 0
    for f in glob.glob(os.path.join(log_dir, "*.log")):
        basename = os.path.basename(f)
        try:
            file_date = datetime.strptime(basename.replace(".log", ""), "%Y-%m-%d")
            if file_date < cutoff:
                os.remove(f)
                removed += 1
        except ValueError:
            continue

    if removed:
        log.info("清理过期日志 %d 个", removed)


def main():
    event = {}
    try:
        raw = sys.stdin.read().strip()
        if raw:
            event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    project_path = get_project_path(event)
    memory_dir = get_memory_dir(project_path)

    log.info("sessionEnd 触发 reason=%s", event.get("reason", "unknown"))

    sync_index(project_path)
    log_session_end(memory_dir, event)
    clean_old_logs()

    print(json.dumps({}))


if __name__ == "__main__":
    main()
