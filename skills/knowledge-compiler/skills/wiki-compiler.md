# Skill: wiki-compiler

## 用途

将 Markdown 知识库编译为结构化、AI 可查询的 wiki。自动发现主题，按章节追踪覆盖度置信度，支持基于变更的增量重编译。

## 激活条件

当用户调用 `kc compile`，或其他命令委托给 wiki-compiler 时激活。

---

## 输入

读取项目根目录的 `.kc-config.json` 获取配置：

```json
{
  "session_mode": "recommended",
  "language": "zh",
  "sources": ["doc"],
  "output_dir": "wiki",
  "exclude": [],
  "compile_options": {
    "parallel_topics": true,
    "max_parallel": 4
  }
}
```

**语言配置：** `language` 字段控制生成的 wiki 内容语言。
- `"zh"` — 中文（默认）。文章正文、章节标题、摘要、覆盖度注释均为中文。YAML frontmatter key 保持英文。
- `"en"` — English。
- 语言设置仅影响**生成的内容**。源文件以其原始语言读取。

---

## 编译管道（5 阶段）

### Phase 1 — 扫描源文件

1. 读取 `.compile-state.json` 获取上次编译快照（文件路径 + mtime）。
2. 遍历 `sources` 中列出的所有目录。
3. 对找到的每个 `.md` 文件，获取当前修改时间：
   ```bash
   stat -f "%m" <file>     # macOS
   stat -c "%Y" <file>     # Linux
   ```
4. 对比当前 mtime 与快照。
5. 生成三个列表：`new_files`、`changed_files`、`deleted_files`。
6. 如果设置了 `--full` 标志，无论状态如何，将所有源文件视为已变更。
7. 如果 `.compile-state.json` 不存在，将所有文件视为新增。

**输出：** `scan_result = { new, changed, deleted }`

**快速退出：** 如果三个列表都为空，报告"无需编译——所有主题已是最新。"并停止。

---

### Phase 2 — 分类与发现主题

对 `new_files + changed_files` 中的每个文件：
1. 读取：文件路径、H1 标题（无 H1 则用文件名）、前 500 字符内容。
2. 推断主题 slug：`lowercase-kebab-case`（如 `api-gateway-design`、`event-driven-architecture`）。
3. 按主题分组。一个文件如果涵盖不同主题，可以属于多个主题。
4. 与现有 `wiki/INDEX.md` 交叉引用，尽量复用已有的主题 slug。
5. 标记真正的新主题供 Phase 3 创建文章。

**输出：** `topic_map = { topic_slug: [file_paths] }`

**规则：**
- 优先合并到已有主题，而非创建新主题。
- 不确定时询问用户："发现内容可能属于 `topic-a` 或 `topic-b`——哪个更合适？"
- 如果指定了 `--topic <slug>`，仅处理该单一主题。

---

### Phase 3 — 编译主题文章

对每个有变更源文件的主题：

1. **完整读取**该主题的所有源文件。
2. **检查** `wiki/concepts/{topic-slug}.md` 是否已存在。
   - 已存在：读取当前文章，识别用户编辑的章节（无 `[source: ...]` 引用的章节，或用户修改了编译器生成内容的章节）。保留这些。
   - 新建：从 `templates/article.md` 创建。
