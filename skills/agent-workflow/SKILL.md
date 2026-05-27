---
name: agent-workflow
description: Agent 驱动的跨 IDE / 跨 LLM 工作流引擎。声明式 YAML 描述节点串行执行 / 用户阻塞 / 条件循环 / 跨 LLM CLI 协作，状态机持久化，崩溃可恢复。Claude Code / Cursor / Codex / OpenCode 通用。
---

# Agent Workflow

> 当前版本：**v1.5.2 已实现**（Python 3.10+）
> 设计文档：`design/agent-workflow/2026-05-27-01-设计文档.md`
> 设计审核：`design/agent-workflow/2026-05-27-03-设计审核.md`
> 验收清单：`design/agent-workflow/2026-05-27-04-v1验收清单.md`

跨 IDE / 跨 LLM 的工作流引擎，以 CLI 状态机形态运行。所有 IDE 的 AI Agent 都可以通过 shell spawn 调用本工具来执行声明式 YAML workflow。

## 何时使用本 Skill

✅ **应该用**：
- ≥3 个节点的多步任务
- 需要用户阻塞确认（`wait_user`）
- 需要条件循环优化（`loop`）
- 跨 LLM CLI 协作（设计交 Claude / 实现交 Codex / 评审回当前 agent）
- 需要可重复执行的 SOP
- 需要审计 / 进度可见

❌ **不应用**：
- 单次问答 / 2-3 步纯 prompt chain
- 临时一次性任务
- 单一 LLM 内部推理

## 核心概念（5 分钟理解）

```
Workflow（YAML）   = 节点数组定义
Run（运行实例）    = 一次 start 创建一个 run_id，独立目录
Executor          = 谁执行节点：caller / claude / codex / custom
Caller            = 启动 workflow 的那个 IDE Agent
状态机             = CLI 推动 workflow 在节点之间流转
```

**最重要规则**：
1. CLI 不内嵌 LLM。所有"动脑子"的工作要么交给 caller（你自己），要么 spawn 外部 LLM CLI
2. 节点 `executor=caller` → CLI 返回 `execute_agent` 让你推理
3. 节点 `executor` 是 claude/codex 等 → CLI 自己 spawn，你只是等结果
4. 节点是 `wait_user` → CLI 返回 `wait_user` 让你问用户
5. 所有响应统一带顶层 `error` 字段；`error != null` 时按 `error.retryable` 决策

## 安装

首次使用前，在 skill 目录下执行：

```bash
cd skills/agent-workflow && pip3 install -r requirements.txt
# 或：pip3 install -e .  （推荐：可编辑安装）
```

> v1.5.2 已可用：`python3 tool.py <action> '<JSON>'` 直接调用。

## 命令规约（v1 必做 9 个）

所有命令格式：

```bash
python3 skills/agent-workflow/tool.py <action> '<JSON params>'
```

所有命令返回统一 JSON：

```json
{
  "result": { /* 业务结果 */ },
  "error": { /* 错误对象，正常时为 null */ }
}
```

### create — 创建 workflow

| action | 参数 | 用途 |
|--------|------|------|
| `list_templates` | 无 | 列出所有内置模板 |
| `from_template` | `template`（模板 alias）, `out`（输出路径） | 拷贝模板到指定路径 |
| `scaffold` | `out`, `name`, `nodes` | 生成空白骨架 |

```bash
# 列模板
python3 skills/agent-workflow/tool.py create '{"action":"list_templates"}'

# 从模板生成
python3 skills/agent-workflow/tool.py create '{
  "action": "from_template",
  "template": "cross-llm-pipeline",
  "out": "./flows/my-pipeline.yaml"
}'
```

### validate — 校验 workflow

四级校验：L1 YAML 语法 / L2 JSON Schema / L3 引用一致性（含数据流分析）/ L4 executor 环境检查。

```bash
python3 skills/agent-workflow/tool.py validate '{"workflow":"./flows/my-pipeline.yaml"}'
```

成功响应：

```json
{
  "result": {
    "valid": true,
    "errors": [],
    "warnings": [{"code":"MISSING_DESCRIPTION","message":"..."}],
    "summary": {"node_count":7,"agent_call":5,"wait_user":1,"loop":1,"executors_used":["caller","claude","codex"]}
  },
  "error": null
}
```

### start — 启动 workflow

```bash
python3 skills/agent-workflow/tool.py start '{
  "workflow": "./flows/my-pipeline.yaml",
  "vars": {"topic": "Claude Code workflow"}
}'
```

