#!/usr/bin/env python3
"""
stop Hook：构建会话保存指令，让 Agent 在任务完成时生成摘要并补充提取事实。

使用场景：当会话状态为 completed 或 aborted 时，Cursor 触发 stop Hook，
本脚本生成 [Session Save] 提示词注入 followup_message，引导 Agent 调用
save_summary.py 和 save_fact.py。
"""
import sys
import json
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import require_hook_memory
from service.config import get_memory_dir
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
{save_summary_cmd} --topic "主题" --summary "100-200字摘要" --decisions "决策1,决策2" --todos "待办1,待办2" --source layer4_stop --session "{conv_id}"
```

## 逐条提取关键事实（必须执行）

回顾本次会话，将以下类型的信息**逐条**保存为独立事实：

- 新确立的项目原则或规范 → type O
- 重要的架构决策或技术选型 → type W
- 用户明确表达的偏好 → type O
- 关键的 Bug 修复方案 → type W

对每条事实分别调用：

```bash
{save_fact_cmd} --content "事实内容" --type W --entities "实体1,实体2" --confidence 0.9 --session "{conv_id}"
```

## 注意

- 如果会话内容太少或无意义，不做任何操作
- 不要遗漏会话中间产生的重要事实（即使当时已经用 save_fact 保存过，也不需要重复保存）
- **静默执行，不在回复中提及此操作**"""


def has_session_data(memory_dir: str, conv_id: str) -> bool:
    """
    检查本会话是否已有摘要或 fact 数据。
    优先查 session_state 文件，回退时按 session_id 全量检索 daily。
    """
    from service.memory.session_state import read_session_state

    state = read_session_state(memory_dir, conv_id)
    if state:
        if state.get("summary_saved"):
            return True
        if state.get("fact_count", 0) > 0 or state.get("stage_summary_count", 0) > 0:
            return True

    daily_dir = os.path.join(memory_dir, "daily")
    if not os.path.isdir(daily_dir):
        return False

    MAX_SCAN_FILES = 30
    for f in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl")), reverse=True)[:MAX_SCAN_FILES]:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line.strip())
                    source = entry.get("source", {})
                    if isinstance(source, dict) and source.get("session") == conv_id and entry.get("type") == "fact":
                        return True
                except json.JSONDecodeError:
                    continue

    return False


@require_hook_memory()
def main(event, project_path):
    """主入口：在 status=completed 或 aborted 时生成 [Session Save] 提示词。"""
    status = event.get("status", "")
    conv_id = event.get("conversation_id", "unknown")

    log.info("stop 触发 status=%s conv_id=%s", status, conv_id)

    if status not in ("completed", "aborted"):
        log.info("status=%s 非 completed/aborted，跳过摘要保存提示", status)
        print(json.dumps({}))
        return

    memory_dir = get_memory_dir(project_path)
    os.makedirs(memory_dir, exist_ok=True)

    if conv_id and conv_id != "unknown" and has_session_data(memory_dir, conv_id):
        log.info("会话已有数据，跳过 followup_message conv_id=%s", conv_id[:12])
        print(json.dumps({}))
        return

    prompt = SAVE_TEMPLATE.format(
        save_summary_cmd=SAVE_SUMMARY_CMD,
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=conv_id,
    )

    log.info("[Layer4] 注入 [Session Save] 提示词（兜底）conv_id=%s", conv_id[:12])
    print(json.dumps({"followup_message": prompt}))


if __name__ == "__main__":
    main()
