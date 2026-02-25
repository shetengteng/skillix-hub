# Memory 架构优化：MEMORY.md 写入策略调整

## 背景

当前 Memory Skill 的 MEMORY.md 有两条写入路径：

1. **规则提炼**（`distill_to_memory.py`）：sessionEnd 时自动执行，基于 confidence/age/关键词 规则筛选 daily/*.jsonl 中的事实，追加到 MEMORY.md
2. **Agent 精炼**（`distill_refined.py`）：由 LLM 在上下文中判断，全量重写 MEMORY.md

问题：规则提炼是**无 LLM 参与的自动汇总**，可能将不值得长期保存的事实写入 MEMORY.md。

## 现状分析

### MEMORY.md 写入路径

| 路径 | 触发时机 | 写入方式 | 是否有 LLM 参与 |
|------|----------|----------|-----------------|
| `distill_to_memory.py` | sessionEnd Hook | 追加（只加不改） | 否，纯规则 |
| `distill_refined.py` | [Session Save] prompt 引导 Agent 调用 | 全量重写 | 是，LLM 精炼 |
| `init/helpers.py` | 首次安装 | 创建默认结构 | 否 |
| `config/__init__.py` | 首次使用新项目 | 创建默认结构 | 否 |

### sessions.jsonl 加载确认

`load_memory.py` 第 67-76 行：每次会话启动时通过 `read_last_entry(sessions_path)` 加载最后一条会话摘要，展示为"上次会话"章节。**是的，sessions.jsonl 每次会话前都会加载（最后一条）**。

### NOTES.md 保留

NOTES.md 保持现状，不做修改。作为用户手动维护的笔记空间。

### distill_to_memory.py 规则提炼详情

```
触发链：sessionEnd → sync_and_cleanup.py → distill_facts() → distill()
筛选条件：
  - confidence >= 0.85
  - age >= 1 天
  - 非 S 类型（排除摘要）
  - 去重（精确匹配 + 子串包含）
分类：按 memory_type + 关键词映射到章节
写入：追加到对应 ## 章节末尾
上限：每次最多 15 条
```

**问题**：
- 无 LLM 参与，无法判断事实是否"值得长期保存"
- 关键词分类过于粗糙（如"使用"这个词出现频率极高）
- 只追加不精简，MEMORY.md 会持续膨胀
- 与 Agent 精炼（distill_refined）功能重叠

---

## 开源项目参考

### OpenClaw

OpenClaw 使用纯 Markdown 文件存储记忆，不依赖向量数据库。

**记忆层级**：

| 层级 | 存储 | 说明 |
|------|------|------|
| 短期 | 对话上下文 | LLM 自动维护 |
| 中期 | `memory/YYYY-MM-DD.md` | 每日日志，启动时加载今天和昨天 |
| 长期 | `MEMORY.md` | 核心持久记忆，建议不超过 2000 词 |

**MEMORY.md 写入规则**（LLM 判断）：

- 只写入**持久事实、决策和偏好** — 下个月还有用的信息才写入
- 用户说"记住这个"时写入
- 日常笔记和运行上下文写入每日日志，不写入 MEMORY.md
- **判断标准**："如果信息下个月还重要，写 MEMORY.md；如果只是今天重要，写每日日志"

**自动压缩触发**：

- 会话接近上下文压缩时，系统触发一个静默的 agentic turn
- 提示 LLM："Session nearing compaction. Store durable memories now"
- LLM 自行判断哪些值得保存，写入 MEMORY.md

**2026 年新特性**：
- FSRS-6 间隔重复：记忆像人类一样自然衰减，不常访问的记忆逐渐淡化
- 5 层记忆层级（T0 工作记忆 → T4 基础知识），自动归档和召回
- 混合搜索：BM25（0.3 权重）+ 向量相似度（0.7 权重）+ MMR 去重排序

**启发**：
- MEMORY.md 写入完全由 LLM 判断，无规则自动追加 — 与我们的优化方向一致
- 2000 词上限是个好实践，防止 MEMORY.md 无限膨胀
- "下个月还重要吗？"是简洁有效的判断标准

### Linggen

Linggen 是 Cursor/Zed/Claude 的本地优先记忆层（Rust + TypeScript，MIT 协议）。

**核心概念 — Design Anchors**：

- 记忆存储为 `.linggen/memory` 目录下的 Markdown 文件
- 重点存储**架构决策**（ADR）和**团队知识**
- 通过 LanceDB 本地向量索引实现语义搜索召回
- AI 处理代码时通过语义搜索自动召回相关记忆

**启发**：
- 记忆按主题拆分为多个文件，而非全部塞入一个 MEMORY.md
- 语义搜索召回比全量加载更高效（大型项目场景）

### Cursor Memory Bank

Cursor Memory Bank 使用文档驱动的方式提供持久记忆（710 stars）。

**核心文件**：

| 文件 | 作用 |
|------|------|
| `projectbrief.md` | 项目核心需求和目标 |
| `productContext.md` | 项目目的、解决的问题 |
| `systemPatterns.md` | 系统架构、技术决策、设计模式 |
| `techContext.md` | 技术栈、开发环境 |
| `activeContext.md` | 当前工作焦点、近期变更 |
| `progress.md` | 已完成功能、待办、当前状态 |

**启发**：
- 将记忆按**职责**拆分为多个文件，而非按时间
- `alwaysApply: true` 确保每次任务开始都加载
- 结构化模板降低 LLM 写入时的随意性

---

## 优化方案

### 核心变更：禁用 distill_to_memory 自动追加

**MEMORY.md 的写入完全依赖 LLM 在上下文中判断**，不再由规则自动汇总。

借鉴 OpenClaw 的做法：LLM 在会话结束时自行判断哪些信息值得长期保存，写入 MEMORY.md。判断标准："如果信息下个月还重要，写 MEMORY.md；如果只是今天重要，写 daily 日志"。

#### 具体修改

| 文件 | 修改内容 |
|------|----------|
| `sync_and_cleanup.py` 第 309 行 | 注释或删除 `distill_facts(project_path, ...)` 调用 |
| `distill_to_memory.py` | 保留代码不删除（`--dry-run` 仍可用于调试），但不再被自动调用 |

#### 修改后的 sessionEnd 流程

```
sessionEnd 触发
 ↓
sync_index()          ← 保留：JSONL → SQLite 同步
truncate_sessions()   ← 保留：sessions.jsonl 截断
auto_generate_summary() ← 保留：兜底摘要生成
check_summary_saved() ← 保留：摘要保存检测
# distill_facts()     ← 移除：不再自动提炼到 MEMORY.md
log_session_metrics() ← 保留：会话指标记录
log_session_end()     ← 保留：会话结束记录
clean_old_logs()      ← 保留：日志清理
clean_old_session_states() ← 保留：状态清理
```

### MEMORY.md 写入策略（优化后）

| 场景 | 写入方式 | 说明 |
|------|----------|------|
| 用户明确表达偏好 | LLM 通过 distill_refined 写入 | [Session Save] prompt 引导 |
| 项目级上下文 | LLM 通过 distill_refined 写入 | [Session Save] prompt 引导 |
| 持续性事实 | LLM 通过 distill_refined 写入 | [Session Save] prompt 引导 |
| 用户说"记住这个" | LLM 直接编辑 MEMORY.md | SKILL.md 中已有指导 |
| 闲聊/一次性问题 | 不写入 | LLM 自行判断 |

### 可选的后续优化（参考开源项目）

| 优化项 | 参考来源 | 说明 | 优先级 |
|--------|----------|------|--------|
| MEMORY.md 字数上限 | OpenClaw | 建议不超过 2000 词，超出时 LLM 精炼压缩 | 中 |
| 记忆衰减机制 | OpenClaw FSRS-6 | 不常访问的记忆逐渐降低权重 | 低 |
| 按主题拆分记忆文件 | Linggen | 大型项目可按主题拆分为多个 .md 文件 | 低 |
| 混合搜索优化 | OpenClaw | BM25 + 向量 + MMR 去重排序 | 低 |

### 不变的部分

- **NOTES.md**：保留，用户手动维护
- **sessions.jsonl**：保留，每次会话前加载最后一条（替代 HISTORY.md 的功能）
- **daily/*.jsonl**：保留，原始事实数据不受影响
- **distill_refined.py**：保留，作为唯一的 MEMORY.md 写入路径（除 init 创建外）

## 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| LLM 遗漏重要事实 | 中 | 事实仍保留在 daily/*.jsonl，可手动或通过 search_memory 找回 |
| MEMORY.md 更新频率降低 | 低 | 每次 [Session Save] 都会触发精炼，频率足够 |
| distill_to_memory 代码废弃 | 低 | 保留代码和 --dry-run，未来可作为辅助工具 |

## 执行步骤

1. 修改 `sync_and_cleanup.py`：移除 `distill_facts()` 调用
2. 验证 sessionEnd Hook 正常执行
3. 确认 [Session Save] 的 distill_refined 路径正常工作