可选参数：
- `allow_missing_executors`（bool，默认 false）：缺失 executor 时是否仍启动
- `caller`（string）：声明调用方 IDE（用于审计，如 `cursor` / `claude-code`）

### advance — 推进（caller 推理完调用）

caller 节点执行后调用，传 result：

```bash
# 成功推进
python3 skills/agent-workflow/tool.py advance '{
  "run_id": "wf-2026-05-27-abc123",
  "result": {"output": "调研结果：1. xxx 2. yyy ..."}
}'

# 节点失败上报
python3 skills/agent-workflow/tool.py advance '{
  "run_id": "wf-2026-05-27-abc123",
  "result": {"error": {"message":"分析失败","details":"..."}}
}'
```

### resume — 恢复（wait_user 输入完调用）

```bash
python3 skills/agent-workflow/tool.py resume '{
  "run_id": "wf-2026-05-27-abc123",
  "user_input": {"approved": false, "feedback": "需要补充错误处理"}
}'
```

### status — 查询单 run

```bash
python3 skills/agent-workflow/tool.py status '{"run_id":"wf-2026-05-27-abc123"}'
```

返回当前 run 状态、变量、最近 10 条 history。

### list — 列出 run（默认仅当前项目；含表格输出）

```bash
# 仅当前项目（默认 JSON）
python3 skills/agent-workflow/tool.py list '{}'

# 状态过滤（支持字符串或数组）
python3 skills/agent-workflow/tool.py list '{"status":"waiting_user"}'

# 跨项目
python3 skills/agent-workflow/tool.py list '{"scope":"all"}'

# v1.5.2 新增：人类可读表格（caller 透传给用户看 / 用户自己跑）
python3 skills/agent-workflow/tool.py list '{"format":"table"}'
```

**format=table 输出示例**（在 `result.table` 字段）：

```
+----------------+--------------------+----------------+----------+----------+---------+
| run_id         | workflow           | status         | node     | started  | elapsed |
+----------------+--------------------+----------------+----------+----------+---------+
| wf-..a3f9c1    | cross-llm-pipeline | waiting_user   | review   | 13:30:00 |  5m 12s |
| wf-..b8d2e3    | code-review        | completed      | -        | 13:25:00 |  8m 03s |
| wf-..c1f5a7    | iterative-refine   | failed         | refine   | 13:20:00 |  2m 45s |
+----------------+--------------------+----------------+----------+----------+---------+
3 runs total | running: 0 | waiting_user: 1 | completed: 1 | failed: 1 | aborted: 0
```

**caller 使用建议**：
- **想自己处理数据**：用 `format: "json"`（默认），读 `result.items[*]`
- **想直接展示给用户**：用 `format: "table"`，把 `result.table` 字符串透传到用户消息

### abort — 主动中止

```bash
python3 skills/agent-workflow/tool.py abort '{"run_id":"wf-2026-05-27-abc123"}'
```

### executors — 列出可用 executor

```bash
python3 skills/agent-workflow/tool.py executors '{}'
```

返回每个 executor 是否在 PATH、配置参数等。

## Agent 调用约定（强制 — 必须遵守）

### 0. caller 接力（v1.5.2，启动时做）

```python
# caller 启动后第一件事：检查未完成 workflow
runs = cli('list', {scope: 'project', status: ['waiting_user', 'awaiting_agent']})
if len(runs.result) > 0:
    show_to_user(f"你有 {len(runs.result)} 个未完成 workflow，是否继续？")
    if user_confirms:
        for run in runs.result:
            # 用 status 拿到 last_payload 重建提问
            s = cli('status', {run_id: run.run_id})
            if s.result.status == 'waiting_user':
                show_to_user(s.result.last_payload.message)
                user_input = collect_input(schema=s.result.last_payload.schema)
                response = cli('resume', {run_id: run.run_id, user_input: user_input})
                # 进入主循环
```

### 1. 主循环（v1.5.2 含 continue 分支）

