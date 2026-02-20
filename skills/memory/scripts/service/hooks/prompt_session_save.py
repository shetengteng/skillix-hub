#!/usr/bin/env python3
"""
stop Hook：构建会话保存指令，让 Agent 在任务完成时生成摘要并补充提取事实。

使用场景：当会话状态为 completed 时，Cursor 触发 stop Hook，本脚本生成
[Session Save] 提示词注入 followup_message，引导 Agent 调用 save_summary.py
和 save_fact.py。
"""
import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_project_path
from service.config import get_memory_dir, is_memory_enabled
from core.utils import iso_now, ts_id, today_str
from service.logger import get_logger

log = get_logger("stop_hook")

_MEMORY_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory"))
SAVE_SUMMARY_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'save_summary.py')}"
SAVE_FACT_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'save_fact.py')}"

SAVE_TEMPLATE = """[Session Save]

任务已完成。请生成本次会话的摘要并保存。

## 摘要要求

1. **主题**：用一句话描述本次会话的主要内容
2. **摘要**：100-200 字的总结
3. **关键决策**：列出本次会话中做出的重要决策
4. **待办事项**：列出未完成的工作（如有）

## 保存摘要

```bash
{save_summary_cmd} --topic "主题" --summary "100-200字摘要" --decisions "决策1,决策2" --todos "待办1,待办2" --session "{conv_id}"
```

## 补充提取事实

如果本次会话中 preCompact 未触发（短会话），同时提取关键事实：

```bash
{save_fact_cmd} --content "事实内容" --type W --entities "实体" --session "{conv_id}"
```

## 注意

- 如果会话内容太少或无意义，不做任何操作
- **静默执行，不在回复中提及此操作**"""


def main():
    """主入口：从 stdin 读取 event，仅在 status=completed 时生成 [Session Save] 提示词。"""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        event = {}

    status = event.get("status", "")
    conv_id = event.get("conversation_id", "unknown")

    log.info("stop 触发 status=%s conv_id=%s", status, conv_id)

    if status != "completed":
        log.info("status 非 completed，跳过摘要保存提示")
        print(json.dumps({}))
        return

    project_path = get_project_path(event)

    if not is_memory_enabled(project_path):
        log.info("Memory 已禁用（.memory-disable），跳过")
        print(json.dumps({}))
        return

    os.makedirs(get_memory_dir(project_path), exist_ok=True)

    prompt = SAVE_TEMPLATE.format(
        save_summary_cmd=SAVE_SUMMARY_CMD,
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=conv_id,
    )

    log.info("注入 [Session Save] 提示词")
    print(json.dumps({"followup_message": prompt}))


if __name__ == "__main__":
    main()
