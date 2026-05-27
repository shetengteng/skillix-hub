---
name: agent-workflow
description: |
  跨 IDE / 跨 LLM 的声明式工作流引擎，以 CLI 状态机形态运行。把多步任务、用户阻塞、条件循环、跨 LLM CLI 协作（claude / codex / caller）描述为一份 YAML，CLI 负责落盘、推进、崩溃恢复，所有推理交给 caller（你）或外部 LLM。当用户提到"workflow"、"流程"、"多步任务"、"跨 LLM 协作"、"用户确认环节"、"自动化 SOP"、"批量处理"、"恢复昨天的任务"，或意图需要 ≥3 个节点、需要审计、需要可重复 SOP 时使用。Python 3.10+，零运行时网络依赖。
---

# Agent Workflow

跨 IDE / 跨 LLM 工作流引擎。你（caller）通过 shell spawn 调用 `tool.py`，CLI 推动 workflow 在节点间流转。**CLI 不内嵌 LLM** — 所有推理动作要么由你完成，要么 CLI spawn 外部 LLM CLI。

完整用户文档（含安装、QuickStart、配方、FAQ）：见同目录 `README.md`。

---

## 何时使用 / 何时不用

**✅ 使用条件**（任一即可）

- 多步任务，**≥3 个节点**
- 需要**用户阻塞确认**（`wait_user`）
- 需要**条件循环**（直到 review 通过为止）
- 需要**跨 LLM 协作**（如：Claude 设计 → Codex 实现 → 当前 agent review）
- 用户说"昨天那个流程接着跑" / "把这套流程做成可重复 SOP"
- 需要审计（每一步落盘可追溯）

**❌ 不要使用**

- 单次问答 / 2-3 步纯 prompt chain（直接推理更快）
- 临时一次性任务（写个脚本就完事）
- 单一 LLM 内部推理（用 CoT 即可，不要套 workflow）

---

## 主循环骨架（最重要 — 必须按此实现）

调用 CLI 后，你会收到统一响应结构：

```json
{ "result": { "action": "...", "run_id": "wf-...", ... }, "error": null }
```

按 `result.action` 分 4 种情况处理（**不要遗漏 `continue`**）：

```python
response = cli("start", {"workflow": "./flow.yaml", "vars": {...}, "caller": "my-agent"})
persist(response["result"]["run_id"])   # 立刻持久化 run_id，避免会话丢失

while True:
    # ① 错误优先检查
    if response.get("error") is not None:
        err = response["error"]
        if err["retryable"]:
            show_to_user(err["message"] + "\n" + err.get("suggestion", ""))
            new_input = ask_user_again()
            response = cli("resume", {"run_id": run_id, "user_input": new_input})
            continue
        show_to_user(f"Workflow 失败：{err['message']}\n建议：{err.get('suggestion')}")
        break

    r = response["result"]
    run_id = r["run_id"]

    if r["action"] == "execute_agent":
        # CLI 让你来推理；payload.prompt 是渲染后的提示
        # ⚠ 不要把 prompt 原样展示给用户；直接推理后调 advance
        if r["node"].get("description"):
            show_to_user(f"正在执行：{r['node']['description']}")
        output = you_reason(r["payload"]["prompt"])
        response = cli("advance", {"run_id": run_id, "result": {"output": output}})

    elif r["action"] == "continue":
        # ⭐ 长链保活：CLI 内部 chain 超时主动返回
        # ⚠ 绝对不要展示给用户、绝对不要推理 — 立即重发 advance（不带 result）
        response = cli("advance", {"run_id": run_id})

    elif r["action"] == "wait_user":
        # 展示 payload.message 给用户，按 payload.schema 收集输入
        show_to_user(r["payload"]["message"])
        user_input = collect_input(schema=r["payload"].get("schema"))
        response = cli("resume", {"run_id": run_id, "user_input": user_input})

    elif r["action"] == "done":
        show_to_user(f"Workflow 完成：{r.get('vars', {})}")
        break
```

