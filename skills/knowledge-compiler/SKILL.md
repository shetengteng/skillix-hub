---
name: knowledge-compiler
version: 0.2.0
description: 将知识材料编译为结构化 Wiki。AI 即编译器，Markdown-in Markdown-out，覆盖度追踪，增量编译。
triggers:
  - 知识编译
  - knowledge compiler
  - kc
  - wiki compile
  - 知识库
  - 编译知识
  - kc init
  - kc compile
  - kc query
  - kc lint
platforms:
  - cursor
  - claude-code
  - codex
---

# Knowledge Compiler

将团队知识材料（设计文档、架构决策、技术调研、会议纪要）编译为结构化 Wiki，让人和 AI 都能高效使用。

**核心理念**：AI 即编译器 — 读取本文件的指令，扫描文件、分类主题、生成 Wiki 文章。纯 Markdown，零代码，零依赖。

## 跨平台兼容

本 Skill 兼容所有支持读取 Markdown 指令的 AI IDE：
- **Cursor**：作为 Skill 安装，AI 读取 SKILL.md 及引用文件执行
- **Claude Code**：作为 Skill 或 AGENTS.md 引用使用
- **Codex**：作为 Skill 读取，AI 按指令执行

所有命令的详细步骤存储在本目录的 `.md` 文件中（见下方命令路由表）。AI 读取对应文件后自行执行，不依赖任何 IDE 特定的命令注册机制。

## 命令路由

当用户表达以下意图时，读取对应的指令文件并按步骤执行：

| 用户意图 | 指令文件 | 说明 |
|---------|---------|------|
| "kc init" / "初始化知识库" | [commands/kc-init.md](commands/kc-init.md) | 创建源目录 + wiki/ + 配置 |
| "kc add" / "添加材料" | [commands/kc-add.md](commands/kc-add.md) | 添加文件到源目录 |
| "kc compile" / "编译" / "compile" | [commands/kc-compile.md](commands/kc-compile.md) | 编译 Wiki（增量/全量/预览） |
| "kc query" / "问一下" / "查知识库" | [commands/kc-query.md](commands/kc-query.md) | 基于 Wiki 回答问题 |
| "kc lint" / "健康检查" / "检查质量" | [commands/kc-lint.md](commands/kc-lint.md) | Hard/Soft Gate 检查 |
| "kc status" / "知识库状态" | [commands/kc-status.md](commands/kc-status.md) | 统计、覆盖度、过期概览 |
| "kc browse" / "浏览知识库" | [commands/kc-browse.md](commands/kc-browse.md) | 知识地图浏览 |

编译命令内部调用 [skills/wiki-compiler.md](skills/wiki-compiler.md) 执行 5 阶段管道。

## 编译管道概览

```
Phase 1: Scan    — 读 .compile-state.json，对比源文件 mtime，找出 new/changed/deleted
Phase 2: Classify — 读标题+前500字，推断 topic slug，匹配已有概念
Phase 3: Compile  — 读全文，生成/更新概念文章，标记覆盖度，标注来源
Phase 3.5: Schema — 首次生成 / 增量更新 schema.md
Phase 4: Index    — 更新 INDEX.md + Hard Gate 验证
Phase 5: State    — 更新 .compile-state.json + log.md
```

详细管道指令见 [skills/wiki-compiler.md](skills/wiki-compiler.md)。

## 知识库目录结构

```
{project}/
├── .kc-config.json              # 配置
├── .compile-state.json          # 编译状态（mtime 快照）
├── {sources}/                   # 源目录（只读约定，默认 raw/，也可使用 doc/、design/ 等已有目录）
│   ├── designs/                 # ← 使用默认 raw/ 结构时的子目录
│   ├── decisions/
│   ├── research/
│   └── notes/
└── wiki/                        # 编译产物
    ├── INDEX.md                 # 概念索引（分类 + 覆盖度）
    ├── schema.md                # 结构契约（分类 + 命名规则 + 交叉引用）
    ├── log.md                   # 编译日志
    ├── concepts/
    │   └── {topic-slug}.md      # 概念文章（frontmatter + 覆盖度标记）
    └── analyses/
        └── {date}-{slug}.md     # 保存的查询分析（kc query --save 产物）
```

## 覆盖度标记

| 级别 | 含义 | AI 行为 |
|------|------|---------|
| high | 多个一致来源 | 直接引用 |
| medium | 单一来源 | 引用但标注"可能需补充" |
| low | 推断或稀疏 | 自动回查源目录中的原始文件 |

