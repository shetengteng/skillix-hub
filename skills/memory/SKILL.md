# Memory Skill

为 Cursor 提供长期记忆能力，自动记录每日对话内容，并在新会话开始时根据用户问题检索相关历史上下文。

## 核心原则

- **零外部依赖**：只使用 Python 标准库
- **利用大模型能力**：让 Cursor 内置的大模型进行语义理解
- **代码数据分离**：Skill 代码可更新，用户数据永不覆盖

## 意图识别（核心入口）

### 意图分类

| 意图类型 | 触发检索 | 信号词示例 |
|----------|---------|-----------|
| 延续性意图 | ✅ | 继续、上次、之前、昨天、我们讨论过、你记得 |
| 偏好相关 | ✅ | 我喜欢、我习惯、按照我的风格 |
| 项目相关 | ✅ | 这个项目、我们的、当前、项目里 |
| 独立问题 | ❌ | Python 怎么读文件（通用知识） |
| 新话题 | ❌ | 换个话题、新问题、另外 |

### 检索决策流程

1. 检查排除信号 → 有则不检索
2. 检查强信号词 → 有则检索
3. 检查弱信号词 → 结合上下文判断
4. 无信号 → 新会话检索，旧会话不检索

### 保存决策

- ✅ **值得保存**：重要决策、用户偏好、项目配置、待办计划、复杂方案
- ❌ **不值得保存**：通用问答、临时调试、闲聊、重复内容

## 检索流程

当需要检索记忆时，执行以下步骤：

### 第一步：意图识别

分析用户问题，识别意图类型：

**强信号词（高置信度触发检索）**：
- 延续性：继续、上次、之前、昨天、我们讨论过、你记得、continue、last time、yesterday
- 偏好：我喜欢、我习惯、按照我的风格、I prefer、my style
- 项目：这个项目、我们的、当前、项目里、this project、our codebase

**排除信号词（不触发检索）**：
- 换个话题、新问题、另外、顺便问一下、change topic、new question

### 第二步：执行检索

如果需要检索，运行以下命令：

```bash
python3 scripts/search_memory.py "用户问题中的关键词"
```

脚本位置：`<skill_dir>/scripts/search_memory.py`

### 第三步：筛选结果

从返回的候选记忆中，选出与用户问题最相关的 1-3 条，作为上下文注入回答。

## 保存流程

当对话结束时，判断是否值得保存：

### 第一步：价值判断

判断本次对话是否包含：
- 重要决策（如技术选型、架构决定）
- 用户偏好（如编码风格、工具选择）
- 项目配置（如 API 设计、命名规范）
- 待办计划（如下一步任务）

### 第二步：提取信息

如果值得保存，提取以下信息：
- **主题**：对话的核心主题（一句话）
- **关键信息**：重要的决策、偏好、配置等（列表形式）
- **标签**：相关标签，以 # 开头

### 第三步：执行保存

运行以下命令保存记忆：

```bash
python3 scripts/save_memory.py '{"topic": "主题", "key_info": ["要点1", "要点2"], "tags": ["#tag1", "#tag2"]}'
```

脚本位置：`<skill_dir>/scripts/save_memory.py`

## 查看流程

当用户想查看记忆时，执行以下命令：

### 查看今日记忆

```bash
python3 scripts/view_memory.py today
```

### 查看指定日期记忆

```bash
python3 scripts/view_memory.py "2026-01-29"
```

### 查看最近 N 天记忆

```bash
python3 scripts/view_memory.py recent 7
```

### 列出所有有记忆的日期

```bash
python3 scripts/view_memory.py list
```

脚本位置：`<skill_dir>/scripts/view_memory.py`

## 删除流程

当用户想删除记忆时，执行以下命令：

### 删除指定记忆

```bash
python3 scripts/delete_memory.py '{"id": "2026-01-29-001"}'
```

### 删除指定日期的所有记忆

```bash
python3 scripts/delete_memory.py '{"date": "2026-01-29"}'
```

### 清空所有记忆

```bash
python3 scripts/delete_memory.py '{"clear_all": true, "confirm": true}'
```

**注意**：清空所有记忆需要 `confirm: true` 参数确认。

脚本位置：`<skill_dir>/scripts/delete_memory.py`

## 导出/导入流程

### 导出记忆

将记忆数据导出为 JSON 文件，便于备份或迁移。

