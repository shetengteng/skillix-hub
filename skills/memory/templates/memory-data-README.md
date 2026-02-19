# Memory Skill 配置说明

Memory Skill 使用分层配置系统，支持全局、项目级和环境变量三种配置方式。

---

## 配置文件位置

| 层级 | 路径 | 优先级 |
|------|------|--------|
| 代码默认值 | `defaults.py` 中的 `_DEFAULTS` | 最低 |
| 全局配置 | `~/.memory/config.json` | 中 |
| 项目配置 | `{project}/.cursor/skills/memory-data/config.json` | 高 |
| 环境变量 | `MEMORY_*` | 最高 |

加载顺序为低优先级到高优先级，后者覆盖前者的同名字段。

---

## config.json 完整字段

### memory — 记忆加载策略

| 字段 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `memory.load_days_full` | int | 2 | 1–365 | 全量加载的天数，最近 N 天的事实全部加载 |
| `memory.load_days_partial` | int | 5 | 1–365 | 部分加载的天数范围上限，超过 full 但在此范围内的按 `partial_per_day` 条数加载 |
| `memory.load_days_max` | int | 7 | 1–365 | 最大加载天数，超过此范围的事实仅加载高置信度条目 |
| `memory.partial_per_day` | int | 3 | 1–100 | 部分加载阶段每天最多加载的事实条数 |
| `memory.important_confidence` | float | 0.9 | 0.0–1.0 | 高置信度阈值，超过 `load_days_partial` 的事实仅加载置信度 ≥ 此值的条目 |
| `memory.facts_limit` | int | 15 | 1–500 | 单次加载的事实总上限 |

**约束关系**：`load_days_full` < `load_days_partial` < `load_days_max`，系统自动修正不满足约束的值。

### embedding — 嵌入模型

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `embedding.model` | str | `BAAI/bge-small-zh-v1.5` | HuggingFace 模型名称，用于向量搜索 |
| `embedding.cache_dir` | str | `~/.memory/models` | 模型缓存目录，跨项目共享 |

> 修改 `embedding.model` 后需要执行 `rebuild-index --full` 重建索引。

### index — 索引分块

| 字段 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `index.chunk_tokens` | int | 400 | 50–2000 | 文本分块的 token 数上限 |
| `index.chunk_overlap` | int | 80 | 0–500 | 相邻分块的重叠 token 数 |

> 修改这两个字段后需要执行 `rebuild-index --full` 重建索引。
> 约束：`chunk_overlap` 必须小于 `chunk_tokens`，否则自动修正为 `chunk_tokens / 5`。

### log — 日志

| 字段 | 类型 | 默认值 | 可选值 | 说明 |
|------|------|--------|--------|------|
| `log.level` | str | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | 日志级别 |
| `log.retain_days` | int | 7 | 1–365 | 日志文件保留天数，超期自动清理 |

### paths — 路径

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `paths.data_dir` | str | `.cursor/skills/memory-data` | 记忆数据存储目录（相对于项目根目录） |

### cleanup — 自动清理

| 字段 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `cleanup.auto_cleanup_days` | int | 90 | 0–3650 | 自动清理超过 N 天的旧数据，设为 0 禁用 |
| `cleanup.backup_retain_days` | int | 30 | 1–365 | 备份文件保留天数 |

---

## 环境变量

以下环境变量可覆盖对应配置字段（优先级最高）：

| 环境变量 | 对应字段 | 类型 |
|----------|----------|------|
| `MEMORY_LOG_LEVEL` | `log.level` | str |
| `MEMORY_LOAD_DAYS_FULL` | `memory.load_days_full` | int |
| `MEMORY_LOAD_DAYS_MAX` | `memory.load_days_max` | int |
| `MEMORY_FACTS_LIMIT` | `memory.facts_limit` | int |
| `MEMORY_EMBEDDING_MODEL` | `embedding.model` | str |
| `MEMORY_DATA_DIR` | `paths.data_dir` | str |

---

## 需要重建索引的字段

修改以下字段后，必须执行 `manage.py rebuild-index --full` 重建搜索索引：

- `embedding.model`
- `index.chunk_tokens`
- `index.chunk_overlap`

---

## 配置示例

### 项目级 config.json

```json
{
  "version": 1,
  "memory": {
    "load_days_full": 3,
    "facts_limit": 20
  },
  "log": {
    "level": "DEBUG"
  }
}
```

未指定的字段自动使用默认值。

### 通过 CLI 管理配置

```bash
# 查看当前生效配置
python3 .cursor/skills/memory/scripts/service/manage/index.py config show

# 获取单个字段
python3 .cursor/skills/memory/scripts/service/manage/index.py config get memory.facts_limit

# 设置项目级配置
python3 .cursor/skills/memory/scripts/service/manage/index.py config set memory.facts_limit 20

# 设置全局配置
python3 .cursor/skills/memory/scripts/service/manage/index.py config set memory.facts_limit 20 --global

# 重置为默认值
python3 .cursor/skills/memory/scripts/service/manage/index.py config reset memory.facts_limit

# 校验配置
python3 .cursor/skills/memory/scripts/service/manage/index.py config validate
```

---

## 自然语言配置

你可以直接用自然语言让 Agent 修改配置，无需手动编辑 JSON 文件。

### 示例对话

```
用户: 帮我看一下现在的记忆配置
Agent: 当前配置：
       • 全量加载天数: 2 天
       • 部分加载天数: 5 天（每天 3 条）
       • 最大加载天数: 7 天
       • 事实上限: 15 条
       • 嵌入模型: BAAI/bge-small-zh-v1.5
       • 日志级别: INFO

用户: 我想多加载几天的记忆，全量加载改成5天
Agent: 已将 memory.load_days_full 从 2 调整为 5。

用户: 日志级别调成 DEBUG
Agent: 已将 log.level 从 INFO 调整为 DEBUG。

用户: 把事实加载上限改为30条
Agent: 已将 memory.facts_limit 从 15 调整为 30。

用户: 换一个嵌入模型，用 BAAI/bge-base-zh-v1.5
Agent: 已将 embedding.model 更新为 BAAI/bge-base-zh-v1.5。
       注意：更换模型后需要重建索引，是否现在执行？

用户: 把配置恢复默认
Agent: 已将所有配置重置为默认值。
```

### 支持的自然语言指令

| 说法示例 | 对应操作 |
|----------|----------|
| "多加载几天记忆" | 增大 `memory.load_days_full` |
| "每天多加载几条" | 增大 `memory.partial_per_day` |
| "加载上限改为30条" | 设置 `memory.facts_limit` 为 30 |
| "调高置信度阈值" | 增大 `memory.important_confidence` |
| "开启调试日志" | 设置 `log.level` 为 DEBUG |
| "日志只保留3天" | 设置 `log.retain_days` 为 3 |
| "关闭自动清理" | 设置 `cleanup.auto_cleanup_days` 为 0 |
| "换个嵌入模型" | 修改 `embedding.model` |
| "帮我看一下配置" | 执行 `config show` |
| "把配置恢复默认" | 执行 `config reset` |

---

## memory-data 目录结构

```
.cursor/skills/memory-data/
├── config.json          # 项目级配置（可选）
├── MEMORY.md            # 核心记忆（Agent 直接编辑）
├── facts.jsonl          # 全局事实记录
├── sessions.jsonl       # 会话摘要
├── index.sqlite         # 搜索索引（FTS5 + 向量）
├── daily/               # 每日事实
│   └── YYYY-MM-DD.jsonl
└── logs/                # 运行日志
    └── YYYY-MM-DD.log
```
