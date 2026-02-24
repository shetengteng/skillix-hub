#!/usr/bin/env python3
"""
CLI 工具：保存单条事实到 daily/YYYY-MM-DD.jsonl。

使用场景：由 flush_memory 或 save_session 的提示词引导 Agent 调用，或手动执行。
每条事实包含 content、memory_type(W/B/O)、entities、confidence 等字段。
"""
import sys
import os
import re
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_daily_dir
from service.config import require_memory_enabled
from core.utils import iso_now, today_str, ts_id
from service.memory.session_state import update_fact_count
from service.logger import get_logger, redirect_to_project

log = get_logger("save_fact")

_MAX_CONTENT_LENGTH = 800


def sanitize_content(content: str) -> str:
    """清洗 fact content，移除混入的命令片段并截断超长内容。"""
    content = re.sub(
        r'python3\s+\S*save_fact\.py\s+--content\s+"[^"]*".*?--session\s+"[^"]*"',
        '', content
    )
    content = re.sub(
        r'python3\s+\S*save_summary\.py\s+--topic\s+"[^"]*".*?--session\s+"[^"]*"',
        '', content
    )
    content = re.sub(r'python3\s+\S*save_fact\.py\s+--\S+.*', '', content)
    content = re.sub(r'\s{2,}', ' ', content).strip()

    if len(content) > _MAX_CONTENT_LENGTH:
        log.warning("fact content 超长 (%d 字)，截断至 %d", len(content), _MAX_CONTENT_LENGTH)
        content = content[:_MAX_CONTENT_LENGTH]

    return content


def infer_memory_type(content: str, declared_type: str) -> str:
    """当 declared_type 为 W 时，尝试根据内容推断更准确的类型。"""
    if declared_type != "W":
        return declared_type

    if re.search(r'偏好|习惯|风格|不要|必须|禁止|规范|约定|规则', content):
        return "O"
    if re.search(r'项目结构|技术栈|子项目|工作区|仓库|架构概览|模块组成', content):
        return "B"
    return "W"


@require_memory_enabled
def main():
    """
    解析命令行参数，将事实追加写入当日 daily 文件。

    参数：--content(必填)、--type(W/B/O)、--entities、--confidence、--session、--project-path
    """
    parser = argparse.ArgumentParser(description="Save a fact to memory")
    parser.add_argument("--content", required=True, help="Fact content")
    parser.add_argument("--type", default="W", choices=["W", "B", "O", "S"],
                        help="W=World, B=Biographical, O=Opinion, S=Stage Summary")
    parser.add_argument("--entities", default="",
                        help="Comma-separated entity tags")
    parser.add_argument("--confidence", type=float, default=0.9)
    parser.add_argument("--session", default="")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    redirect_to_project(args.project_path)

    daily_dir = get_daily_dir(args.project_path)
    os.makedirs(daily_dir, exist_ok=True)

    entities = [e.strip() for e in args.entities.split(",") if e.strip()]

    content = sanitize_content(args.content)
    memory_type = infer_memory_type(content, args.type)

    if memory_type != args.type:
        log.info("memory_type 自动推断: %s → %s", args.type, memory_type)

    entry = {
        "id": f"log-{ts_id()}",
        "type": "fact",
        "memory_type": memory_type,
        "content": content,
        "entities": entities,
        "confidence": args.confidence,
        "timestamp": iso_now(),
    }
    if args.session:
        entry["source"] = {"session": args.session}

    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")
    line = json.dumps(entry, ensure_ascii=False)
    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    log.info("保存事实 id=%s type=%s → %s", entry["id"], memory_type, daily_file)

    if args.session:
        memory_dir = os.path.dirname(daily_dir)
        update_fact_count(memory_dir, args.session, memory_type)

    print(json.dumps({"status": "ok", "id": entry["id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
