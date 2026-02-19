# Memory Skill — Cursor 跨会话记忆系统

让 Cursor Agent 拥有跨会话的持久记忆能力。通过 Hooks 自动触发记忆加载、事实提取、摘要保存和索引同步，配合本地嵌入模型实现语义搜索。

---

## 核心机制

```
sessionStart → 加载记忆（MEMORY.md + daily/*.jsonl + sessions.jsonl）
     ↓
  [对话进行中]
     ↓
preCompact   → 上下文即将压缩，提示 Agent 提取关键事实
     ↓
   stop      → 任务完成，提示 Agent 保存会话摘要
     ↓
sessionEnd   → 静默同步 JSONL → SQLite 索引 + 记录元数据 + 清理日志
```

## 目录结构

```
skills/memory/           ← 源码（开发用）
├── scripts/
│   ├── core/                  # 纯基础设施（无业务逻辑）
│   │   ├── utils.py           #   时间/ID 工具
│   │   ├── embedding.py       #   嵌入模型 + 向量生成
│   │   └── file_lock.py       #   文件互斥锁
│   ├── storage/               # 数据存储层
│   │   ├── sqlite_store.py    #   SQLite CRUD + schema
│   │   ├── sqlite_search.py   #   FTS5 + 向量搜索
│   │   ├── jsonl.py           #   JSONL 读取 + 衰减策略
│   │   ├── jsonl_manage.py    #   JSONL 管理操作
│   │   └── chunker.py         #   Markdown 文本分块
│   └── service/               # 业务逻辑
│       ├── config/            #   配置服务
│       │   ├── defaults.py            # _DEFAULTS / _SCHEMA / 常量
│       │   └── manager.py            # Config 分层加载器
│       ├── logger/            #   日志服务
│       │   └── logger.py             # 按天轮转 → memory-data/logs/
│       ├── hooks/             #   Cursor Hook 入口
│       │   ├── load_memory.py         # sessionStart
│       │   ├── flush_memory.py        # preCompact
│       │   ├── prompt_session_save.py # stop
│       │   └── sync_and_cleanup.py    # sessionEnd
│       ├── init/              #   初始化/安装
│       │   ├── index.py               # 安装主入口
│       │   └── helpers.py             # 安装辅助函数
│       ├── memory/            #   记忆操作
│       │   ├── save_fact.py           # 事实保存 CLI
│       │   ├── save_summary.py        # 摘要保存 CLI
│       │   ├── search_memory.py       # 语义搜索
│       │   └── sync_index.py          # JSONL → SQLite 增量同步
│       └── manage/            #   管理工具
│           ├── index.py               # 管理主入口
│           └── commands/              # 子命令模块
├── templates/                 # 安装模板
│   ├── hooks.json
│   ├── memory-rules.mdc
│   └── MEMORY.md
├── requirements.txt
├── SKILL.md
└── README.md
```

## 安装

### 本地安装（推荐）

```bash
python3 skills/memory/scripts/service/init/index.py --project-path /path/to/your/project
```

### 全局安装

```bash
python3 skills/memory/scripts/service/init/index.py --global
```

### 跳过模型下载

```bash
python3 skills/memory/scripts/service/init/index.py --skip-model
```

安装后自动完成：
- 复制 skill 代码到 `.cursor/skills/memory/`
- 创建 `.cursor/hooks.json`（合并已有配置）
- 创建 `.cursor/rules/memory-rules.mdc`
- 创建 `.cursor/skills/memory-data/` 数据目录
- 下载嵌入模型到 `~/.memory/models/`（全局缓存）

## 数据存储

安装后，记忆数据存储在 `.cursor/skills/memory-data/`：

| 文件 | 用途 | 写入方 |
|------|------|--------|
| `MEMORY.md` | 核心记忆（Agent 直接编辑） | Agent |
| `daily/YYYY-MM-DD.jsonl` | 每日事实 + 系统事件 | save_fact.py / Hooks |
| `sessions.jsonl` | 会话摘要 | save_summary.py |
| `index.sqlite` | 搜索索引（FTS5 + 向量） | sync_index.py |

## 记忆衰减策略

`sessionStart` 加载事实时采用"近多远少"策略：

| 时间范围 | 加载策略 |
|----------|----------|
| 最近 2 天 | 全部加载 |
| 3-5 天前 | 每天最新 3 条 |
| 5-7 天前 | 仅高置信度（≥0.9） |
| 7 天以上 | 不加载 |
| 总上限 | 15 条 |

## 嵌入模型

