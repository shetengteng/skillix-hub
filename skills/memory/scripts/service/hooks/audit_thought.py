#!/usr/bin/env python3
"""
afterAgentThought Hook：检测 Agent 思考过程中的决策意图，记录到审计日志。

思考文本通常包含 AI 的推理过程和决策判断，是提取事实的重要来源。
与 audit_response.py 共享信号检测逻辑，但针对思考文本的特点增加了额外模式。

当前 Cursor 的 afterAgentThought 输出字段为空，仅做审计记录。
"""
import sys
import json
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_project_path, get_memory_dir
from service.config import is_memory_enabled
from core.utils import iso_now, today_str, ts_id
from service.logger import get_logger

log = get_logger("audit_thought")

THOUGHT_PATTERNS = [
    (r"需要记住|应该记录|值得保存", "intent_to_remember"),
    (r"用户(?:偏好|喜欢|要求|希望)", "user_preference"),
    (r"架构(?:决策|选择|方案)|技术(?:选型|方案)", "architecture_decision"),
    (r"这个(?:原则|规范|规则|约定)", "principle"),
    (r"关键(?:发现|结论|决定)", "key_finding"),
]


def detect_thought_signals(text):
    """检测思考文本中的决策意图信号"""
    found = []
    for pattern, signal_type in THOUGHT_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            found.append({"type": signal_type, "matches": matches[:3]})
    return found


def main():
    event = {}
    try:
        raw = sys.stdin.read().strip()
        if raw:
            event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    text = event.get("text", "")
    if not text or len(text) < 20:
        print(json.dumps({}))
        return

    project_path = get_project_path(event)
    if not is_memory_enabled(project_path):
        print(json.dumps({}))
        return

    signals = detect_thought_signals(text)
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
        "source": "thought",
        "signals": signal_types,
        "snippet": snippet,
        "timestamp": iso_now(),
    }

    with open(daily_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info("思考信号 %s (前60字: %s)", signal_types, snippet[:60])
    print(json.dumps({}))


if __name__ == "__main__":
    main()
