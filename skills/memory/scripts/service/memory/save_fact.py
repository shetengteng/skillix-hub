#!/usr/bin/env python3
"""
CLI 工具：保存单条事实到 daily/YYYY-MM-DD.jsonl。

使用场景：由 flush_memory 或 save_session 的提示词引导 Agent 调用，或手动执行。
每条事实包含 content、memory_type(W/B/O)、entities、confidence 等字段。
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_daily_dir
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger

log = get_logger("save_fact")


def main():
    """
    解析命令行参数，将事实追加写入当日 daily 文件。

    参数：--content(必填)、--type(W/B/O)、--entities、--confidence、--session、--project-path
    """
    parser = argparse.ArgumentParser(description="Save a fact to memory")
    parser.add_argument("--content", required=True, help="Fact content")
    parser.add_argument("--type", default="W", choices=["W", "B", "O"],
                        help="W=World, B=Biographical, O=Opinion")
    parser.add_argument("--entities", default="",
                        help="Comma-separated entity tags")
    parser.add_argument("--confidence", type=float, default=0.9)
    parser.add_argument("--session", default="")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    from service.logger import redirect_to_project
    redirect_to_project(args.project_path)

    daily_dir = get_daily_dir(args.project_path)
    os.makedirs(daily_dir, exist_ok=True)

    # 解析逗号分隔的实体列表
    entities = [e.strip() for e in args.entities.split(",") if e.strip()]

    entry = {
        "id": f"log-{ts_id()}",
        "type": "fact",
        "memory_type": args.type,
        "content": args.content,
        "entities": entities,
        "confidence": args.confidence,
        "timestamp": iso_now(),
    }
    if args.session:
        entry["source"] = {"session": args.session}

    # 追加到当日 JSONL 文件
    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")
    line = json.dumps(entry, ensure_ascii=False)
    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    log.info("保存事实 id=%s type=%s → %s", entry["id"], args.type, daily_file)
    print(json.dumps({"status": "ok", "id": entry["id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
