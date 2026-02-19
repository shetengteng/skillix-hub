---
name: memory
description: |
  管理 AI Agent 的长期记忆系统。自动记住重要对话、决策和用户偏好，
  并在新会话中召回相关信息。当收到 [Memory Flush] 或 [Session Save]
  系统消息时自动执行记忆操作。当用户提到"记住"、"记忆"、"之前讨论过"时使用。
---

# Memory Skill

为 Agent 提供跨会话的长期记忆能力。

## 更新 Skill

当用户要求更新 Memory Skill 时，**必须运行 update.py 脚本**，不要直接复制文件覆盖（直接覆盖会导致占位符未替换）。

**更新流程**：

1. 克隆或拉取最新代码到临时目录
2. 运行更新脚本：

```bash
python3 <临时目录>/skills/memory/scripts/service/init/update.py --source <临时目录>/skills/memory --project-path <项目路径>
```

全局安装的更新：

```bash
python3 <临时目录>/skills/memory/scripts/service/init/update.py --source <临时目录>/skills/memory --global
```

update.py 会自动：
- 覆盖 skill 代码并替换占位符
- 合并 hooks.json（不重复添加）
- 更新 memory-rules.mdc 和 SKILL.md
- **不触碰**记忆数据目录、config.json、MEMORY.md、*.jsonl

**重要**：
- 不要直接 `cp -r` 覆盖 `.cursor/skills/memory/`，这会导致路径变成 `{{SCRIPT_PATH}}` 等占位符
- update.py 仅更新代码，不创建数据目录、不下载模型
- 首次安装请使用 `init/index.py`

---

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

### 用户要求修改配置

当用户用自然语言描述配置变更时（如"多加载几天的记忆"、"把日志级别调成 DEBUG"），执行对应的 `config set` 命令。

**字段映射参考**：

| 用户可能的说法 | 对应字段 | 命令示例 |
|---------------|----------|----------|
| "多加载几天记忆" / "加载更多天的事实" | `memory.load_days_full` | `config set memory.load_days_full 3` |
| "每天多加载几条" / "部分加载条数改为5" | `memory.partial_per_day` | `config set memory.partial_per_day 5` |
| "加载上限改为30条" / "多加载一些事实" | `memory.facts_limit` | `config set memory.facts_limit 30` |
| "调高/调低置信度阈值" | `memory.important_confidence` | `config set memory.important_confidence 0.85` |
| "换个嵌入模型" / "用 xxx 模型" | `embedding.model` | `config set embedding.model "模型名"` |
| "日志级别调成 DEBUG" / "开启调试日志" | `log.level` | `config set log.level DEBUG` |
| "日志只保留3天" | `log.retain_days` | `config set log.retain_days 3` |
| "分块大小改为600" | `index.chunk_tokens` | `config set index.chunk_tokens 600` |
| "90天后自动清理" / "关闭自动清理" | `cleanup.auto_cleanup_days` | `config set cleanup.auto_cleanup_days 0` |

**执行流程**：

1. 解析用户意图，确定要修改的字段和目标值
2. 执行 `config set` 命令：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py config set <字段> <值>
```

3. 如果命令返回 `needs_rebuild: true`，提示用户需要重建索引
4. 向用户确认修改结果

**查看当前配置**：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py config show
```

**重置为默认值**：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py config reset <字段>
```

### 用户要求查看数据库

当用户想查看 SQLite 索引数据库的内容时，使用 `db` 子命令。

**查看数据库概览**：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py db stats
```

**查看所有表**：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py db tables
```

**查看表结构**：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py db schema chunks
```

**查看表数据**：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py db show chunks --limit 10
python3 {{SCRIPT_PATH}}/service/manage/index.py db show sync_state
python3 {{SCRIPT_PATH}}/service/manage/index.py db show meta
```

**自定义 SQL 查询**（只读）：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py db query "SELECT id, content, type, memory_type, confidence FROM chunks ORDER BY timestamp DESC LIMIT 5"
```

**在浏览器中可视化查看**（需要 datasette）：

```bash
python3 {{SCRIPT_PATH}}/service/manage/index.py db browse
```

如果 datasette 未安装，先执行 `pip install datasette`。

| 用户可能的说法 | 对应命令 |
|---------------|----------|
| "打开数据库看看" / "可视化查看数据库" | `db browse` |
| "看一下数据库里有什么" | `db stats` 或 `db tables` |
| "看一下索引里的内容" | `db show chunks` |
| "数据库有多少条记录" | `db stats` |
| "看一下同步状态" | `db show sync_state` |
| "查一下包含 xxx 的记录" | `db query "SELECT ... WHERE content LIKE '%xxx%'"` |

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