```bash
# 导出所有记忆（默认文件名）
python3 scripts/export_memory.py

# 导出到指定文件
python3 scripts/export_memory.py '{"output": "backup.json"}'

# 导出指定日期范围
python3 scripts/export_memory.py '{"date_from": "2026-01-01", "date_to": "2026-01-15"}'

# 仅导出索引（不含内容）
python3 scripts/export_memory.py '{"include_content": false}'
```

脚本位置：`<skill_dir>/scripts/export_memory.py`

### 导入记忆

从 JSON 文件导入记忆数据。

```bash
# 合并导入（默认，保留现有数据）
python3 scripts/import_memory.py '{"input": "backup.json"}'

# 替换导入（清空现有数据后导入）
python3 scripts/import_memory.py '{"input": "backup.json", "mode": "replace"}'

# 合并导入并覆盖冲突
python3 scripts/import_memory.py '{"input": "backup.json", "overwrite": true}'

# 导入到全局位置
python3 scripts/import_memory.py '{"input": "backup.json", "location": "global"}'
```

脚本位置：`<skill_dir>/scripts/import_memory.py`

## 用户交互命令

| 命令 | 描述 |
|------|------|
| `记住这个` / `save this` | 手动保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |
| `查看今日记忆` | 查看今天的记忆 |
| `查看最近记忆` | 查看最近 7 天的记忆 |
| `删除记忆: xxx` | 删除特定记忆 |
| `清空所有记忆` | 清空所有记忆（需确认） |
| `导出记忆` / `export memories` | 导出所有记忆到 JSON 文件 |
| `导入记忆 xxx` / `import memories xxx` | 从 JSON 文件导入记忆 |

## 配置说明

配置文件位于 `memory-data/config.json`，首次使用时会从 `default_config.json` 复制。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | **总开关**，`false` 完全禁用 |
| `auto_save` | `true` | 自动保存开关 |
| `auto_retrieve` | `true` | 自动检索开关 |
| `storage.location` | `project-first` | 存储位置策略 |
| `storage.retention_days` | `-1` | 记忆保留天数，`-1` 永久保留 |
| `retrieval.max_candidates` | `10` | 关键词筛选候选数量 |
| `retrieval.max_results` | `3` | 最终返回记忆数量 |
| `retrieval.search_scope_days` | `30` | 检索范围天数，`-1` 搜索全部 |
| `retrieval.time_decay_rate` | `0.95` | 时间衰减率 |

## 使用示例

### 示例 1：自动上下文注入

```
[用户]: 继续昨天的 API 重构工作

[Memory Skill]:
检索到相关记忆: 2026-01-28 - API 重构讨论，决定使用 FastAPI

[AI 响应]:
基于昨天的讨论，我们决定使用 FastAPI 替换 Flask。接下来需要...
```

### 示例 2：偏好记忆

```
[历史记忆]: 用户偏好使用 TypeScript，喜欢函数式编程风格

[用户]: 帮我写一个数据处理函数

[AI 响应]: (自动使用 TypeScript + 函数式风格)
```

## 数据存储

### 目录结构

```
<project>/.cursor/skills/
├── memory/                      # Skill 代码（可安全更新）
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── save_memory.py
│   │   ├── search_memory.py
│   │   ├── view_memory.py
│   │   ├── delete_memory.py
│   │   ├── export_memory.py
│   │   ├── import_memory.py
│   │   └── utils.py
│   └── default_config.json
└── memory-data/                 # 用户数据（永不覆盖）
    ├── daily/
    │   └── 2026-01-29.md
    ├── index/
    │   └── keywords.json
    └── config.json
```

### 每日记忆文件格式

```markdown
# 2026-01-29 对话记忆

## Session 1 - 10:30:45

### 主题
Memory Skill 设计讨论

### 关键信息
- 用户希望创建长期记忆功能
- 检索方式：关键词 + 大模型二次筛选

### 标签
#skill #memory #design

---
```

## 记忆权重机制

记忆的最终权重由三个因素综合计算：

```
最终权重 = 关键词匹配分 × 时间衰减系数 × 来源权重
```

| 因素 | 计算方式 | 默认值 |
|------|---------|--------|
| 关键词匹配分 | 匹配数 / 查询词数 | - |
| 时间衰减系数 | rate^天数 | 0.95 |
| 来源权重 | 项目/全局 | 1.0/0.7 |

### 时间衰减参考

| 天数 | 衰减系数 | 说明 |
|------|---------|------|
| 0 (今天) | 1.00 | 无衰减 |
| 7 | 0.70 | 衰减 30% |
| 30 | 0.21 | 衰减 79% |
