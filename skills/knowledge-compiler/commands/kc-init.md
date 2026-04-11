# 命令: kc init

在当前目录或指定路径初始化知识库。初始化是一个**多轮交互过程**，AI 必须在每个决策点与用户确认。

## 用法

```
kc init                    # 在当前目录初始化
kc init --path <dir>       # 在指定目录初始化
```

---

## 交互流程

### 步骤 1 — 检查已有配置

检查目标目录是否已存在 `.kc-config.json`。

- **已存在** → 向用户确认：

  > 发现已有知识库配置（`.kc-config.json`）。
  > 当前配置：源目录 `doc/, design/`，语言 `zh`，模式 `recommended`。
  >
  > 重新初始化？（不会删除已有 wiki/ 内容）
  > [1] 是 — 重新配置
  > [2] 否 — 保持当前配置

  用户选 2 → 输出当前配置摘要后结束。
  用户选 1 → 继续步骤 2。

- **不存在** → 继续步骤 2。

---

### 步骤 2 — 扫描并选择源目录

在目标目录中扫描已有 `.md` 文件和目录结构。

**AI 汇报扫描结果并询问：**

> 扫描到以下包含 Markdown 文件的目录：
>
> | 目录 | .md 文件数 | 示例文件 |
> |------|-----------|---------|
> | `doc/` | 12 | system-activity-api.md, user-guide.md |
> | `design/` | 5 | api-gateway.md, auth-flow.md |
> | `src/` | 0 | (无 .md 文件) |
>
> 选择哪些目录作为知识源？
> [1] 使用 `doc/`, `design/`（推荐 — 包含 17 个 .md 文件）
> [2] 自定义选择（输入目录名，逗号分隔）
> [3] 使用默认结构（创建 `raw/designs/`, `raw/decisions/`, `raw/research/`, `raw/notes/`）

**等待用户回答后才继续。不可跳过此步骤。**

- 用户选 1 → 使用推荐目录
- 用户选 2 → 等待用户输入目录列表
- 用户选 3 → 创建默认 raw/ 结构

> **说明**：`raw/` 只是默认的源材料组织方式。如果项目已有文档目录，直接用它们即可。

---

### 步骤 3 — 创建目录结构

**使用自定义 source 目录时**（源目录已存在）：
```
{target}/
└── wiki/
    ├── concepts/
    └── analyses/
```

**使用默认 raw/ 结构时**：
```
{target}/
├── raw/
│   ├── designs/
│   ├── decisions/
│   ├── research/
│   └── notes/
└── wiki/
    ├── concepts/
    └── analyses/
```

仅创建不存在的目录。

---

### 步骤 4 — 选择语言

**AI 询问：**

> Wiki 输出语言?
> [1] zh — 中文（默认）
> [2] en — English

**等待用户回答。** 用户不回答或说"默认"→ 使用 `zh`。

---

### 步骤 5 — 选择会话模式

**AI 询问：**

> AI 如何使用知识库？
> [1] staging     — 辅助参考，需要时查阅 wiki
> [2] recommended — 优先读 wiki，再查原始文件补充（默认）
> [3] primary     — wiki 为主，仅低覆盖部分查原始文件

**等待用户回答。** 用户不回答或说"默认"→ 使用 `recommended`。

---

### 步骤 6 — 生成配置

根据用户在步骤 2-5 中的选择，生成 `.kc-config.json`：

```json
{
  "session_mode": "recommended",
  "language": "zh",
  "sources": ["doc", "design"],
  "output_dir": "wiki",
  "exclude": [],
  "compile_options": {
    "parallel_topics": true,
    "max_parallel": 4
  }
}
```

---

### 步骤 7 — 创建 Wiki 脚手架

创建空的脚手架文件：

**wiki/INDEX.md:**
```markdown
# Wiki 索引

> 由 knowledge-compiler 自动维护。运行 `kc compile` 构建。

尚无编译主题。添加源材料到配置的源目录后运行 `kc compile`。
```

**wiki/log.md:**
```markdown
# 编译日志

> 追加式日志，记录每次编译运行。
```

---

### 步骤 8 — 输出报告

向用户展示最终配置和下一步：

```
知识库初始化完成。

源目录:  doc/, design/
输出:    wiki/
语言:    zh
模式:    recommended

下一步:
  1. 确认源目录中有知识材料
  2. 运行: kc compile
```

---

## 交互规则（强制）

1. **每个决策点必须等待用户回答**，不可自动跳过。
2. **提供明确选项**而非开放式问题——给编号让用户选。
3. **展示扫描结果**让用户做出知情决策，不要隐藏信息。
4. 如果用户说"快速初始化"或"用默认就行"，可以用默认值跳过语言和模式选择，但**源目录选择不可跳过**。
5. 如果发现项目中完全没有 `.md` 文件，主动告知用户并建议创建默认 `raw/` 结构。