```python
response = cli('start', {workflow: '...', vars: {...}})
# 立即持久化 run_id（写文件 / IDE memory）
persist(response.result.run_id)

while True:
    # ① 错误检查
    if response.error is not None:
        if response.error.retryable:
            show_to_user(response.error.message + response.error.suggestion)
            new_input = ask_user_again()
            response = cli('resume', {run_id, user_input: new_input})
            continue
        else:
            show_to_user(f"Workflow 失败：{response.error.message}\n建议：{response.error.suggestion}")
            break

    # ② 按 action 分支
    result = response.result
    if result.action == 'execute_agent':
        if result.node.description:
            show_to_user(f"正在执行：{result.node.description}")
        agent_output = think_and_respond(result.payload.prompt)
        response = cli('advance', {run_id: result.run_id, result: {output: agent_output}})

    elif result.action == 'continue':               # ⭐ v1.5.2 长链保活
        # 不展示给用户，立即再调 advance（不带 result）
        response = cli('advance', {run_id: result.run_id})
        continue

    elif result.action == 'wait_user':
        show_to_user(result.payload.message)
        user_input = collect_input(schema=result.payload.schema)
        response = cli('resume', {run_id: result.run_id, user_input: user_input})

    elif result.action == 'done':
        show_to_user(f"Workflow 完成：{result.vars.final_report}")
        break
```

**严格约束**：
- 永远不要绕过 CLI 直接修改 `state.json` / `events.ndjson` / `audit.log`
- 不要跳过 CLI 返回的节点（必须按其指示 advance / resume）
- 同一 run_id 不要并发 advance（CLI 内部有锁，会返回 `RUN_BUSY`）
- 不会收到 `executor != caller` 的 `execute_agent`（外部 LLM 由 CLI 内部自动 chain）
- 收到 `action: "continue"` 时**不要**推理 / 不要问用户 → 立刻重发 advance
- `start` 返回的 `run_id` 必须立刻持久化到 caller 侧，避免会话丢失后无法接力

## 错误码表（v1.5）

按命名空间分组。所有错误都返回顶层 `error` 对象，含 `code` / `message` / `retryable` / `suggestion`。

| 错误码 | 含义 | retryable | caller 建议处理 |
|--------|------|:---:|------|
| `WORKFLOW_INVALID` | start 时 L1~L4 校验失败 | ❌ | 展示 suggestion；不重启 |
| `WORKFLOW_SNAPSHOT_CORRUPTED` | 快照文件损坏 | ❌ | 提示用户从源 YAML 重新 start |
| `RUN_NOT_FOUND` | run_id 不存在 | ❌ | 检查 run_id 是否正确 |
| `RUN_ALREADY_TERMINAL` | run 已 completed/failed/aborted | ❌ | 不重复操作 |
| `RUN_BUSY` | 并发 advance/resume 冲突 | ✅ | 等 1 秒后重试 |
| `NODE_TIMEOUT` | 外部 executor 超时 | ❌ | 提示用户调大 timeout |
| `NODE_EMPTY_OUTPUT` | stdout 空 | ❌ | 提示检查 executor 配置 |
| `NODE_OUTPUT_REQUIRED` | output 字段缺失 | ❌ | 修 YAML 后重新 validate |
| `EXECUTOR_NOT_FOUND` | start 时 PATH 找不到 executor | ❌ | 提示用户安装 CLI 或加 `allow_missing_executors: true` |
| `EXECUTOR_NONZERO_EXIT` | 子进程非 0 退出 | ❌ | 展示 stderr_tail，建议检查 CLI |
| `EXECUTOR_STALLED` | 子进程超 stall_timeout（默认 300s）无 stdout | ❌ | 展示 stderr_tail，建议增大 stall_timeout 或换 executor |
| `LOOP_EXCEEDED` | iteration 超 max_iterations | ❌ | 提示用户增大 max 或调整 condition |
| `SCHEMA_VIOLATION` | wait_user 输入不符 schema | ✅ | **重新索取输入** |
| `VAR_NOT_IN_SCOPE` | strict_vars 下变量未定义 | ❌ | 修 YAML，把节点提前或检查 alias |
| `CALLER_ERROR` | advance 时 caller 主动报错 | ❌ | 不再继续 |

## 节点类型速查（v1，含 v1.5.1 sleep）

### `agent_call` — Agent 推理节点

```yaml
- alias: research              # 可选；CLI 自动生成 UUID 主键
  type: agent_call
  description: 调研主题         # 可选；用于 status/error 显示
  executor: caller             # caller / claude / codex / custom
  prompt: "调研：{{topic}}"     # 模板 {{var}} 必须在当前作用域内
  output: research_result       # v1.5 必填；写回 vars
  timeout: 600                 # 可选（仅外部 executor 生效）
  context_files:               # 可选；spawn 时注入文件内容
    - "./README.md"
```

### `wait_user` — 用户阻塞节点

