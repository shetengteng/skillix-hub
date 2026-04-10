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

## AI Agent 标准工作流

Knowledge Compiler 是 **AI-first 工具**，设计为 AI Agent 在对话中直接调用。以下是推荐的使用模式：

### 模式 1：快速编译（增量）

```bash
KC="python3 skills/knowledge-compiler/main.py"
$KC compile                        # 扫描变更、分类、生成 prompt + stub
# AI Agent 读取 .kc-compile-prompt.md，执行精细编译
$KC apply result.md                # 将 AI 编译结果写回（自动 merge 保留用户编辑）
$KC lint                           # 质量检查
```

### 模式 2：精细编译（单概念）

```bash
$KC compile --topic api-gateway --dry-run  # 预览分类
$KC compile --topic api-gateway            # 编译单个概念
# AI Agent 执行精细编译...
$KC apply result.md --slug api-gateway     # 写回指定概念
```

### 模式 3：查询沉淀

```bash
$KC query "微服务间的通信方式有哪些？" --save  # 查询并保存为草稿概念
$KC compile                                     # 下次编译时自动完善草稿
```

### 模式 4：质量巡检

```bash
$KC lint           # 查看 Hard Gate / Soft Gate 报告
$KC lint --fix     # 自动修复 schema 同步问题
$KC status         # 查看覆盖度分布和过期概念
$KC browse         # 浏览知识地图
```

> **关键约定**：`compile` 生成编译 prompt，AI Agent 执行后通过 `apply` 写回。这是两段式设计，
> 不是缺陷——AI Agent 在一次对话中可以原子化执行整个管道。

## 命令列表

| 命令 | 说明 |
|------|------|
| `init` | 初始化知识库（创建 raw/ + wiki/ + 配置） |
| `add <path> [--tags T] [--category C]` | 添加材料到 raw/ |
| `compile [--full\|--dry-run\|--topic SLUG]` | 编译 Wiki（增量/全量/预览/单概念） |
| `apply <result-path> [--slug SLUG]` | 将 AI 编译结果写回概念文章（经 section merge） |
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
