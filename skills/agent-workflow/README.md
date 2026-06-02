# agent-workflow

> **当前版本**：v1.6.0（已实现，Python 3.10+）
> **完整 Agent 规约**：`SKILL.md`
> **在线文档**：[docs/index.html](../../docs/index.html) 中 `agent-workflow` 卡片

跨 IDE / 跨 LLM 的声明式工作流引擎，以 CLI 状态机形态运行。**全局存储、渐进式披露** — workflow 定义和运行状态统一存放于 `~/.config/agent-workflow/`，跨项目共享。Claude Code / Cursor / Codex / OpenCode 通用，纯 Python 3.10+ 实现，零运行时网络依赖。

```
+------------------+    YAML       +------------------+    Result    +------------------+
| Workflow Author  | -----------> | tool.py state    | <----------- | Caller Agent /   |
| (用户 / Agent)   |              | machine (Python) | -----------> | External LLM CLI |
+------------------+              +------------------+    Prompt    +------------------+
                                          ^
                                          v
                          disk: ~/.config/agent-workflow/
                          ├── workflows/<name>.yaml
                          └── runs/<run_id>/ (state.json, events.ndjson, audit.log)
```

---

## 目录

1. [它解决什么问题](#它解决什么问题)
2. [何时该用 / 不该用](#何时该用--不该用)
3. [安装](#安装)
4. [渐进式披露：flows 命令](#渐进式披露flows-命令)
5. [5 分钟跑通第一个 workflow](#5-分钟跑通第一个-workflow)
6. [Workflow YAML 完整写法](#workflow-yaml-完整写法)
7. [4 种节点类型字段速查](#4-种节点类型字段速查)
8. [11 个 CLI 命令](#11-个-cli-命令)
9. [集成到 IDE Agent：caller 主循环](#集成到-ide-agent-caller-主循环)
10. [接外部 LLM CLI（真实跑通的写法）](#接外部-llm-cli真实跑通的写法)
11. [view 命令：浏览器可视化 run](#view-命令浏览器可视化-run)
12. [长链稳定性：chain_timeout & stall watchdog](#长链稳定性chain_timeout--stall-watchdog)
13. [secrets 与 ENV](#secrets-与-env)
14. [错误处理：retryable 判定](#错误处理retryable-判定)
15. [调试 recipes](#调试-recipes)
16. [测试](#测试)
17. [目录结构](#目录结构)
18. [FAQ](#faq)

---

## 它解决什么问题

让 AI Agent 跑**多步、可中断、可恢复、可审计**的工作流，**核心思想**：

- **CLI 不做推理**，只做状态机。所有"动脑子"的事，要么交给 caller（你 IDE 里的 Agent），要么 spawn 外部 LLM CLI（claude / codex / opencode 等）。
- **声明式 YAML 描述流程**，节点串行 → 用户阻塞 → 条件循环 → 跨 LLM 协作都可在一个文件里说清楚。
- **状态全部落盘**，CLI 进程可以随时被 kill，下次跑 `status` / `advance` / `resume` 接着走。
- **统一错误对象**，每次失败都有 `code` + `retryable` + `suggestion`，caller 能根据这个决定要不要重试。

---

## 何时该用 / 不该用

| ✅ 该用 | ❌ 不该用 |
|---|---|
| 多步任务（≥3 节点） | 单次问答 / 2-3 步纯 prompt chain |
| 需要用户阻塞确认（`wait_user`） | 临时一次性任务 |
| 需要条件循环（`loop`） | 单一 LLM 内部推理（CoT 即可） |
| 跨 LLM CLI 协作（Claude+Codex+caller） | 不需要审计 / 进度可见的内部计算 |
| 可重复执行的 SOP（每次跑都按同一份 YAML） | 流程结构每次都变的探索性对话 |
| 需要审计追溯每一步 | |

---

## 安装

```bash
cd skills/agent-workflow
pip3 install -r requirements.txt
# 或：pip3 install -e .   # 把 agent-workflow 装到 PATH（之后可直接用 `agent-workflow ...`）
```

依赖：`PyYAML>=6.0` · `jsonschema>=4.20` · `filelock>=3.13`（运行时全部为标准 Python 包，零网络调用）。

验证安装：

```bash
python3 skills/agent-workflow/tool.py executors '{}'
# 返回已注册 executor 列表（默认含 caller / mock / claude / codex / opencode）
```

---

## 渐进式披露：flows 命令

`flows` 是 v1.6 新增的**发现入口**。AI Agent 通过 `flows` 发现全局已注册的 workflow，按 `triggers` / `description` 匹配用户意图后自动 `start`：

```bash
# 列出所有全局 workflow
agent-workflow flows '{}'

# 按关键词搜索
agent-workflow flows '{"query":"review"}'
```

返回示例：

```json
{
  "result": {
    "workflows": [
      {
        "name": "code-review",
        "description": "对一个 PR / Diff 做多角度评审",
        "triggers": ["代码审查", "review MR", "帮我看看代码"],
        "node_count": 4,
        "path": "/Users/you/.config/agent-workflow/workflows/code-review.yaml"
      }
    ],
    "count": 1,
    "workflows_root": "/Users/you/.config/agent-workflow/workflows"
  }
}
```

### triggers 字段

每个 workflow YAML 可声明 `triggers`（字符串数组），描述触发该 workflow 的自然语言模式：

```yaml
name: code-review
triggers:
  - "代码审查"
  - "review 这个 MR"
  - "帮我看看这段代码"
description: 调研 → 代码审查 → 用户确认 → 输出报告
```

AI Agent 的判断流程：

1. 用户说了一句话
2. Agent 调 `flows '{}'` 获取所有可用 workflow
3. 遍历 `triggers` + `description`，判断匹配度
4. 匹配到 → `start '{"workflow":"code-review"}'`
5. 不匹配 → 正常推理或创建新 workflow

---

## 5 分钟跑通第一个 workflow

```bash
# 1) 列出全局已有 workflow
agent-workflow flows '{}'

# 2) 从模板创建到全局目录
agent-workflow create '{
  "action":"from_template",
  "template":"iterative-refine"
}'

# 3) 4 级校验（按 name 查找）
agent-workflow validate '{"workflow":"iterative-refine"}'
# → {"result": {"valid": true, "stats": {...}}}

# 4) 启动 run（按 name 启动）
agent-workflow start '{"workflow":"iterative-refine","caller":"manual"}'
# → {"result": {"action": "execute_agent" | "wait_user" | "continue" | "done", ...}}

# 5) 浏览器查看进度
agent-workflow view '{}'
# → 自动打开总览页（每行一个 run，可点击进入详情）
```

`start` / `advance` / `resume` 三个动作的返回值都是同样结构（见下面 caller 主循环章节）。

---

## Workflow YAML 完整写法

一个能跑的最小例子（含所有节点类型）：

```yaml
name: full-demo
description: 演示所有节点类型

config:
  chain_timeout_ms: 25000      # CLI 内部 chain 超过这个会主动 pause（可选）

executors:                     # 局部 executor，覆盖内置同名 spec（可选）
  claude:
    kind: spawn
    cmd: ["claude", "-p"]
    input_mode: stdin
    timeout_ms: 60000
    stall_timeout_ms: 30000

vars:                          # workflow 级变量，可在 prompt 里用 {{var}}
  topic: "OAuth 登录"
  api_key: "$ENV:OPENAI_API_KEY"   # start 时自动从环境变量展开
  _secrets: ["api_key"]            # 标记敏感字段（自动脱敏）

nodes:
  - alias: research               # ① 让 caller 做调研
    type: agent_call
    executor: caller
    prompt: "针对 {{topic}} 调研 3 种实现思路"
    output: ideas

  - alias: pick_one               # ② 让用户挑一个
    type: wait_user
    message: "三种思路你想用哪个？给个选择 + 理由"
    schema:
      type: object
      required: [choice]
      properties:
        choice:   { type: string }
        reason:   { type: string, default: "" }

  - alias: cool_down              # ③ 限流 1s（可选）
    type: sleep
    seconds: 1

  - alias: implement_loop         # ④ 实现 + 评审 循环
    type: loop
    condition: "{{review.approved}} == false"
    max_iterations: 5
    step_sleep_ms: 500
    body:
      - alias: implement
        type: agent_call
        executor: claude          # 交给 Claude
        prompt: "基于选择 {{pick_one.choice}} 实现代码"
        output: code

      - alias: review
        type: wait_user
        message: "Review code:\n{{code}}\n通过吗？"
        schema:
          type: object
          required: [approved]
          properties:
            approved: { type: boolean }
            feedback: { type: string, default: "" }

  - alias: final_report           # ⑤ 总结
    type: agent_call
    executor: caller
    prompt: "总结这一轮：选择={{pick_one.choice}}，代码={{code}}"
    output: report
```

要点：

- **`alias` 是人读 ID，必须在 workflow 内全局唯一**；CLI 内部还会再分配一个 `_internal_id`（UUID 短串）做引擎引用。
- **`output: NAME`** 把节点 result 写入 `vars.NAME`，后续节点用 `{{NAME}}` 引用；
  `wait_user` 的输出按 `alias` 自动存（`{{pick_one.choice}}`）。
- **`condition`** 是简单表达式，支持 `==` / `!=` / `<` / `>` / `<=` / `>=` / `and` / `or` / 字符串相等比较。
- **`loop` 第一次迭代默认 do-while**：condition 里未定义的变量被宽松判定为 truthy，保证 body 至少跑一次。

---

## 4 种节点类型字段速查

### `agent_call` — 让 caller / 外部 LLM 推理

| 字段 | 必填 | 说明 |
|---|---|---|
| `alias` | ✅ | 唯一人读 ID |
| `type` | ✅ | `agent_call` |
| `executor` | ✅ | `caller` 或已注册的 spawn executor 名 |
| `prompt` | ✅ | 模板字符串，支持 `{{var}}` |
| `output` | 推荐 | 把 result 写到 `vars.<name>` |
| `description` | 可选 | 给 caller 看的节点说明 |
| `timeout_ms` | 可选 | 单节点超时（覆盖 executor 默认） |
| `context_files` | 可选 | spawn 时把文件内容拼到 prompt 前 |
| `agent` | 可选 | v1.5.4+ agent 上下文：`{role: "...", skills: [...]}`，caller payload 透传 / spawn 自动拼 stdin 前缀（详见 SKILL.md「节点类型速查」） |

### `wait_user` — 阻塞等用户输入

| 字段 | 必填 | 说明 |
|---|---|---|
| `alias` | ✅ | |
| `type` | ✅ | `wait_user` |
| `message` | ✅ | 给用户看的提问（模板） |
| `schema` | 可选 | JSON Schema，CLI 自动校验用户输入 |
| `default` | 可选 | 用户跳过时的默认值 |

resume 时 CLI 会用 `schema` 校验 `input`，失败返回 `SCHEMA_VIOLATION`（retryable=true）。

### `loop` — 条件循环

| 字段 | 必填 | 说明 |
|---|---|---|
| `alias` | ✅ | |
| `type` | ✅ | `loop` |
| `condition` | ✅ | 表达式（每轮结束后求值，true 继续） |
| `body` | ✅ | 数组，至少 1 个节点 |
| `max_iterations` | ✅ | 1–100，防死循环 |
| `step_sleep_ms` | 可选 | 每轮间隔毫秒数（0–60000） |

### `sleep` — 原子睡眠

| 字段 | 必填 | 说明 |
|---|---|---|
| `alias` | ✅ | |
| `type` | ✅ | `sleep` |
| `seconds` | ✅ | 0–300，支持小数 |

---

## 12 个 CLI 命令

| Action | 用途 |
|---|---|
| `flows` | **v1.6** 列出全局可用 workflow 定义（渐进式披露入口） |
| `create` | 列模板 / 从模板生成 / 空白脚手架 |
| `validate` | L1 YAML + L2 Schema + L3 引用 + L4 executor PATH |
| `start` | 创建 run（支持 name 或路径），进入第一个节点 |
| `advance` | caller 推理完上报 result，继续推进 |
| `resume` | wait_user 收到用户输入后恢复 |
| `retry` | **v1.7** caller 显式从断点 / 指定 alias 续跑（支持 vars_patch / skip） |
| `status` | 查询单 run 状态 / 历史 / events |
| `list` | 列出 run（JSON 或表格） |
| `abort` | 主动中止 |
| `executors` | 列出已注册 executor 及 PATH 状态 |
| `view` | 生成自包含 HTML，浏览器可视化查看 run |

每条命令的完整参数与返回，见 `SKILL.md`。

### `retry` —— 节点失败 / 卡住后从断点续跑

适用场景：节点失败、`execute_agent` 卡住超时、用户拿到中间产物后想倒回来重跑、想跳过某个失败节点。

```jsonc
// 默认：从最后失败的节点重跑
retry '{"run_id":"wf-..."}'

// 显式倒回到某个 alias
retry '{"run_id":"wf-...","alias":"step_a"}'

// 改 vars 后重跑（深合并到 state.vars）
retry '{"run_id":"wf-...","vars_patch":{"topic":"new"}}'

// 跳过失败节点：手动给 output，直接进入下一节点
retry '{"run_id":"wf-...","skip":true,"vars_patch":{"step_b_output":"manually-filled"}}'
```

行为：

1. cursor 重置到目标节点（按 alias 解析；不传 alias → 按 history → pending → cursor 顺序推断）
2. history 中从目标节点开始的旧记录被裁掉（events.ndjson 保留完整审计）
3. `error / last_payload / pending_node` 清空，`status` 翻回 `awaiting_agent`
4. `skip=true` 时把 `vars_patch` 写进 vars + 追加一条 `status: skipped` history，cursor 直接前进
5. 写 `retry_invoked` event/audit，含 `target_alias / target_path / skip / vars_patch_keys`

约束：

- 仅在 `status ∈ {failed, awaiting_agent, waiting_user, executing_external}` 时可调用；`completed / aborted` 不可重试
- `skip=true` 只对 `agent_call / wait_user` 有意义
- `retry` 是唯一允许重置 cursor 的入口；`advance / resume` 永远沿 cursor 前进

---

## 集成到 IDE Agent：caller 主循环

把 agent-workflow 嵌入你自己 Agent 的最小骨架（伪代码）：

```python
import json, subprocess

def call(action, params):
    r = subprocess.run(
        ["python3", "skills/agent-workflow/tool.py", action, json.dumps(params)],
        capture_output=True, text=True, timeout=120
    )
    return json.loads(r.stdout)

# 1) 启动（按 name 或路径）
resp = call("start", {"workflow": "iterative-refine", "caller": "my-agent"})

while True:
    data = resp.get("result")
    err  = resp.get("error")

    if err:
        if err["retryable"]:
            # 把 err.message / err.suggestion 展给用户，拿到修正再 resume
            ...
            continue
        # 非 retryable：可询问用户是否走 retry 入口从断点续跑
        if user_wants_retry():
            resp = call("retry", {"run_id": data["run_id"]})  # 默认从最后失败节点
            continue
        raise RuntimeError(err["message"])

    action = data["action"]
    run_id = data["run_id"]

    if action == "execute_agent":
        # CLI 让 caller（你）来推理；payload 里有 prompt
        prompt = data["payload"]["prompt"]
        output = my_llm.infer(prompt)
        resp = call("advance", {"run_id": run_id, "result": {"output": output}})

    elif action == "wait_user":
        # 把 payload.message 显示给用户，按 schema 收集输入
        user_input = ask_user(data["payload"]["message"], data["payload"].get("schema"))
        resp = call("resume", {"run_id": run_id, "input": user_input})

    elif action == "continue":
        # CLI 内部 chain 超时主动返回，立即再发一次 advance（不带 result）
        resp = call("advance", {"run_id": run_id})

    elif action == "done":
        print("workflow finished:", data.get("vars"))
        break
```

关键不变量：

- `start` / `advance` / `resume` 返回结构一致，主循环不需要分支判断"现在是哪个 action 调用的"。
- 收到 `action: "continue"`：**立即再发** `advance`，CLI 会从内部 cursor 接着跑。
- 收到 `error.retryable == true`：让用户改后再调同一个 action（典型场景：`SCHEMA_VIOLATION`）。
- 收到 `error.retryable == false`：终态，停止主循环，把错误展给用户。

---

## 接外部 LLM CLI（真实跑通的写法）

> **opencode 暂未官方支持**：opencode CLI（v0.x）在 stdout 不是 TTY 时只输出第一条 `step_start` 事件后自缓冲死，无法直接被 SpawnExecutor 调用；需要 v1.6 增加 PTY 执行模式后才能接入。当前请在 TUI 中手动使用。

内置 `claude` / `codex` 默认 `cmd` 在某些版本下会进 REPL 模式不接 stdin，会被 stall watchdog 误杀。**推荐在 workflow 里 override `cmd` 传 headless flag**：

```yaml
executors:
  claude:
    kind: spawn
    cmd: ["claude", "-p"]          # -p / --print：headless 模式，stdin → stdout → 退出
    input_mode: stdin
    stall_timeout_ms: 30000
    timeout_ms: 60000
  codex:
    kind: spawn
    cmd: ["codex", "exec"]         # codex exec：headless 模式
    input_mode: stdin
    stall_timeout_ms: 30000
    timeout_ms: 60000

nodes:
  - alias: ask
    type: agent_call
    executor: claude
    prompt: "Reply with exactly the single word: PONG"
    output: result
```

实测：`claude -p` 平均回包 8–12s，`codex exec` 类似。如需全局生效：写入 `~/.config/agent-workflow/config.yaml` 的 `executors:` 段，所有 workflow 都会继承。

---

## view 命令：浏览器可视化 run

```bash
# 所有 run 总览（自动打开浏览器）
python3 skills/agent-workflow/tool.py view '{}'

# 单 run 详情（节点拓扑 + cursor 高亮 + history + events 流）
python3 skills/agent-workflow/tool.py view '{"run_id":"wf-20260527-100647-6d81e3"}'

# 不自动打开，只生成文件
python3 skills/agent-workflow/tool.py view '{"open":false}'

# 自定义输出路径
python3 skills/agent-workflow/tool.py view '{"out":"./report.html"}'
```

页面构成（self-contained，零外部依赖）：

```
┌──────────────────────────────────────────────────────────┐
│ workflow-name · wf-20260527-100647-6d81e3                │
│ [waiting_user]  caller: manual  created: ...  updated:.. │
├──────────────────────────────────────────────────────────┤
│ Nodes                                                     │
│  ● research      agent_call · executor: mock      0 ms   │
│  ● design        agent_call · executor: mock      0 ms   │
│  ● cool_down     sleep · seconds: 0               0 ms   │
│  ● ask          ←──── wait_user                  (cursor)│
│  ○ final         agent_call · executor: mock             │
├──────────────────────────────────────────────────────────┤
│ History (3) · table                                       │
├──────────────────────────────────────────────────────────┤
│ Events (12) · time stream                                 │
├──────────────────────────────────────────────────────────┤
│ vars · json                                               │
└──────────────────────────────────────────────────────────┘
```

总览页支持按 status 过滤 + 全文搜索（Cmd/Ctrl + F 即可），点击 run_id 跳转单 run 详情。

---

## 长链稳定性：chain_timeout & stall watchdog

| 机制 | 默认 | 作用 |
|---|---|---|
| `chain_timeout_ms` | 25000 | CLI 内部 chain 超过这个值会返回 `action:"continue"`，caller 立即再发 advance 即可。**避免 IDE shell 子进程超时** |
| `stall_timeout_ms` | 300000 | 外部 executor 长时间无 stdout 输出 → 强杀 + `EXECUTOR_STALLED`。**避免 caller hang 死** |
| `timeout_ms` | 600000 | 单节点硬超时，到点强杀 |
| caller handoff | — | 会话切换后，新 caller 用 `list` 找未完成 → `status` 拿 `last_payload` 重建提问 → 继续 |

三档防御组合，保证 workflow 跑几分钟到几十分钟都不会"卡死无感知"。

---

## secrets 与 ENV

```yaml
vars:
  api_key: "$ENV:OPENAI_API_KEY"   # start 时自动从环境变量展开
  db_pwd:  "$ENV:DB_PASSWORD"
  user:    "alice"
  _secrets: ["api_key", "db_pwd"]
```

`start` 时：

1. CLI 读取 `OPENAI_API_KEY` / `DB_PASSWORD` 替换占位（找不到时报 `ENV_VAR_NOT_SET`）。
2. 收集 `_secrets` 中字段的**实际值**到 contextvar。
3. 之后所有写入 `events.ndjson` / `audit.log` / `state.json.history` 的内容自动把这些值替换为 `***REDACTED***`。

`stdin` 模式下 prompt 直接通过管道传给子进程，**不会出现在 shell 历史 / `ps` 输出 / 错误日志**。

---

## 错误处理：retryable 判定

所有错误统一为：

```json
{
  "code": "SCHEMA_VIOLATION",
  "message": "wait_user input does not match schema: 'approved' is a required property",
  "retryable": true,
  "suggestion": "ask user to provide a boolean for 'approved'",
  "location": { "alias": "review", "field": "approved" }
}
```

caller 判定规则：

| 错误码 | retryable | 处理 |
|---|---|---|
| `SCHEMA_VIOLATION` | ✅ | 把 message+suggestion 展给用户，让用户改输入后再 resume |
| `RUN_BUSY` | ✅ | 等 1s 重试同一个动作 |
| `WORKFLOW_INVALID` | ❌ | 终态，展给用户修 YAML |
| `EXECUTOR_NOT_FOUND` | ❌ | 终态，提示安装对应 CLI |
| `EXECUTOR_STALLED` | ❌ | 终态，检查外部 CLI 状态 → **可走 `retry` 让用户决定从断点续跑** |
| `EXECUTOR_NONZERO_EXIT` | ❌ | 终态，看 `stderr_tail` → **可走 `retry` 让用户决定从断点续跑** |
| `NODE_TIMEOUT` / `NODE_EMPTY_OUTPUT` | ❌ | 终态 → **可走 `retry`** |
| `LOOP_EXCEEDED` | ❌ | 终态，业务方修 condition / max_iterations |
| `RUN_NOT_FOUND` | ❌ | 终态，run_id 不对 |

完整错误码表见 `SKILL.md`。

> 对所有非 `retryable` 的执行类错误（executor / timeout / empty output），caller 可以询问用户是否走 `retry` 入口从失败节点续跑，详见上面《`retry` —— 节点失败 / 卡住后从断点续跑》章节。

---

## 调试 recipes

每个 run 在 `~/.config/agent-workflow/runs/<run_id>/` 下有完整审计目录：

```
state.json          # 当前游标 + history + vars + last_payload + error
workflow.yaml       # 启动时的快照（带分配的 _internal_id）
events.ndjson       # 结构化事件流：run_start / node_start / spawn_* / sleep_* / node_end / error / pause / resume / run_end / abort
audit.log           # 可读时间线
outputs/            # 单节点 result > 10KB 时落盘
```

常用排查：

```bash
# 1) 看当前状态 + 最近 50 条事件
python3 skills/agent-workflow/tool.py status \
  '{"run_id":"wf-...","include_events":true,"event_limit":50}'

# 2) 浏览器可视化
python3 skills/agent-workflow/tool.py view '{"run_id":"wf-..."}'

# 3) 实时跟 events 流
tail -f ~/.config/agent-workflow/runs/wf-.../events.ndjson | jq .

# 4) 看 audit.log 时间线
less ~/.config/agent-workflow/runs/wf-.../audit.log
```

---

## 测试

测试代码集中在仓库顶层 `tests/agent-workflow/`（与其他 skill 测试统一管理）。

```bash
# 全部用例（单测 + 集成）
python3 tests/agent-workflow/run_tests.py

# 仅单测
python3 -m unittest discover -s tests/agent-workflow/unit

# 真实 claude 集成测试（opt-in）
AGENT_WORKFLOW_REAL_CLAUDE=1 python3 -m unittest tests.agent-workflow.integration.test_real_spawn
```

当前 **57 个用例**（55 单测 + 1 真实 `python3` spawn 集成 + 1 claude opt-in skip），跑完约 1.7s。

---

## 目录结构

```
skills/agent-workflow/
├── SKILL.md                  # 给 Agent 看的完整规约
├── README.md                 # 本文件（给人看的完整用户指南）
├── pyproject.toml            # Python 3.10+ 项目元数据
├── requirements.txt
├── tool.py                   # CLI 入口
├── schemas/workflow.schema.json
├── examples/                 # 4 个内置 workflow 模板
└── lib/                      # 引擎实现
    ├── errors.py logger.py template.py parser.py store.py engine.py
    ├── nodes/                # agent_call / wait_user / loop / sleep
    ├── executors/            # base/caller/mock + registry
    ├── builder/scaffold.py   # create 命令实现
    └── view/render.py        # view 命令：HTML 渲染（v1.5.3）

tests/agent-workflow/         # 测试代码（顶层 tests/ 集中管理）
├── run_tests.py
├── unit/                     # template / parser / engine / handoff / sleep / stall / secrets / view ...
├── integration/              # 真实 spawn 集成
└── testdata/flows/           # 测试用 workflow YAML

docs/                         # skillix-hub 文档站（agent-workflow 已注册其中）
├── index.html
└── scripts/skills/agent-workflow.js
```

---

## FAQ

**Q: 不写 caller 也能跑吗？**
A: 能。所有 `executor: caller` 的节点都换成 spawn executor（如 `claude` / `codex`），再 cron / 脚本直跑 `start`，CLI 内部 chain 跑完整个 workflow。

**Q: workflow 跑到一半 IDE 重启了怎么办？**
A: 所有状态在 `~/.config/agent-workflow/runs/<run_id>/state.json`（全局存储，跨项目共享）。重启后用 `list '{"status":["waiting_user","awaiting_agent"]}'` 找未完成的 run，用 `status` 拿 `last_payload` 重建上下文，直接 `resume` / `advance` 即可。

**Q: 一个 prompt 太长（几 KB）有问题吗？**
A: 没问题。stdin 模式下 prompt 通过管道传给子进程，无 argv 长度限制。`output: result` 超过 10KB 时自动落盘到 `outputs/<uuid>.txt`，state.json 里只存 `result_head` + `result_file`。

**Q: caller 中途死掉了 / 网络断了怎么办？**
A: CLI 与 caller 之间是无状态调用，每次 `advance` / `resume` 都是单独进程。caller 死了等于"暂停"，重启后接着调即可。

**Q: 多个 caller 同时 `advance` 同一个 run 会怎样？**
A: filelock 互斥。后到的会立刻拿到 `RUN_BUSY` 错误（retryable），caller 等 1s 重试即可。

**Q: 怎么扩展自己的 executor？**
A: 在 workflow 的 `executors:` 段下声明 `kind: spawn` + `cmd` + `input_mode`，CLI 自动 spawn 子进程。要支持 PTY / HTTP 等更复杂模式，需要在 `lib/executors/` 下加新 `kind`（v1.6 计划）。

**Q: 怎么写新的 workflow 模板？**
A: 内置模板放 `skills/agent-workflow/examples/<name>.yaml`；用户自己的 workflow 放 `~/.config/agent-workflow/workflows/<name>.yaml`，`flows '{}'` 会自动发现。

**Q: 这套设计能扛多大的 workflow？**
A: 当前实测 100 节点 / 50 轮 loop / 跑 15 分钟无问题。`chain_timeout` + `stall_watchdog` + `caller_handoff` 三档保底，主要瓶颈在外部 LLM CLI 的速度，不在 CLI 本体。

---

更多协议细节、错误码全表、agent 调用约定 → `SKILL.md`。
