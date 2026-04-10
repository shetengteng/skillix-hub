# Knowledge Compiler — 纯 Markdown Skill 设计 (v3)

> 日期：2026-04-10
> 架构：纯 Markdown，AI 即编译器，零代码，零依赖
> 设计来源：llm-wiki-compiler（~60%）+ project-knowledge-base-nex（~30%）+ 新增（~10%）

---

## 1. 核心定位

**一句话**：将知识材料编译为结构化、有覆盖度标记的 Wiki，AI Agent 读取 Markdown 指令自行执行编译。

**与 v1/v2 的根本区别**：
- v1/v2：Python CLI（typer），AI 运行 `python3 main.py compile`，Python 代码是编译器
- **v3：纯 Markdown Skill，AI 读取指令文件后自己扫描、分类、编译，AI 本身就是编译器**

---

## 2. 架构决策

| 决策 | 选择 | 舍弃 | 理由 |
|------|------|------|------|
| 实现方式 | 纯 Markdown 指令 | Python CLI | AI 自身能力足够完成扫描、分类、生成，不需要 Python 脚本 |
| 跨平台 | Cursor + Claude Code + Codex | 单平台绑定 | 纯 Markdown 无 IDE 特定依赖 |
| 命令分发 | SKILL.md 命令路由表 + 引用 .md 文件 | IDE commands/ 注册 | 不依赖 IDE 特定的命令注册机制 |
| 编译管道 | 5 阶段（from llm-wiki） | 3 步引擎（from PKB） | 5 阶段对知识编译更精确（扫描→分类→编译→索引→状态） |
| 覆盖度 | 章节级 3 级（high/medium/low） | 文档级 5 维评分 | 章节粒度更精确，AI 知道具体哪段需要回查 |
| 质量门控 | Hard/Soft Gate 分级（from PKB） | 统一报告 | 分级更实用：Hard Gate 阻断错误，Soft Gate 仅警告 |
| SKILL.md 长度 | ~130 行入口 + 引用文件 | 600 行单文件 | 减少 Token 消耗，AI 按需加载详细指令 |

---

## 3. Skill 文件结构

```
skills/knowledge-compiler/
├── SKILL.md                      # 入口 + 命令路由（~130行）
├── commands/                     # 命令指令（AI 读取后执行步骤）
│   ├── kc-init.md                # 初始化知识库
│   ├── kc-add.md                 # 添加材料
│   ├── kc-compile.md             # 触发编译
│   ├── kc-query.md               # 知识问答
│   ├── kc-lint.md                # 健康检查
│   ├── kc-status.md              # 状态概览
│   └── kc-browse.md              # 知识浏览
├── skills/
│   └── wiki-compiler.md          # 5阶段编译管道（核心逻辑）
├── templates/                    # 生成时使用的模板
│   ├── article.md                # 概念文章模板
│   ├── schema.md                 # Schema 模板
│   └── index.md                  # INDEX 模板
└── references/                   # 详细规范（按需加载）
    ├── quality-gates.md          # Hard/Soft Gate 定义
    └── coverage-tags.md          # 覆盖度标记使用指南
```

---

## 4. 知识库目录结构（编译产物）

```
{project}/
├── .kc-config.json              # 配置（session_mode, sources, output_dir）
├── .compile-state.json          # 编译状态（文件 mtime 快照）
├── raw/                         # 原始材料（只读约定）
│   ├── designs/
│   ├── decisions/
│   ├── research/
│   └── notes/
└── wiki/                        # 编译产物
    ├── INDEX.md                 # 概念索引
    ├── schema.md                # 结构契约
    ├── log.md                   # 编译日志
    └── concepts/
        └── {topic-slug}.md      # 概念文章
```

---

## 5. 编译管道

```
Phase 1: Scan
  读 .compile-state.json → 对比 raw/ 文件 mtime → 产出 new/changed/deleted 三个列表

Phase 2: Classify
  读变更文件标题+前500字 → 推断 topic slug → 匹配已有概念 → 产出 topic_map

Phase 3: Compile
  读源文件全文 → 生成/更新概念文章 → 标记覆盖度 → 标注来源引用 → 保留用户手动编辑

Phase 3.5: Schema
  首次生成 schema.md / 后续增量更新 → 不覆盖手动编辑

Phase 4: Index + Verify
  更新 INDEX.md → 运行 Hard Gate 检查 → 运行 Soft Gate 检查

Phase 5: State + Log
  更新 .compile-state.json → 追加 log.md
```

---

## 6. 来源追溯

### 来自 llm-wiki-compiler（~60%）

- 5 阶段编译管道骨架
- 覆盖度 3 级标记（high/medium/low）
- Schema 人机共维契约
- 会话模式（staging/recommended/primary）
- `[[slug]]` 交叉引用 + `[source: path]` 来源引用
- Raw 不可变原则
- `.compile-state.json` mtime 状态管理
- 概念文章模板结构
- 纯 Markdown 架构（commands/ 是 .md 指令文件）

### 来自 PKB（~30%）

- Hard/Soft Gate 分级验证
- YAML frontmatter 元数据标准
- 过期检测时间窗口（30 天）
- 保留用户手动编辑策略
- 按需加载（SKILL.md 精简 + references/ 详细文档）

### 新增（~10%）

- `kc add` 命令
- `kc status` 状态概览
- `kc browse` 知识浏览
- 跨平台兼容设计（Cursor + Claude Code + Codex）