`cli(action, params)` = `subprocess.run(["python3","skills/agent-workflow/tool.py",action,json.dumps(params)]) → json.loads(stdout)`

---

## 强制约束（DON'T）

1. **永远不要绕过 CLI 直接改 `state.json` / `events.ndjson` / `audit.log`** — 任何编辑都会破坏审计与恢复
2. **收到 `action: "continue"` 时**：不展示给用户、不推理、不问用户、不 sleep；立即重发 `advance(run_id)`，不带 result
3. **`start` 返回的 `run_id` 必须立刻持久化** 到 caller 侧（写文件或会话内存），否则会话丢失后无法接力
4. **同一个 `run_id` 不要并发 advance/resume** — CLI 内部有 filelock，重入会返回 `RUN_BUSY`
5. **永远不会收到 `executor != caller` 的 `execute_agent`** — 外部 LLM 节点由 CLI 内部自动 spawn 与 chain，你只会等结果
6. **不要在 `prompt` 字段硬编码 API Key / 密码** — 用 `vars.api_key: "$ENV:OPENAI_API_KEY"` + `vars._secrets: ["api_key"]`
7. **不要在 advance 时携带渲染后 prompt 当上下文** — CLI 已自管 vars，传 `result.output` 即可

---

## 4 种 action 处理详解

| `result.action` | 含义 | 你的下一步 |
|---|---|---|
| `execute_agent` | CLI 要 caller 推理 | 读 `payload.prompt` → 推理 → `advance({run_id, result: {output}})` |
| `wait_user` | CLI 要 caller 问用户 | 展示 `payload.message` → 按 `payload.schema` 收集 → `resume({run_id, user_input})` |
| `continue` | CLI 长链保活返回 | **立即** `advance({run_id})`，**不**带 result |
| `done` | workflow 完成 | 展示 `result.vars` 中的最终结果 |

`payload` 还会带：
- `node.alias` / `node.type` / `node.description`（给用户的提示文案可用）
- `node_description`（如设了，可展示"正在执行：xxx"）

`vars` 在 `done` 时包含 workflow 累计写入的所有命名变量（每个 `agent_call.output` 都会写一条）。

---

## CLI 命令速查（10 个 action）

| Action | 何时用 | 最小调用示例 |
|---|---|---|
| `create` | 用户要新 workflow / 看模板 | `create '{"action":"list_templates"}'` 然后 `create '{"action":"from_template","template":"...","out":"./flows/x.yaml"}'` |
| `validate` | YAML 改后启动前必跑 | `validate '{"workflow":"./flows/x.yaml"}'` |
| `start` | 启动一个 run | `start '{"workflow":"./flows/x.yaml","vars":{"topic":"..."},"caller":"my-agent"}'` |
| `advance` | 主循环里推理完上报 / 收到 continue 后重发 | `advance '{"run_id":"wf-...","result":{"output":"..."}}'` 或 `advance '{"run_id":"wf-..."}'` |
| `resume` | wait_user 收到用户输入 | `resume '{"run_id":"wf-...","user_input":{"approved":true}}'` |
| `status` | 用户问"workflow 跑到哪了" | `status '{"run_id":"wf-...","include_events":true,"event_limit":50}'` |
| `list` | 用户问"我有哪些 workflow" / 接力查未完成 | `list '{"status":["waiting_user","awaiting_agent"]}'` 或 `list '{"format":"table"}'` |
| `abort` | 用户说"停 / 取消 / 算了" | `abort '{"run_id":"wf-..."}'` |
| `executors` | 用户问"有哪些可用 executor" | `executors '{}'` |
| `view` | 用户说"看一下 workflow"/"可视化" | `view '{}'`（总览） / `view '{"run_id":"wf-..."}'`（单 run），默认自动开浏览器 |

完整参数表与返回结构见 README §10。

---

## 节点类型速查

### `agent_call` — 推理节点

