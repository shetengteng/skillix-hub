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

from service.config import get_project_path
from service.config import get_memory_dir
from core.utils import iso_now, today_str, ts_id

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

## 注意

- 如果没有需要记住的内容，不做任何操作
- **静默执行，不在回复中提及此操作**
- 不要重复已存在于 MEMORY.md 中的内容"""


def main():
    """主入口：从 stdin 读取 event，生成 [Memory Flush] 提示词并输出 user_message。"""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        event = {}

    project_path = get_project_path(event)
    os.makedirs(get_memory_dir(project_path), exist_ok=True)

    # 填充模板：上下文使用率、消息数、save_fact 命令、会话 ID
    prompt = FLUSH_TEMPLATE.format(
        usage=event.get("context_usage_percent", "?"),
        msg_count=event.get("message_count", "?"),
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=event.get("conversation_id", "unknown"),
    )

    print(json.dumps({"user_message": prompt}))


if __name__ == "__main__":
    main()
