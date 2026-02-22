#!/usr/bin/env python3
"""
记忆加载脚本

两种调用方式：
1. 命令行调用（Rules 触发）：python3 load_memory.py → 直接输出纯文本记忆
2. 未来 Hook 调用（stdin 传入 event JSON）：输出 {"additional_context": "..."} JSON
"""
import sys
import json
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import MEMORY_MD, SESSIONS_FILE, DAILY_DIR_NAME
from service.config import get_memory_dir, is_memory_enabled, init_hook_context, ensure_memory_dir
from storage.jsonl import read_recent_facts_from_daily, read_last_entry
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger, redirect_to_project

log = get_logger("load")


def load_context(project_path):
    """加载所有记忆数据，返回格式化的上下文文本"""
    memory_dir = get_memory_dir(project_path)
    ensure_memory_dir(memory_dir)
    context_parts = []

    memory_md_path = os.path.join(memory_dir, MEMORY_MD)
    if os.path.exists(memory_md_path):
        with open(memory_md_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            context_parts.append(f"## 核心记忆\n\n{content}")
            log.info("加载 MEMORY.md (%d 字符)", len(content))

    daily_dir = os.path.join(memory_dir, DAILY_DIR_NAME)
    recent_facts = read_recent_facts_from_daily(daily_dir)
    recent_facts = [f for f in recent_facts if f.get("memory_type") != "S"]
    fact_count = len(recent_facts) if recent_facts else 0
    log.info("加载近期事实 %d 条（从 daily/ 目录）", fact_count)
    if recent_facts:
        for i, fact in enumerate(recent_facts):
            fid = fact.get("id", "?")
            ftype = fact.get("memory_type", "?")
            fdate = fact.get("timestamp", "")[:10]
            fcontent = fact.get("content", "")[:80]
            log.info("  [%d] id=%s date=%s type=%s: %s", i + 1, fid, fdate, ftype, fcontent)
        lines = []
        for fact in recent_facts:
            mtype = fact.get("memory_type", "?")
            content = fact.get("content", "")
            ts = fact.get("timestamp", "")[:10]
            lines.append(f"- [{mtype}][{ts}] {content}")
        context_parts.append("## 近期事实\n\n" + "\n".join(lines))

    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    last_session = read_last_entry(sessions_path)
    if last_session:
        topic = last_session.get("topic", "未知")
        summary = last_session.get("summary", "无")
        sid = last_session.get("id", "?")
        log.info("加载上次会话 id=%s topic='%s'", sid, topic[:50])
        context_parts.append(
            f"## 上次会话\n\n- 主题：{topic}\n- 摘要：{summary}"
        )
    else:
        log.info("无上次会话摘要")

    return "\n\n".join(context_parts) if context_parts else ""


def log_session_start(memory_dir: str, workspace: str, conv_id: str):
    """将 session_start 事件写入 daily/YYYY-MM-DD.jsonl"""
    daily_dir = os.path.join(memory_dir, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")
    entry = json.dumps(
        {
            "id": f"log-{ts_id()}",
            "type": "session_start",
            "timestamp": iso_now(),
            "workspace": workspace,
            "session_id": conv_id,
        },
        ensure_ascii=False,
    )
    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def main():
    parser = argparse.ArgumentParser(description="Load memory context")
    parser.add_argument("--project-path", default=os.getcwd())
    args, _ = parser.parse_known_args()

    event = {}
    stdin_raw = ""
    if not sys.stdin.isatty():
        try:
            stdin_raw = sys.stdin.read().strip()
            if stdin_raw:
                event = json.loads(stdin_raw)
        except (json.JSONDecodeError, ValueError) as e:
            log.error("stdin JSON 解析失败: %s, raw=%s", e, stdin_raw[:200])

    try:
        if event:
            project_path = init_hook_context(event)
            conv_id = event.get("conversation_id", "unknown")
            log.info("sessionStart hook 触发 conv_id=%s project=%s", conv_id, project_path)
        else:
            project_path = args.project_path
            redirect_to_project(project_path)
            log.info("命令行调用 project=%s", project_path)
    except Exception as e:
        log.error("初始化失败: %s", e, exc_info=True)
        print(json.dumps({"additional_context": ""}) if event else "")
        return

    if not is_memory_enabled(project_path):
        log.info("Memory 已禁用（.memory-disable），跳过")
        print(json.dumps({"additional_context": ""}) if event else "")
        return

    try:
        memory_dir = get_memory_dir(project_path)
        context = load_context(project_path)
        log_session_start(memory_dir, project_path, event.get("conversation_id", ""))
        log.info("上下文输出 %d 字符", len(context))
    except Exception as e:
        log.error("记忆加载失败: %s", e, exc_info=True)
        context = ""

    if event:
        print(json.dumps({"additional_context": context}))
    else:
        print(context)


if __name__ == "__main__":
    main()