```yaml
- alias: research                # 必填，全 workflow 唯一
  type: agent_call
  description: 调研主题            # 可选；用于 status/UI 显示
  executor: caller                # caller / claude / codex / 自定义 spawn executor
  prompt: "调研主题：{{topic}}"    # 模板，{{var}} 必须当前作用域可见
  output: research_result          # 必填；推理结果写入 vars.<output>
  timeout_ms: 60000                # 可选（仅外部 executor 生效）
  context_files: ["./README.md"]   # 可选；spawn 时把文件内容拼入 prompt
```

### `wait_user` — 用户阻塞节点

```yaml
- alias: review
  type: wait_user
  message: "请审阅设计文档"          # 可选模板字符串
  schema:                          # 可选 JSON Schema（顶层 object）
    type: object
    required: [approved]
    properties:
      approved: { type: boolean }
      feedback: { type: string, default: "" }
```

- 不写 `output`：用户输入按 `alias` 自动写入 `vars.<alias>`（如 `vars.review.approved`）
- 不允许 `context_files`、`executor`、`prompt`

### `loop` — 条件循环节点

```yaml
- alias: refine_loop
  type: loop
  condition: "{{review.approved}} == false"  # 必填，每轮结束求值
  max_iterations: 5                # 必填，1–100
  step_sleep_ms: 1000              # 可选，每轮间隔毫秒
  body:                            # 必填，≥1 个子节点
    - alias: refine
      type: agent_call
      executor: caller
      prompt: "基于反馈优化：{{review.feedback}}"
      output: design
    - alias: review
      type: wait_user
      message: "再审一次"
      schema: { ... }
```

- **第一次迭代用 do-while 语义**：condition 中未定义变量被宽松判定为 truthy，保证 body 跑一次
- 不允许 loop 顶层 `output`（输出在 body 内通过 `output:` 写入）

### `sleep` — 原子睡眠节点

```yaml
- alias: cool_down
  type: sleep
  seconds: 5                       # 必填，0–300，支持 {{var}} 模板
```

- v1 同步实现：调 advance 的那次 CLI 调用会阻塞 N 秒后才返回
- 不写 vars / 不允许 output
- 典型用法：loop.body 末尾插 `sleep` 做轮询，或两次 LLM 调用之间限流

---

## 错误处理：retryable 决策表

所有错误是顶层 `error`，结构统一：

```json
{
  "code": "SCHEMA_VIOLATION",
  "message": "user_input.approved is required",
  "retryable": true,
  "suggestion": "请用户提供 approved 字段（boolean）",
  "location": { "alias": "review", "field": "approved" }
}
```

| 错误码 | retryable | caller 处理 |
|---|:---:|---|
| `SCHEMA_VIOLATION` | ✅ | 展示 message+suggestion，让用户改输入后再 resume |
| `RUN_BUSY` | ✅ | 等 1 秒，重发同一动作 |
| `WORKFLOW_INVALID` | ❌ | 终态。展示 suggestion，引导用户修 YAML 后重新 start |
| `WORKFLOW_SNAPSHOT_CORRUPTED` | ❌ | 终态。从源 YAML 重新 start |
| `RUN_NOT_FOUND` | ❌ | 终态。检查 run_id 是否正确 |
| `RUN_ALREADY_TERMINAL` | ❌ | 终态。run 已结束，不要重复操作 |
| `EXECUTOR_NOT_FOUND` | ❌ | 终态。提示用户安装对应 CLI（或 start 时加 `allow_missing_executors: true` 跳过 L4） |
| `EXECUTOR_NONZERO_EXIT` | ❌ | 终态。展示 `stderr_tail`，建议检查外部 CLI |
| `EXECUTOR_STALLED` | ❌ | 终态。子进程 300s+ 无 stdout 被强杀；增大 `stall_timeout_ms` 或换 executor |
| `NODE_TIMEOUT` | ❌ | 终态。建议增大 `timeout_ms` 或拆分 prompt |
| `NODE_EMPTY_OUTPUT` | ❌ | 终态。检查 executor 命令是否真的输出到 stdout |
| `NODE_OUTPUT_REQUIRED` | ❌ | 终态。修 YAML 补 `output:` |
| `LOOP_EXCEEDED` | ❌ | 终态。建议增大 max_iterations 或修 condition |
| `VAR_NOT_IN_SCOPE` | ❌ | 终态。引用了未来节点的 output；检查 nodes 顺序与 alias 拼写 |
| `ENV_VAR_NOT_SET` | ❌ | 终态。`$ENV:VAR` 在环境里找不到，提示用户 export |
| `CALLER_ERROR` | ❌ | 终态。caller 自报错误，按业务决定 |

