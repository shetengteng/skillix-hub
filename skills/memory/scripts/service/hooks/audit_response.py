#!/usr/bin/env python3
"""
afterAgentResponse Hook：检测 Agent 回复中的重要事实信号，记录到审计日志。

在 Agent 每次完成一条回复后触发，分析回复文本中是否包含值得记忆的信号词。
当前 Cursor 的 afterAgentResponse 输出字段为空（无法注入消息），
因此本脚本仅做审计记录，不影响 Agent 行为。

检测到信号时写入 daily.jsonl 的 type=audit 记录，方便排查"AI 说了但没保存"的情况。
"""
import sys
import json
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import require_hook_memory, get_memory_dir
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger

log = get_logger("audit_response")

SIGNAL_PATTERNS = [
    (r"记下来了|已记录|我记住了|已经记住", "memory_claim"),
    (r"这个原则|这个规范|这个规则|项目规范", "principle"),
    (r"决定使用|选择了|确定方案|采用了|改为使用", "decision"),
    (r"重要[：:]|注意[：:]|关键[：:]", "important_marker"),
    (r"commit.*(?:push|完成)|已.*(?:commit|push)", "commit_action"),
]


def detect_signals(text):
    """检测文本中的重要事实信号，返回匹配的信号列表"""
    found = []
    for pattern, signal_type in SIGNAL_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            found.append({"type": signal_type, "matches": matches[:3]})
    return found


@require_hook_memory()
def main(event, project_path):
    text = event.get("text", "")
    if not text:
        print(json.dumps({}))
        return

    signals = detect_signals(text)
    if not signals:
        print(json.dumps({}))
        return

    memory_dir = get_memory_dir(project_path)
    daily_dir = os.path.join(memory_dir, "daily")
    os.makedirs(daily_dir, exist_ok=True)
    daily_file = os.path.join(daily_dir, f"{today_str()}.jsonl")

    signal_types = [s["type"] for s in signals]
    snippet = text[:200].replace("\n", " ")

    entry = {
        "id": f"log-{ts_id()}",
        "type": "audit",
        "signals": signal_types,
        "snippet": snippet,
        "timestamp": iso_now(),
    }

    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info("检测到信号 %s (回复前200字: %s)", signal_types, snippet[:60])
    print(json.dumps({}))


if __name__ == "__main__":
    main()
