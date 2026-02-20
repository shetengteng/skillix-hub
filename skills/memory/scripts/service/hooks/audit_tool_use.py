#!/usr/bin/env python3
"""
postToolUse Hook：在 Shell 工具执行后检测关键操作（git commit 等），
自动提取决策信息并记录到 daily.jsonl。

通过 matcher="Shell" 过滤，只在 Shell 工具执行后触发。
检测 git commit 命令时从输出中提取 commit message 作为决策记录。
跳过 save_fact.py/save_summary.py 调用以避免递归。
"""
import sys
import json
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import init_hook_context, get_memory_dir
from service.config import is_memory_enabled
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger

log = get_logger("audit_tool")

SKIP_PATTERNS = [
    r"save_fact\.py",
    r"save_summary\.py",
    r"distill_to_memory\.py",
    r"sync_index\.py",
    r"userinput\.py",
]

CAPTURE_PATTERNS = [
    {
        "pattern": r"git\s+commit",
        "type": "git_commit",
        "extract": r'\[[\w/]+\s+([a-f0-9]+)\]\s+(.+)',
    },
    {
        "pattern": r"git\s+push",
        "type": "git_push",
        "extract": r'([a-f0-9]+)\.\.([a-f0-9]+)\s+\S+\s*->\s*(\S+)',
    },
    {
        "pattern": r"(?:npm|pip|yarn)\s+install",
        "type": "dependency_install",
        "extract": r'added\s+(\d+)\s+packages|Successfully installed (.+)',
    },
]


def should_skip(command):
    """检查命令是否应该跳过（memory 自身的脚本调用）"""
    for pat in SKIP_PATTERNS:
        if re.search(pat, command):
            return True
    return False


def detect_tool_action(command, output):
    """检测工具操作类型并提取关键信息"""
    for cap in CAPTURE_PATTERNS:
        if re.search(cap["pattern"], command):
            extracted = None
            if output and cap.get("extract"):
                match = re.search(cap["extract"], output)
                if match:
                    extracted = match.groups()
            return cap["type"], extracted
    return None, None


def main():
    event = {}
    try:
        raw = sys.stdin.read().strip()
        if raw:
            event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    tool_name = event.get("tool_name", "")
    if tool_name != "Shell":
        print(json.dumps({}))
        return

    tool_input = event.get("tool_input", {})
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except (json.JSONDecodeError, ValueError):
            tool_input = {"command": tool_input}

    command = tool_input.get("command", "")
    output = event.get("tool_output", "")

    if not command or should_skip(command):
        print(json.dumps({}))
        return

    project_path = init_hook_context(event)
    if not is_memory_enabled(project_path):
        print(json.dumps({}))
        return

    action_type, extracted = detect_tool_action(command, output)
    if not action_type:
        print(json.dumps({}))
        return

    memory_dir = get_memory_dir(project_path)
    daily_dir = os.path.join(memory_dir, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")

    entry = {
        "id": f"log-{ts_id()}",
        "type": "audit",
        "action": action_type,
        "command": command[:200],
        "timestamp": iso_now(),
    }
    if extracted:
        entry["extracted"] = [x for x in extracted if x]

    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info("捕获操作 %s: %s", action_type, command[:60])
    print(json.dumps({}))


if __name__ == "__main__":
    main()