---

## 高阶能力

### 1. caller handoff — 断点续跑（会话切换后）

caller 启动后**第一件事**应该检查未完成 workflow：

```python
runs = cli("list", {"status": ["waiting_user", "awaiting_agent"]})
if runs["result"]:
    show_to_user(f"你有 {len(runs['result'])} 个未完成 workflow，是否继续？")
    if user_confirms():
        for run in runs["result"]:
            s = cli("status", {"run_id": run["run_id"]})
            if s["result"]["status"] == "waiting_user":
                # last_payload 含原 message/schema，可直接重建提问
                show_to_user(s["result"]["last_payload"]["message"])
                user_input = collect_input(schema=s["result"]["last_payload"].get("schema"))
                response = cli("resume", {"run_id": run["run_id"], "user_input": user_input})
                # 进入主循环
```

### 2. 长链稳定性

| 机制 | 默认 | 触发 |
|---|---|---|
| `chain_timeout_ms` | 25000 | CLI 内部 chain 超时 → 返回 `action:"continue"`，caller 立即重发 advance |
| `stall_timeout_ms` | 300000 | 外部 executor 长时间无 stdout → 强杀 + `EXECUTOR_STALLED` |
| `timeout_ms` | 600000 | 单节点硬超时 |

三档防御保证 caller 永远不会"hang 死无感知"。

### 3. secrets 与 ENV

```yaml
vars:
  api_key: "$ENV:OPENAI_API_KEY"        # start 时从环境变量展开
  user: "alice"
  _secrets: ["api_key"]                 # 标记敏感字段
```

`start` 时：
1. CLI 读取 `OPENAI_API_KEY` 替换占位（找不到 → `ENV_VAR_NOT_SET`）
2. 收集 `_secrets` 中字段的实际值
3. 写入 `events.ndjson` / `audit.log` / `state.json.history` 时自动把这些值替换为 `***REDACTED***`

stdin 模式下 prompt 通过管道传给子进程，不会出现在 shell 历史 / `ps` 输出。

### 4. view — 浏览器可视化

```bash
# 总览（所有 run）
view '{}'
# 单 run 详情（节点拓扑 + cursor 高亮 + history + events 流 + vars）
view '{"run_id":"wf-..."}'
# 不自动开浏览器
view '{"open":false}'
# 自定义输出路径
view '{"out":"./report.html"}'
```

输出为 self-contained HTML（vanilla CSS+内嵌 JS），离线可读可分享。

---

## 输出格式（统一）

成功：

```json
{
  "result": {
    "run_id": "wf-...",
    "status": "awaiting_agent | executing_external | waiting_user | completed | failed | aborted",
    "action": "execute_agent | wait_user | continue | done",
    "node": { "internal_id": "...", "alias": "...", "type": "...", "executor": "..." },
    "payload": { "prompt": "...", "message": "...", "schema": {} },
    "vars": { ... },
    "history_tail": [ ... ]
  },
  "error": null
}
```

错误：

```json
{
  "result": null,
  "error": {
    "code": "EXECUTOR_STALLED",
    "message": "...",
    "retryable": false,
    "suggestion": "...",
    "node": { "internal_id": "...", "alias": "..." },
    "executor": "claude",
    "details": { "exit_code": 124, "stderr_tail": "..." }
  }
}
```

---

## 自然语言交互指南（用户说 / 你做）