- **开发环境**：BAAI/bge-small-zh-v1.5（96MB，中英文支持）
- **缓存位置**：`~/.memory/models/`（跨项目共享）
- 首次使用时自动下载，后续从缓存加载

## 搜索

Agent 可通过 `search_memory.py` 搜索历史记忆：

```bash
# 全文搜索
python3 .cursor/skills/memory/scripts/service/memory/search_memory.py "关键词" --method fts

# 向量语义搜索
python3 .cursor/skills/memory/scripts/service/memory/search_memory.py "模糊描述" --method vector

# 混合搜索（推荐）
python3 .cursor/skills/memory/scripts/service/memory/search_memory.py "查询" --method hybrid
```

## 自然语言交互示例

安装完成后，直接在 Cursor 中用自然语言与 Agent 对话即可。以下是完整的交互场景：

### 自动行为（无需干预）

| 场景 | 触发条件 | Agent 行为 |
|------|----------|------------|
| 新会话开始 | 打开 Cursor / 开始新对话 | 自动加载 MEMORY.md + 近期事实 + 上次摘要 |
| 长对话压缩 | 上下文接近阈值时 | 静默提取关键事实并保存（用户不可见） |
| 任务完成 | 对话正常结束 | 静默保存会话摘要和待办事项 |

### 记忆保存

```
用户: 记住这个：我们的代码规范要求所有函数必须有 docstring
Agent: 已记录到核心记忆中。以后我会确保所有函数都包含 docstring。

用户: 我们决定使用 PostgreSQL 作为主数据库，不用 MySQL
Agent: （Agent 在回复中继续正常对话的同时，静默执行 save_fact 保存这个技术决策）
```

### 记忆检索

```
用户: 继续昨天的 API 重构工作
Agent: 根据之前的记忆，昨天我们讨论了：
       • 使用 FastAPI 替换 Flask
       • RESTful 风格设计，路径前缀 /api/v2
       • 待办：实现认证中间件
       我们从认证中间件开始吧。

用户: 搜索一下我们之前关于数据库的讨论
Agent: 找到 3 条相关记忆：
       1. [W] 项目使用 PostgreSQL 数据库（置信度 0.95）
       2. [W] 数据库连接池配置为最大 20 个连接
       3. [S] 会话摘要：讨论了数据库选型方案

用户: 我们之前决定用什么做缓存？
Agent: 根据记忆，你们决定使用 Redis 做缓存层，TTL 设为 300 秒。
```

### 记忆管理

```
用户: 帮我看一下记忆统计
Agent: 📊 记忆统计
       • 核心记忆: 856 字符
       • 事实记录: 47 条（W:28 / B:11 / O:8）
       • 会话摘要: 12 条
       • 磁盘占用: 156 KB

用户: 删除关于 MySQL 的记忆
Agent: 找到 2 条包含 "MySQL" 的记忆，已删除。索引已更新。

用户: 帮我看一下现在的配置
Agent: 当前配置：
       • 嵌入模型: BAAI/bge-small-zh-v1.5
       • 最大加载事实数: 15
       • 搜索方法: hybrid
```

### 跨会话场景

```
=== 会话 A ===
用户: 我们决定用 Redis 做缓存层，TTL 300 秒
Agent: 好的，使用 Redis 缓存，TTL 300 秒。
用户: 好了今天就到这里
Agent: 再见！（自动保存会话摘要）

=== 会话 B（新开对话）===
用户: 我们之前决定用什么做缓存？TTL 是多少？
Agent: 根据之前的记忆，你们决定使用 Redis 做缓存层，TTL 设为 300 秒。
```

## 测试

从项目根目录运行全量测试：

```bash
python3 tests/memory/run_tests.py
```

测试报告自动输出到 `tests/memory/reports/`。

## 开发流程

1. 在 `skills/memory/` 源码目录开发
2. 运行测试验证
3. 通过 `init.py` 安装到 `.cursor/skills/memory/`
4. 实际使用中验证 Hook 触发

## Hook 配置

| Hook 事件 | 脚本 | 功能 |
|-----------|------|------|
| `sessionStart` | `load_memory.py` | 加载记忆到 Agent 上下文 |
| `preCompact` | `flush_memory.py` | 上下文压缩前提取事实 |
| `stop` | `prompt_session_save.py` | 任务完成后保存摘要 |
| `sessionEnd` | `sync_and_cleanup.py` | 索引同步 + 元数据记录 |

## 依赖

- Python 3.9+
- sentence-transformers（可选，用于向量搜索）