```yaml
- alias: review
  type: wait_user
  description: 用户审阅设计
  message: 请审阅设计文档，是否通过？
  schema:                      # JSON Schema 子集
    type: object
    required: [approved]
    properties:
      approved: { type: boolean }
      feedback: { type: string, default: "" }
```

### `loop` — 条件循环节点（v1.5：body 允许 wait_user）

```yaml
- alias: refine_loop
  type: loop
  condition: "{{review.approved}} == false"
  max_iterations: 3            # 上限 100
  body:
    - alias: review            # ✅ v1.5 允许嵌套 wait_user
      type: wait_user
      message: 是否通过？
      schema: {...}
    - alias: refine
      type: agent_call
      executor: claude
      prompt: "...{{review.feedback}}..."
      output: design_doc
```

### `sleep` — 原子等待节点（v1.5.1 新增）

```yaml
- alias: cool_down
  type: sleep
  description: 防 LLM rate limit
  seconds: 5             # 必填；0-300（即 0~5 分钟）；支持 {{var}}
```

**典型用法**：

```yaml
# 1) 轮询：loop.body 末尾插 sleep
- alias: poll_loop
  type: loop
  condition: "{{job_status}} != 'done'"
  max_iterations: 60
  body:
    - alias: check
      type: agent_call
      executor: caller
      prompt: "查询任务 {{job_id}} 状态"
      output: job_status
    - alias: gap
      type: sleep
      seconds: 5

# 2) Rate limit：两个 LLM 调用之间插 sleep
- alias: cool_down
  type: sleep
  seconds: 3
```

**注意**：
- v1 同步实现：调 advance/resume 的那次 CLI 调用会阻塞 N 秒后才返回
- sleep 期间**不能 abort**（v1 限制；v1.5 引入异步版本）
- 不写 vars，无 output

## Quick Start — 30 秒上手

```bash
# 0) 检查是否有未完成 workflow（v1.5.2 推荐 caller 启动时做）
python3 skills/agent-workflow/tool.py list '{"scope":"project","status":["waiting_user","awaiting_agent"]}'

# 1) 看可用模板
python3 skills/agent-workflow/tool.py create '{"action":"list"}'

# 2) 复制模板到项目
python3 skills/agent-workflow/tool.py create '{
  "action": "from_template",
  "template": "research-and-implement",
  "out": "./flows/my-first.yaml"
}'

# 3) 校验（推荐每次改 YAML 后做）
python3 skills/agent-workflow/tool.py validate '{"workflow":"./flows/my-first.yaml"}'

# 4) 启动
python3 skills/agent-workflow/tool.py start '{
  "workflow": "./flows/my-first.yaml",
  "vars": {"topic": "Claude Code workflow"}
}'
# → 拿到 run_id（**立即持久化** 到 caller 侧避免会话丢失）

# 5) 后续 Agent 按 Agent 调用约定 循环 advance/resume
#    遇到 action:"continue" 自动重发；遇到 wait_user 问用户

# 6) 看进度
python3 skills/agent-workflow/tool.py status '{"run_id":"wf-..."}'
# 返回含 last_payload（如在 waiting_user 状态，可用它重建提问上下文）

# 7) 跨进程实时看
tail -f ~/.agent-workflow/runs/wf-.../events.ndjson
```

## 恢复未完成 workflow（caller 关闭后）

```bash
# 1) 列出本项目所有未完成 run
python3 skills/agent-workflow/tool.py list '{"scope":"project","status":["waiting_user","awaiting_agent"]}'

# 2) 看 last_payload 重建上下文
python3 skills/agent-workflow/tool.py status '{"run_id":"wf-..."}'
# 输出含：
#   .result.status = "waiting_user"
#   .result.last_payload.message = "请审阅设计文档..."
#   .result.last_payload.schema = {...}

# 3) caller 把 message 重新展示给用户 → 问输入 → resume
python3 skills/agent-workflow/tool.py resume '{"run_id":"wf-...","user_input":{...}}'
```

## 输出格式（统一协议）

成功响应：

```json
{
  "result": {
    "run_id": "wf-2026-05-27-abc123",
    "status": "awaiting_agent | executing_external | waiting_user | completed | failed | aborted",
    "action": "execute_agent | wait_user | done",
    "node": {
      "internal_id": "7f3a9c2e",
      "alias": "research",
      "description": "...",
      "type": "agent_call",
      "executor": "caller"
    },
    "payload": {
      "prompt": "渲染后的 prompt（仅 caller 节点）",
      "node_description": "...",
      "message": "wait_user 时的提示",
      "schema": {}
    },
    "vars": {},
    "history_tail": []
  },
  "error": null
}
```

