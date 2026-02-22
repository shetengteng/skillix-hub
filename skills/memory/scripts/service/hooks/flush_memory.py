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
SAVE_FACT_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'save_fact.py')}"

# 记忆刷写提示词模板，包含提取规则和 save_fact 调用示例
FLUSH_TEMPLATE = """[Memory Flush]

上下文即将压缩（当前使用率 {usage}%，消息数 {msg_count}）。请回顾当前对话，提取关键事实并保存。

## 提取规则

1. **技术决策**：架构选择、配置变更、Bug 修复方案
2. **用户偏好**：编码风格、工具选择、沟通方式、命名习惯
3. **项目经历**：里程碑、重要变更、团队信息

## 保存方式

对每条事实调用保存工具：

```bash
{save_fact_cmd} --content "事实内容" --type W --entities "实体1,实体2" --confidence 0.9 --session "{conv_id}"
```

memory_type：W=客观事实 / B=项目经历 / O=用户偏好

## 阶段摘要

请同时保存一条阶段摘要，概括截至目前的对话主要内容（50-100字）：

```bash
{save_fact_cmd} --content "阶段摘要：[概括内容]" --type S --entities "session" --confidence 1.0 --session "{conv_id}"
```

## 注意

- 如果没有需要记住的内容，不做任何操作
- **静默执行，不在回复中提及此操作**
- 不要重复已存在于 MEMORY.md 中的内容"""


@require_hook_memory()
def main(event, project_path):
    """主入口：生成 [Memory Flush] 提示词并输出 user_message。"""
    os.makedirs(get_memory_dir(project_path), exist_ok=True)

    usage = event.get("context_usage_percent", "?")
    msg_count = event.get("message_count", "?")
    conv_id = event.get("conversation_id", "unknown")

    log.info("preCompact 触发 usage=%s%% msg_count=%s conv_id=%s", usage, msg_count, conv_id)

    prompt = FLUSH_TEMPLATE.format(
        usage=usage,
        msg_count=msg_count,
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=conv_id,
    )

    print(json.dumps({"user_message": prompt}))


if __name__ == "__main__":
    main()