| 用户说 | 你做 |
|---|---|
| 跑一下 / 启动 workflow X | `validate` → 校验通过 → `start` |
| 我想做一个 workflow / 创建一个 workflow | `create '{"action":"list_templates"}'` → 推荐合适模板 → `from_template` |
| 检查 / 校验 / lint 一下 YAML | `validate` |
| workflow 跑到哪了 / 进度 / 状态 | `status` 或 `view '{"run_id":"..."}'` |
| 列一下我的 workflow / 都有哪些 run | 用户视角用 `list '{"format":"table"}'` 把 `result.table` 透传；caller 自己用默认 JSON |
| 可视化 / 看一下流程 / 打开浏览器看 | `view '{}'` 或 `view '{"run_id":"..."}'` |
| 停 / 中止 / cancel | `abort` |
| 收到 `execute_agent` | 推理后 → `advance` |
| 收到 `wait_user` | 展示 message → 问用户 → `resume` |
| 收到 `continue` | 立刻 `advance({run_id})` |
| 收到 `done` | 展示 `result.vars` 关键字段，结束 |
| 收到 `error.retryable=true` | 引导用户调整输入 → 重发 resume |
| 收到 `error.retryable=false` | 展示 `message` + `suggestion`，结束 |
| 昨天那个 workflow 接着跑 | `list '{"status":["waiting_user","awaiting_agent"]}'` → 选一个 → `status` 拿 last_payload → `resume` |
| 看下 events / 实时跟进 | `tail -f .agent-workflow/runs/<run_id>/events.ndjson \| jq .` |

---

## 与其他 Skill 协作

| Skill | 协作方式 |
|---|---|
| `agent-interact` | 安装后 `wait_user` 可用弹窗 UI；未安装则降级到 terminal |
| `skill-builder` | 本 skill 由 skill-builder 流程产出；遵循其 10 阶段规范 |
| `prompt-helper` | 用 PRISM 框架优化 workflow 中的 `prompt` 字段质量 |

---

## 故障排查速查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `EXECUTOR_NOT_FOUND` | 外部 CLI 没装 / 不在 PATH | `which claude` / `which codex`；或加 `allow_missing_executors:true` |
| `EXECUTOR_STALLED` | 子进程 300s+ 无 stdout | 增大 `stall_timeout_ms`；或检查 LLM CLI 是否真的卡 |
| `NODE_TIMEOUT` | prompt 过大或外部 CLI 卡住 | 增大 `timeout_ms` / 拆 prompt |
| `VAR_NOT_IN_SCOPE` | 引用了未来节点 output | 修 nodes 顺序或 alias 拼写 |
| `RUN_BUSY` | 并发 advance/resume | 等 1 秒重试 |
| advance 等了 ≥25s 才返回 `continue` | 长链保活触发 | **正常** — 立即重发 advance（不带 result） |
| sleep 节点 abort 没生效 | v1 同步实现 | 等 sleep 自然结束后再 abort |
| 看不到外部 LLM 中间输出 | 设计如此（spawn 模式不流式回吐） | `view` 或 `tail events.ndjson` 看进度 |
| caller 关掉后想继续 | 状态已落盘 | `list` 找未完成 → `status` 拿 last_payload → `resume` |
| 跨 IDE 接力 | v1 不锁 caller 身份 | 任意 caller 都可 resume；audit.log 留痕 |

---

## 调试

```bash
.agent-workflow/runs/<run_id>/
├── state.json         # 当前游标 + history + vars + last_payload + error
├── workflow.yaml      # start 时的快照
├── events.ndjson      # 结构化事件流
├── audit.log          # 可读时间线
└── outputs/           # 节点 result >10KB 时落盘
```

常用命令：

```bash
# 最近 50 条事件
status '{"run_id":"wf-...","include_events":true,"event_limit":50}'

# 浏览器可视化
view '{"run_id":"wf-..."}'

# 实时跟事件流
tail -f .agent-workflow/runs/wf-.../events.ndjson | jq .
```