错误响应：

```json
{
  "result": null,
  "error": {
    "code": "NODE_TIMEOUT",
    "message": "...",
    "node": {"internal_id":"...","alias":"design","description":"..."},
    "executor": "claude",
    "details": {"exit_code":124,"stderr_tail":"...","cmd_template":"claude (stdin)"},
    "retryable": false,
    "suggestion": "Increase timeout or split prompt into smaller chunks"
  }
}
```

## 自然语言交互指南（caller agent）

| 用户说 | Agent 做 |
|--------|---------|
| 启动 / 运行 / 跑 workflow X | `validate` → 校验通过 → `start` |
| 这个 workflow 行不行 / 校验 / 检查 / lint | `validate` |
| 我想做一个 workflow / 创建一个 workflow | `create '{"action":"list"}'` → 推荐合适模板 → `from_template` |
| workflow 怎么样了 / 跑到哪了 / 进度 | `status` 或 `tail -f events.ndjson` |
| 列出 / 显示我的 workflow | `list`（默认仅当前项目） |
| 看一下我的 workflow / 列个表 | `list '{"format":"table"}'` 把 `result.table` 透传给用户 |
| 停 / 中止 / cancel | `abort` |
| 收到 `execute_agent` action | 自己推理 → `advance` 传 result |
| 收到 `wait_user` action | 展示 message → 问用户 → `resume` |
| 收到 `done` action | 展示 `result.vars` 中关键字段 |
| 收到 `error.retryable=true` | 引导用户调整输入 → 重新 resume |
| 收到 `error.retryable=false` | 展示 `error.message` + `error.suggestion`，本轮结束 |

## 与其他 Skill 协作

| Skill | 协作方式 |
|-------|---------|
| `agent-interact` | 安装后 wait_user 自动用弹窗 UI（v1.5）；未安装则用 terminal |
| `skill-builder` | 本 skill 由 skill-builder 脚手架生成；遵循其 10 阶段规范 |

## 安全注意

- v1.5 默认 stdin 传 prompt，避免敏感信息出现在进程列表
- `state.json` 不记录渲染后 prompt，仅记 cmd 模板
- 用 `vars.<name>.secret: true` 标记敏感变量，自动从日志脱敏
- `$ENV:VAR_NAME` 启动时自动展开环境变量

## 当前限制（v1）

- 仅支持串行执行（按 nodes 数组顺序）；并行 / DAG 在 v2
- 仅支持 macOS / Linux；Windows 待 v2
- 节点失败无 retry（v1.5 引入节点级 retry）
- wait_user schema 仅 JSON Schema 子集（顶层 object + 字段 string/boolean/number）
- 不支持子工作流（`sub_workflow` 在 v2）

## 故障排查

| 现象 | 可能原因 | 排查 |
|------|---------|------|
| `EXECUTOR_NOT_FOUND` | 外部 CLI 未装 | `which claude` / `which codex` |
| `NODE_TIMEOUT` | 外部 CLI 卡住或 prompt 过大 | 调大 timeout 或拆分 prompt |
| `VAR_NOT_IN_SCOPE` | 引用了未来节点输出 | 检查 nodes 顺序、output 字段拼写 |
| `RUN_BUSY` | 并发 advance | 等 1 秒重试 |
| 看不到外部 LLM 输出过程 | 是预期行为 | `tail -f events.ndjson` 看进度 |
| `state.json` 文件锁残留 | 上次崩溃 | 删除 `~/.agent-workflow/runs/<run_id>/state.json.lock` |
| advance 调用很久没返回 | workflow 命中了 sleep 节点或外部 executor | 正常 — sleep N 秒后会返回；外部 executor 超 stall_timeout 自动 SIGTERM |
| advance 调用 ≥25 秒返回 `action:"continue"` | 长链 chain_timeout 触发保活 | 正常 — 立即重发 advance（不传 result） |
| sleep 节点想 abort 但无效 | v1 同步实现限制 | 等 sleep 完后再 abort；v1.5 异步版可中途 abort |
| caller 关掉后想继续 workflow | run 状态已持久化 | `list` 找 run_id → `status` 看 last_payload → `resume` |
| 跨 IDE 接力同一 workflow | v1 不做 caller 身份锁 | 任何 caller 都可 resume；audit.log 记录切换 |
| `EXECUTOR_STALLED` | 子进程 300s 无 stdout | 增大 `stall_timeout_ms` 或检查 LLM CLI 是否真的卡死 |
