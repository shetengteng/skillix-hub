# 事件日志架构设计：Memory 作为 Event Store（面向 Cursor）

> **版本**: v1.0  
> **日期**: 2026-02-02  
> **状态**: 设计中  
> **适用场景**: Cursor（会话可能中断、规则并发触发、安装位置可能是全局/项目级）

## 一、目标与边界

### 1.1 目标

- **Memory 成为唯一的“会话事实”落盘点**：以追加式事件（Event）记录对话/工具调用/关键决策等事实
- **Behavior Prediction / Continuous Learning 只做“派生视图”**：从事件流构建 patterns/instincts 等派生结果（可缓存）
- **最小耦合**：Skill 间不通过 Python import 强绑定，优先采用 **CLI + JSON** 契约

### 1.2 明确不做的事

- 不要求把所有历史数据迁移（可视为新项目开发期重构）
- 不强制统一“完整 session schema”（避免方案 A 的大一统写入争用与字段权威问题）

## 二、核心概念

### 2.1 Event（事件）

事件是“事实”的最小单位，要求：
- **追加写**（append-only），不在原地修改
- 每条事件自带最小定位信息：`project_id`、`session_id`、`ts`、`type`
- Schema 可版本化：`schema_version`

### 2.2 Session（会话）

Session 不再是“唯一真相的单个 JSON 文件”，而是：
- 一个 `session_id` 对应的一组事件（按时间顺序）
- 会话“结束”是一条事件（或 finalize 动作），而非必须存在且完整的单文件

### 2.3 Derived View（派生视图）

- Behavior Prediction 的 patterns/profile、Continuous Learning 的 instincts/evolved 属于派生结果
- 派生结果**不写回 Memory 作为权威字段**（避免多写者冲突）
- 若需要缓存，只写各自 cache/data 目录，并带上 `source_watermark`（例如最后处理到的 event offset）

## 三、存储结构（建议）

放在 Memory 的数据目录下（沿用你现有 `memory-data/` 思路）：

```
memory-data/
├── events/
│   ├── 2026-02/
│   │   ├── project_<project_id>_events.jsonl
│   │   └── project_<project_id>_events.idx   # 可选：offset/时间索引
│   └── ...
├── sessions/
│   ├── 2026-02/
│   │   └── sess_20260202_001.meta.json       # 可选：会话元信息（小文件）
│   └── ...
├── index/
│   ├── projects.json                         # project_id -> path/name
│   ├── sessions_by_project.json              # 可按月分片
│   └── tags.json                             # 可按分片
├── temp/
└── config.json
```

说明：
- **events.jsonl 是唯一强依赖的数据源**（最重要）
- `sessions/*.meta.json` 仅保存“便于检索的最小元信息”，不承载完整内容
- 索引建议可分片，避免大 JSON 并发写冲突

## 四、事件模型（建议 v1）

### 4.1 基础字段

```json
{
  "schema_version": 1,
  "event_id": "evt_20260202_000001",
  "project_id": "proj_abcd1234",
  "project_path": "/abs/path/to/project",
  "session_id": "sess_20260202_001",
  "ts": "2026-02-02T10:00:00.000Z",
  "type": "session_started",
  "payload": {}
}
```

### 4.2 事件类型（最小集合）

- `session_started`
- `session_finalized`（或 `session_ended`）
- `message`（可配置是否记录原文/是否脱敏）
  - `payload.role`: `user|assistant`
  - `payload.content`: string（可选/可脱敏）
- `tool_call`
  - `payload.tool`: `Read|Write|ApplyPatch|Shell|...`
  - `payload.details`: `{file_path?, command?, ...}`
  - `payload.stage`: `design|implement|test|document|...`（可选）
- `memory_fact`（Memory 自己确认要长期保存的事实条目）
  - `payload.fact_type`: `decision|preference|config|plan|note`
  - `payload.content`: string
  - `payload.tags`: string[]
- `user_feedback`（Continuous Learning 重点）
  - `payload.feedback_type`: `correction|approval|rejection`
  - `payload.content`: string

## 五、CLI 契约（建议）

为避免跨 Skill 的 Python import 依赖，统一采用命令行 + JSON：

### 5.0 为什么要避免跨 Skill 的 Python import 依赖（Cursor 场景详解）

在 Cursor 的 skill/rule 触发模型里，“直接 `import memory...`”这类跨 Skill 代码依赖非常脆弱，主要风险是：

1. **安装位置不唯一导致 import 指向不确定**
   - Skill 可能同时存在于“全局安装路径”和“项目级安装路径”（甚至被复制过多份）。
   - Python 的模块搜索路径会受到当前工作目录、`PYTHONPATH`、执行入口位置影响，导致同一条 `import memory...` 在不同触发方式下可能加载到**不同副本**，出现“读写不是同一份数据/同一份实现”的隐蔽问题。

2. **规则并发触发带来的加载与运行时不一致**
   - 多个脚本可能同时启动；如果跨 Skill import 发生在不同进程中，代码版本、配置文件路径、相对路径解析都可能不同，排查成本很高。

