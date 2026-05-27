# agent-workflow

> **当前版本**：v1.5.2（已实现，Python 3.10+）
> **完整规约**：见同目录 `SKILL.md`
> **设计与验收**：`design/agent-workflow/` 下 5 份文档

跨 IDE / 跨 LLM 的声明式工作流引擎，以 CLI 状态机形态运行。Claude Code / Cursor / Codex / OpenCode 通用。

---

## 5 分钟上手

### 1. 安装

```bash
cd skills/agent-workflow
pip3 install -r requirements.txt          # 最小依赖
# 或：pip3 install -e .                    # 把 agent-workflow 命令装到 PATH
```

依赖：`PyYAML>=6.0` · `jsonschema>=4.20` · `filelock>=3.13`

### 2. 跑一个内置示例

```bash
# 列出内置模板
python3 tool.py create '{"action":"list_templates"}'

# 从模板拷一份
python3 tool.py create '{
  "action": "from_template",
  "template": "iterative-refine",
  "out": "./flows/demo.yaml"
}'

# 校验
python3 tool.py validate '{"workflow":"./flows/demo.yaml"}'

# 启动（首次会创建 .agent-workflow/runs/wf-...）
python3 tool.py start '{"workflow":"./flows/demo.yaml","caller":"manual"}'
```

启动后 CLI 会返回 `action: execute_agent` / `wait_user` / `continue` / `done` 之一，由 caller（IDE Agent 或你自己）按 `SKILL.md` 中的主循环约定推进。

### 3. 查看运行情况

```bash
# 表格视图（直接给人看）
python3 tool.py list '{"format":"table"}'

# 某个 run 的详情
python3 tool.py status '{"run_id":"wf-..."}'

# 含 events 流
python3 tool.py status '{"run_id":"wf-...","include_events":true}'
```

---

## 10 个 CLI 命令

| Action | 用途 | 详细参数 |
|---|---|---|
| `create` | 列模板 / 从模板生成 / 空白脚手架 | `SKILL.md` §create |
| `validate` | L1 YAML + L2 Schema + L3 引用 + L4 executor PATH | `SKILL.md` §validate |
| `start` | 创建 run，进入第一个节点 | `SKILL.md` §start |
| `advance` | caller 推理完上报 result，继续推进 | `SKILL.md` §advance |
| `resume` | wait_user 收到用户输入后恢复 | `SKILL.md` §resume |
| `status` | 查询单 run 状态 / 历史 / events | `SKILL.md` §status |
| `list` | 列出 run（JSON 或表格） | `SKILL.md` §list |
| `abort` | 主动中止 | `SKILL.md` §abort |
| `executors` | 列出已注册 executor 及 PATH 状态 | `SKILL.md` §executors |
| `view` | 生成自包含 HTML，浏览器可视化查看 run（v1.5.3） | `SKILL.md` §view |

### 可视化 view 命令一行体验

```bash
# 看所有 run（总览 + 每个 run 详情页，自动开浏览器）
python3 skills/agent-workflow/tool.py view '{}'

# 看某个 run 的节点拓扑 + history 时间线 + events 流
python3 skills/agent-workflow/tool.py view '{"run_id":"wf-20260527-100647-6d81e3"}'
```

输出为零外部依赖的 self-contained HTML（vanilla CSS + 内嵌 JS 提供搜索/过滤），离线可读、可分享。

---

## 4 种节点类型

| Type | 行为 | 关键字段 |
|---|---|---|
| `agent_call` | 让 caller 推理或 spawn 外部 LLM CLI | `executor` / `prompt` / `output` |
| `wait_user` | 阻塞等用户输入，可附 JSON Schema 校验 | `message` / `schema` |
| `loop` | 条件循环，支持 do-while 语义 + 步长睡眠 | `condition` / `body` / `max_iterations` |
| `sleep` | 原子睡眠（限流 / 等下游收敛） | `seconds`（0–300） |

---

## v1.5.2 长链稳定性

1. **chain_timeout**（默认 25s）：CLI 内部 chain 太久会返回 `action:"continue"`，caller 立即再发 `advance` 即可，避免 IDE shell 超时。
2. **stall watchdog**（默认 300s）：外部 executor 长时间无 stdout 输出会被强杀并报 `EXECUTOR_STALLED`。
3. **caller handoff**：会话切换后，新 caller 用 `list` 找未完成 run，再用 `status` 拿 `last_payload` 重建提问，无缝接力。

---

## 接外部 LLM CLI（真实跑通的写法）

内置 `claude` / `codex` spec 默认 `cmd: ["claude"]` / `cmd: ["codex","exec"]`，部分版本下 claude 默认进 REPL 不接 stdin，会被 stall watchdog 误杀。推荐在 workflow 里直接 override `cmd`，传 headless flag：

> **opencode 暂未官方支持**：opencode CLI（v0.x）在 stdout 不是 TTY 时只输出第一条 `step_start` 事件后自缓冲死，无法直接被 SpawnExecutor 调用；需要 v1.6 增加 PTY 执行模式后才能接入。当前如需使用，可在 TUI 中手动执行。

```yaml
executors:
  claude:
    kind: spawn
    cmd: ["claude", "-p"]          # -p / --print：headless 模式，stdin 输入 → stdout 输出 → 退出
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

> 已在本机实测：`claude -p` 真实回包平均 8~12s，节点正常完成；`codex exec` 类似。
> 如需统一全局：写入 `~/.agent-workflow/config.yaml` 的 `executors:` 段。

## secrets 与 ENV

`workflow.vars` 中以 `$ENV:NAME` 起始的字符串会在 `start` 时自动展开成环境变量；列在 `vars._secrets` 中的字段名对应的值会被自动从 `events.ndjson` / `audit.log` / `state.json.history` 中脱敏为 `***REDACTED***`。

```yaml
vars:
  api_key: "$ENV:OPENAI_API_KEY"
  user: "alice"
  _secrets: ["api_key"]
```

---

## 测试

测试代码集中在仓库顶层 `tests/agent-workflow/`（与其他 skill 测试统一管理）。

```bash
# 全部单测 + 集成测试
python3 tests/agent-workflow/run_tests.py

# 仅单测
python3 -m unittest discover -s tests/agent-workflow/unit

# 真实 claude 集成测试（opt-in，需本机有 claude CLI）
AGENT_WORKFLOW_REAL_CLAUDE=1 python3 -m unittest tests.agent-workflow.integration.test_real_spawn
```

当前 57 个用例（55 单测 + 1 个真实 python3 spawn 集成测试 + 1 个 claude opt-in skip）。

---

## 目录结构

```
skills/agent-workflow/
├── SKILL.md                  # 给 Agent 看的完整规约（覆盖所有协议细节）
├── README.md                 # 本文件，给人看的快速入门
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

tests/agent-workflow/         # 测试代码（与其他 skill 统一存放在顶层 tests/）
├── run_tests.py              # 统一入口
├── unit/                     # 单测（template / parser / engine / handoff / sleep / stall / secrets ...）
├── integration/              # 真实 spawn 集成测试
└── testdata/flows/           # 测试用 workflow YAML
```

更多协议细节、错误码表、agent 调用约定，全部见 `SKILL.md`。
