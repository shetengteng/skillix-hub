#!/usr/bin/env python3
"""
会话结束 Hook 脚本（sessionEnd）

在 Composer 会话彻底关闭后触发（stop 之后），执行后台清理任务：
1. 增量同步 JSONL → SQLite 索引（此时 Agent 已完成所有写入）
2. 检测本次会话是否成功保存了摘要（兜底检测）
3. 记录会话元数据（结束原因、持续时间）到 daily.jsonl
4. 清理超期日志文件

这是 fire-and-forget Hook，输出不被使用。
"""
import sys
import json
import os
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import init_hook_context, _DEFAULTS, SESSIONS_FILE
from service.config import get_memory_dir, is_memory_enabled
from storage.jsonl import read_last_entry
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger

log = get_logger("end_session")

_MEMORY_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory"))


def sync_index(project_path: str):
    """调用 sync_index.py 增量同步 JSONL 到 SQLite"""
    sync_script = os.path.join(_MEMORY_DIR, "sync_index.py")
    try:
        env = os.environ.copy()
        env["MEMORY_PROJECT_PATH"] = project_path
        proc = subprocess.run(
            [sys.executable, sync_script, "--project-path", project_path],
            capture_output=True, text=True, timeout=25, env=env,
        )
        if proc.returncode == 0:
            log.info("索引同步完成")
        else:
            log.warning("索引同步失败 (exit=%d): %s", proc.returncode, proc.stderr[:200])
    except subprocess.TimeoutExpired:
        log.warning("索引同步超时")
    except Exception as e:
        log.warning("索引同步异常: %s", e)


def distill_facts(project_path: str):
    """调用 distill_to_memory.py 将高价值事实提炼到 MEMORY.md"""
    try:
        from service.memory.distill_to_memory import distill
        count = distill(project_path)
        if count > 0:
            log.info("事实提炼完成: %d 条写入 MEMORY.md", count)
    except Exception as e:
        log.warning("事实提炼异常: %s", e)


def check_summary_saved(memory_dir: str, event: dict):
    """检测本次会话是否成功保存了摘要，未保存则写入警告"""
    conv_id = event.get("conversation_id", "")
    reason = event.get("reason", "unknown")
    if not conv_id or reason not in ("completed", "user_close"):
        return

    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    last = read_last_entry(sessions_path)
    if last and last.get("session_id") == conv_id:
        log.info("摘要已保存 session_id=%s", conv_id)
        return

    log.warning("本次会话未保存摘要 session_id=%s reason=%s", conv_id, reason)
    daily_dir = os.path.join(memory_dir, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")
    warning = {
        "id": f"log-{ts_id()}",
        "type": "warning",
        "content": f"会话 {conv_id[:8]}... 未保存摘要 (reason={reason})",
        "session_id": conv_id,
        "timestamp": iso_now(),
    }
    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(warning, ensure_ascii=False) + "\n")


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


def clean_old_logs(project_path: str):
    """清理超过保留天数的日志文件"""
    import glob
    from datetime import datetime, timedelta

    log_dir = os.path.join(project_path, _DEFAULTS["paths"]["data_dir"], "logs")
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

    project_path = init_hook_context(event)

    if not is_memory_enabled(project_path):
        log.info("Memory 已禁用（.memory-disable），跳过")
        print(json.dumps({}))
        return

    memory_dir = get_memory_dir(project_path)

    log.info("sessionEnd 触发 reason=%s", event.get("reason", "unknown"))

    sync_index(project_path)
    check_summary_saved(memory_dir, event)
    distill_facts(project_path)
    log_session_end(memory_dir, event)
    clean_old_logs(project_path)

    print(json.dumps({}))


if __name__ == "__main__":
    main()
