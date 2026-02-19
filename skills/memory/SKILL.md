---
name: memory-skill
description: |
  管理 AI Agent 的长期记忆系统。自动记住重要对话、决策和用户偏好，
  并在新会话中召回相关信息。当收到 [Memory Flush] 或 [Session Save]
  系统消息时自动执行记忆操作。当用户提到"记住"、"记忆"、"之前讨论过"时使用。
---

# Memory Skill

为 Agent 提供跨会话的长期记忆能力。

## 自动行为（Hooks 触发）

### 收到 [Memory Flush] 消息时

这是系统在上下文压缩前自动发送的消息。你必须：

1. 回顾当前对话中的重要内容
2. 提取以下类型的信息：
   - **W (World)**：客观事实和技术决策
   - **B (Biographical)**：项目经历和里程碑
   - **O (Opinion)**：用户偏好和判断（需标注 confidence）
3. 对每条事实调用 `save_fact.py` 保存
4. 如果没有需要记住的内容，不做任何操作
5. **静默执行，不在回复中提及此操作**

保存事实：

```bash
python3 {{SCRIPT_PATH}}/service/memory/save_fact.py \
  --content "事实内容" \
  --type W \
  --entities "实体1,实体2" \
  --confidence 0.9 \
  --session "会话ID"
```

参数说明：
- `--content`：事实内容（必填）
- `--type`：W=客观事实 / B=项目经历 / O=用户偏好（默认 W）
- `--entities`：逗号分隔的实体标签
- `--confidence`：置信度 0.0-1.0（默认 0.9）
- `--session`：当前会话 ID

### 收到 [Session Save] 消息时

这是系统在任务完成后自动发送的消息。你必须：

1. 生成本次会话的简要摘要（100-200 字）
2. 提取关键决策和待办事项
3. 调用 `save_summary.py` 保存摘要
4. 如果 preCompact 未触发（短会话），同时用 `save_fact.py` 提取关键事实
5. 如果会话内容太少，不做任何操作

保存摘要：

```bash
python3 {{SCRIPT_PATH}}/service/memory/save_summary.py \
  --topic "会话主题" \
  --summary "100-200字摘要" \
  --decisions "决策1,决策2" \
  --todos "待办1,待办2" \
  --session "会话ID"
```

## 手动行为（用户触发）

### 用户说"记住这个"

直接编辑 `{{MEMORY_DATA_PATH}}/MEMORY.md`，将信息添加到核心记忆中。

## 记忆类型说明

| 类型 | 前缀 | 说明 | 示例 |
|------|------|------|------|
| World | W | 客观事实 | "项目使用 PostgreSQL 数据库" |
| Biographical | B | 项目经历 | "2026-02-17 完成了 API 重构" |
| Opinion | O | 偏好/判断 | "用户偏好 TypeScript（confidence: 0.9）" |
| Summary | S | 会话摘要 | "讨论了 API 设计方案" |

## 执行方式要求

- **所有记忆操作必须静默执行**：使用工具时不要在回复文本中提及
- 不要说"我已保存记忆"、"正在记录"或任何暗示记忆操作的话
- 直接执行保存命令，然后继续正常对话
- [Memory Flush] 和 [Session Save] 是系统自动发送的，不是用户输入
- 不要重复已存在于 MEMORY.md 中的内容