3. **生成**文章内容（使用配置中指定的 `language`）：

   **语言处理规则：**
   - 模板骨架是中文（默认 `zh`）。当 `language=zh` 时，直接使用中文章节名和中文正文。
   - 当 `language=en` 时，使用以下映射替换章节名，正文用英文：

     | 模板中文 | English |
     |---------|---------|
     | 概要 | Summary |
     | 关键决策 | Key Decisions |
     | 当前状态 | Current State |
     | 注意事项 | Gotchas |
     | 待解决问题 | Open Questions |
     | 相关概念 | Related |
     | 来源 | Sources |
     | 主题分类 | Topic Taxonomy |
     | 未分类 | Uncategorized |
     | Wiki 索引 | Wiki Index |
     | 分析记录 | Analyses |
     | 统计 | Stats |
   - 用源材料中的**详尽、深入**综合填充模板的每个章节。
   - **深度要求：**
     - **概要**：5-10 句。涵盖是什么、为什么重要、在系统中的定位、关键特征。包含源材料中的具体细节（字段名、路径、格式）。
     - **关键决策**：提取源材料中的每一个设计决策、权衡和架构选择。每条决策说明选择内容 + 理由 + 考虑过的替代方案。目标 3-8 条。
     - **当前状态**：描述完整的当前实现状态。包含数据模型、API 端点、配置详情、数据库 schema——源材料中提供的所有信息。结构化数据用表格呈现。
     - **注意事项**：提取所有陷阱、边界情况、非直觉行为。如果源材料提到不一致、格式问题或意外行为，逐条列出。
     - **待解决问题**：仅列出真正未解决的问题。不要编造——只列出源材料中留下的开放问题。
   - 如果源材料内容丰富（>100 行），编译的文章应至少同等详细。**不要过度概括。** 保留字段名、端点路径、数据格式、SQL schema、代码示例等具体细节。
   - **Mermaid 图表（场景化推荐，非强制）：** 以下类型的 topic 推荐包含 mermaid 图表：
     - 架构类（组件关系）→ `graph` 或 `classDiagram`
     - 流程类（工作流、生命周期）→ `flowchart` 或 `sequenceDiagram`
     - 状态机类（状态转换）→ `stateDiagram-v2`
   - 以下类型**不强制**：概念解释类、FAQ 类、配置说明类。
   - 图表语法使用 markdown 代码块 ` ```mermaid `。
   - 图表中的文字遵循 `language` 配置。
   - **判断原则**：如果图表对 AI 检索没有帮助（AI 不依赖图表做召回），则不必添加。
   - **Frontmatter 检索字段约束（渐进式披露 Layer 2）：**

     **`summary`（1-3 句，必须包含主题专有名词）：**
     - 不允许只写泛化描述（如"这是一个设计文档"）
     - 必须包含：该主题做什么、覆盖哪些关键概念
     - 好例子："系统活动 API 提供控制台活动、请求历史、审计日志三个分页查询端点，支持 JWT 认证和灵活过滤。"
     - 坏例子："系统活动相关的 API 接口。"

     **`tags`（3-12 个，至少覆盖 3 类）：**
     - 技术术语（如 api, jwt, pagination）
     - 组件/模块名（如 console-tracking, audit-log）
     - 业务域关键词（如 system-activity, user-behavior）
     - 不要只用泛化标签（如 design, document, system）

     **`answers`（3-5 个自然语言问题句）：**
     - 必须是问句（以？结尾）
     - 应直接反映该 topic 的回答边界
     - 好例子："系统活动 API 支持哪些查询类型？"
     - 坏例子："系统活动 API 的说明"（不是问句）
     - 不同 topic 的 answers 应互不重叠——如果两个 topic 能回答同一个问题，说明主题边界不清
   - 为每个章节标注**覆盖度**：
     - `high` — 多个来源，一致，文档充分
     - `medium` — 单一来源或部分覆盖
     - `low` — 推断或稀疏；读者应核查原始文件
   - 在引用源信息的地方添加 `[source: path/to/file.md]` 行内引用。
4. **与现有内容合并：**
   - 编译器生成的章节（带 `[source: ...]`）：用新综合内容更新。
   - 用户编辑的章节（无来源引用或手动调整过的）：保留用户版本。
   - 来自之前未涵盖的源的新章节：追加。

**并行处理：** 如果 `compile_options.parallel_topics` 为 true 且有 3 个以上主题要编译，按批次并行处理（最多 `max_parallel` 个）。

**输出：** 更新或创建的 `wiki/concepts/{topic-slug}.md` 文件。

---

### Phase 3.5 — Schema

- **首次运行：** 从 `templates/schema.md` 生成 `wiki/schema.md`。从已编译文章中推断主题分类、命名规范和交叉引用规则。
- **后续运行：** 仅在新增主题或现有主题重组时增量更新 schema。永远不覆盖 schema.md 中的手动编辑。
- Schema 是人和编译器之间的共享契约。在主题命名和分类方面以它为准。

---

### Phase 4 — 更新索引 + 验证

#### 4a. 更新 INDEX.md（含 Topic Registry）

使用 `templates/index.md` 重写 `wiki/INDEX.md`：

**Topic Registry（机器优先）：**
- 为每个已编译主题生成一行 registry 记录
- 字段：slug、title、summary、tags、answers、coverage、updated、sources_count
- 数据直接从 concept frontmatter 提取，必须与 frontmatter 一致
- `kc query / kc browse / kc status` 优先依赖此表做首轮召回

**分类视图（人类友好）：**
- 按分类分组（如有 schema.md 则从中推断）
- 标记新增/更新的主题：`[更新: YYYY-MM-DD]`
- 与 Registry 数据一致，仅组织形式不同

#### 4b. Hard Gate 验证

运行以下检查。如有失败，报告问题并尝试修复后再继续：

| 门控 | 检查项 | 失败时 |
|------|--------|--------|
| Frontmatter 完整 | 每篇概念文章的 YAML frontmatter 有 `id`、`title`、`sources`、`created`、`updated` | 补充缺失字段 |
| 覆盖度标记 | 每个 `## 章节` 有 `<!-- coverage: X -->` 注释 | 添加 `<!-- coverage: low -->` |
| 来源引用有效 | 每个 `[source: path]` 指向实际存在的文件 | 移除无效引用，警告用户 |
| Schema 一致性 | 每个已编译主题在 `wiki/schema.md` 中有条目 | 将缺失条目添加到 schema |
| 非空内容 | 每个章节有实质内容（不仅仅是标题） | 标记空章节：`[待补充: 无可用源内容]` |