3. **循环依赖风险（尤其当 Memory 也要通知 BP/CL 时）**
   - 一旦 BP/CL 需要 `import memory`，而 Memory 为了“通知/回调”也 `import bp/cl`，就会形成循环依赖。
   - 即使暂时不循环，也会把演进空间锁死：任何一方的初始化逻辑变复杂，都可能引入隐式循环。

4. **升级/回滚难度大**
   - 代码级 import 等价于“强链接”：任何一方的目录结构或模块名变化，都会立即破坏另一方。
   - 在开发期频繁迭代时，会造成大量“接口变更导致全链路同时改”的连锁反应。

因此这里推荐把跨 Skill 依赖降级为“协议依赖”：
- **CLI + JSON**：BP/CL 通过 `python3 <memory>/scripts/...` 调用 Memory 的稳定入口，入参/出参用 JSON。
- **好处**：路径更可控、接口更显式、避免循环依赖、便于做兼容（例如 `schema_version`、参数默认值）。

### 5.1 Memory：写入事件

- `memory/scripts/event_store.py --append '<json_event>'`
- `memory/scripts/event_store.py --append-batch '<json_array>'`

### 5.2 Memory：读取事件（供 BP/CL）

- `memory/scripts/event_store.py --read '{"project_id":"...","since_ts":"...","limit":1000}'`
- `memory/scripts/event_store.py --tail '{"project_id":"...","limit":200}'`

### 5.3 Memory：会话元信息（可选）

- `memory/scripts/session_meta.py --upsert '{...}'`
- `memory/scripts/session_meta.py --list '{"project_id":"...","days":90}'`

## 六、三个 Skill 的改造点

### 6.1 Memory Skill（变更点）

**新增/调整职责**
- 负责 event append、最小索引（项目、会话、tag）
- 负责并发安全（锁/原子写）
- 负责隐私策略（是否保存 message 原文、脱敏）

**建议实现顺序**
- Phase 1：先实现 `events.jsonl` 追加写 + 最小读取
- Phase 2：加可选索引（按 project/session/time）
- Phase 3：把现有 `temp/` 与 `pending_session.json` 的 finalize 逻辑映射为事件（`session_started/session_finalized`）

### 6.2 Behavior Prediction Skill（变更点）

**改为只读 Memory 的事件流**
- `--init`：从 Memory 读取最近 N 天事件，构建/更新：
  - workflow transitions（从 `tool_call.stage` 或从事件类型序列推断）
  - 用户画像（技术栈、常用阶段、偏好提示）
- `--finalize`：不再负责落盘“原始会话”，只做：
  - 计算派生结果并写入自己的 cache（或 data）目录
  - 写入一个 watermark（例如最后处理的 `event_id` 或文件 offset）

**关键注意**
- 不要回写 Memory 的“权威事实字段”（避免与 Memory 写入者冲突）
- 若需要“预测下一步”实时性，可用 `--tail` 读取近期事件增量更新

### 6.3 Continuous Learning Skill（变更点）

**输入从 observation -> event**
- `--init`：读取事件流，重点关注：
  - `user_feedback`（纠正/拒绝/认可）
  - `tool_call` + 错误输出（如果你愿意记录 `Shell` 的 exit_code/摘要）
  - 形成 instincts 的证据链（事件引用：`event_id` 列表）
- `--record`：若需要记录“用户纠正”，直接调用 Memory 追加 `user_feedback` 事件
- `--finalize`：生成/更新 instincts/evolved，写入自己的 data 目录，不写回 Memory

## 七、并发与一致性（Cursor 必备注意点）

### 7.1 追加写的原子性

- `events.jsonl` 采用“单行 JSON”追加（每条事件一行）
- 写入时必须保证：
  - 单次写入是原子追加（或通过锁保证）
  - 写失败不会产生半行 JSON（否则解析会崩）

### 7.2 锁策略（最小可行）

- 以 `project_id` 为粒度锁 `events/<month>/project_<id>_events.lock`
- 索引文件写入同样需要锁（建议按分片降低冲突）

### 7.3 Watermark（派生视图增量处理关键）

- BP/CL 在各自 cache 中记录：
  - `last_event_id` 或 `last_offset`
- 再次 init 时先读 watermark，再增量读取事件

## 八、隐私与落盘策略（强烈建议写进 config）

最小建议：
- `store_messages`: true/false
- `redaction.enabled`: true/false
- `redaction.patterns`: 默认覆盖 `token/secret/key/password` 等常见关键词/格式
- `retention_days`: 对 events 与 index 的保留策略（开发期可 -1，但要写清楚）

## 九、落地路线图（建议）

1. **先做 Event Store**：Memory 支持 append/read（最小功能闭环）
2. **BP/CL 改为只读事件流**：先跑通 init & 派生结果写入
3. **再补索引与增量**：加入 watermark 与分片索引，提升性能
4. **最后再考虑“更强统一”**：如果未来确实需要统一 session schema，可在事件流之上构建“session snapshot”（派生，不是权威）

## 十、与方案 A 的关系（简短说明）

- 事件日志方案把“统一”下沉为：**统一事实记录方式（event）**，而不是统一“最终数据模型（session JSON）”
- 在 Cursor 的不稳定/并发环境下，它更容易做到：
  - 写入简单、冲突少
  - 可回放、可增量
  - Skill 间低耦合（协议而非 import）

