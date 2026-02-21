#!/usr/bin/env python3
"""
CLI 工具：保存会话摘要到 sessions.jsonl。

使用场景：由 save_session 的 stop Hook 提示词引导 Agent 调用。记录会话主题、
摘要、关键决策、待办事项，供 load_memory 在下次会话时加载「上次会话」。
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_memory_dir
from service.config import SESSIONS_FILE
from core.utils import iso_now, ts_id
from core.file_lock import FileLock
from service.logger import get_logger

log = get_logger("save_summary")


def main():
    """
    解析命令行参数，将会话摘要追加写入 sessions.jsonl。

    参数：--topic、--summary(必填)、--decisions、--todos、--session、--project-path
    """
    parser = argparse.ArgumentParser(description="Save session summary")
    parser.add_argument("--topic", required=True, help="Session topic")
    parser.add_argument("--summary", required=True, help="Session summary")
    parser.add_argument("--decisions", default="",
                        help="Comma-separated decisions")
    parser.add_argument("--todos", default="",
                        help="Comma-separated todo items")
    parser.add_argument("--session", default="")
    parser.add_argument("--source", default="layer1_rules",
                        choices=["layer1_rules", "layer4_stop"],
                        help="摘要来源层级")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    from service.logger import redirect_to_project
    redirect_to_project(args.project_path)

    memory_dir = get_memory_dir(args.project_path)
    os.makedirs(memory_dir, exist_ok=True)

    # 解析逗号分隔的决策和待办列表
    decisions = [d.strip() for d in args.decisions.split(",") if d.strip()]
    todos = [t.strip() for t in args.todos.split(",") if t.strip()]

    entry = {
        "id": f"sum-{ts_id()}",
        "session_id": args.session,
        "topic": args.topic,
        "summary": args.summary,
        "decisions": decisions,
        "todos": todos,
        "timestamp": iso_now(),
        "source": args.source,
    }

    sessions_file = os.path.join(memory_dir, SESSIONS_FILE)

    def do_write():
        with open(sessions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    if args.session:
        from service.memory.session_state import save_summary_atomic, SaveResult, _sessions_lock_path
        result = save_summary_atomic(memory_dir, args.session, args.source, do_write)
        if result.status == SaveResult.EXISTS:
            log.info("摘要已存在，跳过 session=%s", args.session[:12])
            print(json.dumps({"status": "skipped", "reason": "already_saved"}))
            return
        elif result.status == SaveResult.ERROR:
            log.warning("摘要保存异常 session=%s: %s", args.session[:12], result.reason)
            print(json.dumps({"status": "error", "reason": result.reason}))
            return
    else:
        from service.memory.session_state import _sessions_lock_path
        with FileLock(_sessions_lock_path(memory_dir), timeout=5):
            do_write()

    log.info("[Layer1] 摘要保存 id=%s topic='%s' → %s", entry["id"], args.topic[:30], sessions_file)
    print(json.dumps({"status": "ok", "id": entry["id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