详细说明见 [references/coverage-tags.md](references/coverage-tags.md)。

## 输出语言

配置 `.kc-config.json` 中的 `language`：

| 值 | 含义 |
|----|------|
| `zh` | 中文（默认）— 文章正文、章节标题、摘要均为中文 |
| `en` | English — 章节标题和正文切换为英文（按 wiki-compiler.md 中的映射表） |

模板骨架为中文（默认语言）。`language=en` 时，编译器按映射表将章节标题替换为英文，正文用英文生成。YAML frontmatter key 始终为英文。

## 会话模式

配置 `.kc-config.json` 中的 `session_mode`：

| 模式 | 行为 |
|------|------|
| staging | Wiki 可用，按需查阅 |
| recommended | 先读 Wiki 再读原始文件 |
| primary | Wiki 为主，low 覆盖才看源目录 |

进入含 `.kc-config.json` 的目录时自动识别，未找到则静默退出。

## 质量保障

采用 Hard/Soft Gate 分级验证，详见 [references/quality-gates.md](references/quality-gates.md)。

- **Hard Gates**（必须通过）：frontmatter 完整、覆盖度标记、来源引用有效、schema 一致、非空内容
- **Soft Gates**（警告不阻断）：孤立概念、低覆盖集群、过期文档、内容矛盾、断裂链接

## 交互原则

编译过程中 AI **必须在不确定时暂停并向用户确认**，不可擅自决定：
- 主题归属不明确（一个文件可能属于多个主题）
- 新主题与现有主题名称相近（合并还是新建）
- 源文件之间存在矛盾
- 用户手动编辑与新源冲突
- Hard Gate 失败且无法自动修复

详细的确认场景和规则见 [skills/wiki-compiler.md](skills/wiki-compiler.md) 的"交互式确认"章节。

## AI 渐进式披露协议

生成的知识库面向 AI 消费。AI 按以下层级逐步深入，避免一次性读取所有内容：

```
Layer 0: .kc-config.json       → 知识库是否存在、源目录、语言、模式
Layer 1: wiki/INDEX.md          → 全部主题列表、摘要、覆盖度（快速扫描）
Layer 2: wiki/concepts/*.md     → 仅读 YAML frontmatter（summary、tags、answers）
Layer 3: wiki/concepts/*.md     → 读完整文章正文
Layer 4: 源目录中的原始文件       → 仅在 low 覆盖或需要验证时读取
```

**规则：**
1. **Layer 1 是入口**。AI 收到知识相关问题时，**先读 INDEX.md**，不要直接读 concepts/。
2. **Layer 2 做匹配**。通过 frontmatter 的 `summary`、`tags`、`answers` 判断哪些文章与问题相关，不需要读全文。
3. **Layer 3 按需读取**。只读与问题相关的文章，且优先读 high/medium 覆盖度的章节。
4. **Layer 4 最后手段**。仅在 low 覆盖度章节不足以回答，或 `session_mode=recommended/primary` 要求验证时才读原始文件。

**Frontmatter 快速匹配字段：**
- `summary`：2-3 句概述，AI 据此判断文章是否与问题相关
- `tags`：关键词列表，用于语义匹配
- `answers`：该文章能回答的典型问题列表，AI 据此做精准路由

## 核心约定

1. **AI 是编译器**：不运行外部脚本，AI 读取指令文件后自己执行所有步骤
2. **源目录不可变**：编译器永远不修改源目录下的文件
3. **人机共维**：用户手动编辑的内容在重编译时保留
4. **按需加载**：AI 只在需要时读取对应的指令文件和参考文档，避免一次性加载所有内容
5. **不确定则问**：遇到歧义时暂停向用户确认，不擅自选择
6. **Mermaid 图表**：每篇编译的 wiki 文章至少包含 1 个 mermaid 流程图/架构图，辅助可视化理解

## Skill 文件结构

```
skills/knowledge-compiler/
├── SKILL.md                      # 本文件（入口 + 命令路由）
├── commands/                     # 命令指令（AI 读取后执行）
│   ├── kc-init.md
│   ├── kc-add.md
│   ├── kc-compile.md
│   ├── kc-query.md
│   ├── kc-lint.md
│   ├── kc-status.md
│   └── kc-browse.md
├── skills/
│   └── wiki-compiler.md          # 5阶段编译管道（核心逻辑）
├── templates/                    # 生成内容时使用的模板
│   ├── article.md
│   ├── schema.md
│   └── index.md
└── references/                   # 详细规范（按需加载）
    ├── quality-gates.md
    └── coverage-tags.md
```
