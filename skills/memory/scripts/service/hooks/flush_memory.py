#!/usr/bin/env python3
"""
preCompact Hook：构建记忆刷写指令，让 Agent 在上下文压缩前提取关键事实。

使用场景：当对话上下文使用率接近阈值时，Cursor 触发 preCompact，本脚本生成
[Memory Flush] 提示词注入 user_message，引导 Agent 调用 save_fact.py 保存事实。
"""
import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import require_hook_memory
from service.config import get_memory_dir
from service.logger import get_logger

log = get_logger("flush_memory")

_MEMORY_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory"))
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
SAVE_FACT_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'save_fact.py')}"


def _load_template(name: str) -> str:
    path = os.path.join(_PROMPTS_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().rstrip()


@require_hook_memory()
def main(event, project_path):
    """主入口：生成 [Memory Flush] 提示词并输出 user_message。"""
    os.makedirs(get_memory_dir(project_path), exist_ok=True)

    usage = event.get("context_usage_percent", "?")
    msg_count = event.get("message_count", "?")
    conv_id = event.get("conversation_id", "unknown")

    log.info("preCompact 触发 usage=%s%% msg_count=%s conv_id=%s", usage, msg_count, conv_id)

    prompt = _load_template("flush_template.txt").format(
        usage=usage,
        msg_count=msg_count,
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=conv_id,
    )

    print(json.dumps({"user_message": prompt}))


if __name__ == "__main__":
    main()
