---
name: knowledge-compiler
version: 0.1.0
description: 将团队知识材料编译为结构化、有覆盖度标记的 Wiki。Markdown-first，支持增量编译、覆盖度追踪、过期检测。
triggers:
  - 知识编译
  - knowledge compiler
  - kc
  - wiki compile
  - 知识库
  - 编译知识
---

# Knowledge Compiler

将团队的知识材料（设计文档、架构决策、技术调研、会议纪要）编译为结构化 Wiki，让人和 AI 都能高效使用。

## 核心特性

- **Markdown-first**：输入是 Markdown，输出是 Markdown，用户可直接编辑
- **覆盖度追踪**：每个章节标记 high/medium/low，让 AI 知道何时需要回查原始文件
- **增量编译**：基于 mtime 检测变更，只重编译有变化的概念
- **人机共维**：编译器保留用户手动编辑，Schema 由人和编译器共同维护

## 快速开始

```bash
SKILL_PATH="skills/knowledge-compiler"

# 初始化知识库
python3 $SKILL_PATH/main.py init

# 添加材料
python3 $SKILL_PATH/main.py add raw/designs/my-design.md --tags "architecture"

# 编译
python3 $SKILL_PATH/main.py compile

# 查询
python3 $SKILL_PATH/main.py query "XXX 的设计取舍是什么？"

# 健康检查
python3 $SKILL_PATH/main.py lint
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `init` | 初始化知识库（创建 raw/ + wiki/ + 配置） |
| `add <path> [--tags T] [--category C]` | 添加材料到 raw/ |
| `compile [--full\|--dry-run\|--topic SLUG]` | 编译 Wiki（增量/全量/预览/单概念） |
| `query <question> [--save]` | 基于 Wiki 回答问题 |
| `lint [--fix]` | 健康检查 + 可选自动修复 |
| `status` | 知识库状态总览 |
| `browse [category]` | 知识地图浏览 |

## 目录结构

```
{project}/
├── .kc-config.json              # 配置
├── .compile-state.json          # 编译状态
├── raw/                         # 原始材料（只读）
│   ├── designs/
│   ├── decisions/
│   ├── research/
│   └── notes/
└── wiki/                        # 编译产物
    ├── INDEX.md
    ├── schema.md
    ├── log.md
    └── concepts/
        └── {topic-slug}.md
```

## 覆盖度标记

每个概念文章的每个章节标记覆盖度：

| 级别 | 含义 | AI 行为 |
|------|------|---------|
| high | 多个一致来源 | 直接引用 |
| medium | 单一来源 | 引用但标注"可能需补充" |
| low | 推断或稀疏 | 自动回查 raw/ 原始文件 |

## 会话模式

配置 `.kc-config.json` 中的 `session_mode`：

| 模式 | 行为 |
|------|------|
| staging | Wiki 可用，按需查阅 |
| recommended | 先读 Wiki 再读原始文件 |
| primary | Wiki 为主，low 覆盖才看 raw/ |