#### 4c. Soft Gate 检查

运行以下检查并报告警告（不阻断）：

| 门控 | 检查项 |
|------|--------|
| 孤立页面 | 未被 INDEX.md 或其他文章通过 `[[链接]]` 引用的 wiki 页面 |
| 低覆盖集群 | 所有章节都标记为 `low` 的主题 |
| 过期检测 | 源文件自上次编译后有变更（mtime），或概念超过 30 天未更新 |
| 内容矛盾 | 不同主题文章中关于同一事物的矛盾说法 |
| 断裂链接 | `[[topic-slug]]` 引用指向不存在的页面 |
| 缺失交叉引用 | 文章中提到但未链接到对应页面的主题 |
| Topic 边界重叠 | 多个 topic 的 `answers` 中包含语义几乎相同的问题 — 说明主题划分不清 |
| Registry 信息漂移 | `INDEX.md` Registry 中的元数据与 concept frontmatter 不一致 |

---

### Phase 5 — 状态与日志

1. **更新 `.compile-state.json`：**
```json
{
  "last_compiled": "YYYY-MM-DD",
  "language": "zh",
  "files": {
    "doc/api-gateway.md": {
      "mtime": 1234567890,
      "topics": ["api-gateway-design"]
    }
  }
}
```

2. **追加到 `wiki/log.md`：**
```markdown
## [YYYY-MM-DD] compile | 增量
- 编译主题: X 新建, Y 更新, Z 未变
- 处理文件: A 新增, B 变更, C 删除
- 新增主题: [列表]
- 更新主题: [列表]
- Hard Gate: 全部通过 / N 个问题已修复
- Soft Gate: N 个警告
```

---

## 预览模式

如果设置了 `--dry-run` 标志：
- 仅运行 Phase 1 和 Phase 2。
- 输出预览：哪些文件有变更、哪些主题会被编译、预估范围。
- 不写入任何文件。

---

## 单主题模式

如果设置了 `--topic <slug>` 标志：
- 跳过 Phase 1 扫描。从 `.compile-state.json` 中查找该主题的源文件。
- 仅对该主题的文件运行 Phase 2。
- 对该单一主题运行 Phase 3。
- Phase 3.5、4、5 正常运行。

---

## 交互式确认（强制规则）

编译过程中 AI **必须**在以下场景暂停并向用户确认，不可自行决定：

### 必须确认的场景

| 阶段 | 场景 | 询问方式 |
|------|------|---------|
| Phase 2 | 一个文件可能属于多个主题 | "该文件涉及 `topic-a` 和 `topic-b`，应归入哪个主题？还是拆分为两条？" |
| Phase 2 | 发现新主题，但与现有主题名称相近 | "发现新内容，它应该合并到现有的 `existing-topic` 还是创建新主题 `new-topic`？" |
| Phase 3 | 源文件之间存在矛盾信息 | "文件 A 说 X，文件 B 说 Y。以哪个为准？" |
| Phase 3 | 已有文章包含用户手动编辑的内容，且新源信息与之冲突 | "你之前手动写了 X，但新源文件说 Y。保留你的版本还是更新？" |
| Phase 3.5 | Schema 中现有分类与新发现的主题不匹配 | "新主题 `X` 不属于现有任何分类。创建新分类 `Y` 还是放入未分类？" |
| Phase 4 | Hard Gate 失败且无法自动修复 | "检查到以下问题无法自动修复：[列表]。是否继续编译？" |

### 可自动处理的场景（不需要确认）

| 场景 | AI 行为 |
|------|---------|
| 源文件不可读 | 记录警告，跳过该文件，继续处理剩余 |
| 缺失覆盖度标记 | 自动添加 `<!-- coverage: low -->` |
| 缺失 frontmatter 字段 | 自动从文件名/标题推导 |
| 新主题分类明确且不冲突 | 自动归入对应分类 |
| 孤立页面、缺失交叉引用 | 作为 Soft Gate 警告报告 |

### 确认方式

- 每次确认只问一个问题，不要堆积多个问题。
- 提供明确的选项（而非开放式问题）。
- 如果用户回答"你决定"或"都行"，选择更保守的选项（合并而非创建、保留用户版本而非覆盖）。

---

## 错误处理

- 如果源文件不可读，记录警告并继续处理剩余文件。
- 如果超过 3 个文件的主题分类不明确，暂停并逐个询问用户。
- 如果 schema.md 与发现的主题冲突，展示冲突并在更新前询问。
- 如果 Hard Gate 失败且无法自动修复，报告问题并询问是否继续。
