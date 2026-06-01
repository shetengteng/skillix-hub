# agent-workflow

> **Version**: v1.6.0 (Python 3.10+)
> **Agent Spec**: `SKILL.md`
> **Online docs**: [docs/index.html](../../docs/index.html) `agent-workflow` card

A declarative, cross-IDE / cross-LLM workflow engine running as a CLI state machine. **Global storage with progressive disclosure** — workflow definitions and run states are stored in `~/.config/agent-workflow/`, shared across projects. Works with Claude Code, Cursor, Codex and OpenCode. Pure Python 3.10+, zero runtime network dependencies.

```
+------------------+    YAML       +------------------+    Result    +------------------+
| Workflow Author  | -----------> | tool.py state    | <----------- | Caller Agent /   |
| (User / Agent)   |              | machine (Python) | -----------> | External LLM CLI |
+------------------+              +------------------+    Prompt    +------------------+
                                          ^
                                          v
                          disk: ~/.config/agent-workflow/
                          ├── workflows/<name>.yaml
                          └── runs/<run_id>/ (state.json, events.ndjson, audit.log)
```

---

## Table of Contents

1. [What Problem It Solves](#what-problem-it-solves)
2. [When to Use / Not to Use](#when-to-use--not-to-use)
3. [Installation](#installation)
4. [Progressive Disclosure: flows Command](#progressive-disclosure-flows-command)
5. [5-Minute Quick Start](#5-minute-quick-start)
6. [Workflow YAML Reference](#workflow-yaml-reference)
7. [4 Node Types](#4-node-types)
8. [11 CLI Commands](#11-cli-commands)
9. [IDE Agent Integration: Caller Main Loop](#ide-agent-integration-caller-main-loop)
10. [External LLM CLI Integration](#external-llm-cli-integration)
11. [view Command: Browser Visualization](#view-command-browser-visualization)
12. [Long-Run Stability](#long-run-stability)
13. [Secrets & ENV](#secrets--env)
14. [Error Handling](#error-handling)
15. [Debugging](#debugging)
16. [Testing](#testing)
17. [Directory Structure](#directory-structure)
18. [FAQ](#faq)

---

## What Problem It Solves

Enables AI Agents to run **multi-step, interruptible, recoverable, auditable** workflows:

- **CLI does no reasoning** — it's a pure state machine. All "thinking" is delegated to the caller (your IDE Agent) or spawned external LLM CLIs (claude / codex / opencode).
- **Declarative YAML** describes the flow: serial nodes → user-blocking → conditional loops → cross-LLM collaboration — all in one file.
- **Full disk persistence** — CLI process can be killed anytime; next `status` / `advance` / `resume` picks up where it left off.
- **Unified error objects** — every failure has `code` + `retryable` + `suggestion`, so the caller knows whether to retry.

---

## When to Use / Not to Use

| ✅ Good fit | ❌ Not for |
|---|---|
| Multi-step tasks (≥3 nodes) | One-shot Q&A / 2-3 step prompt chains |
| User-blocking confirmation (`wait_user`) | Disposable tasks |
| Conditional loops (`loop`) | Single-LLM internal reasoning (CoT) |
| Cross-LLM CLI collaboration | No audit/progress visibility needed |
| Repeatable SOPs | Structure changes every time |
| Audit trail needed | |

---

## Installation

```bash
pip3 install -e skills/agent-workflow/
# Installs `agent-workflow` CLI globally
```

Dependencies: `PyYAML>=6.0` · `jsonschema>=4.20` · `filelock>=3.13` (all standard Python packages, zero network calls).

Verify:

```bash
agent-workflow executors '{}'
# Returns registered executor list (default: caller / mock / claude / codex / opencode)
```

---

## Progressive Disclosure: flows Command

`flows` is the **discovery entry point** added in v1.6. The AI Agent calls `flows` to discover globally registered workflows, matches user intent against `triggers` / `description`, then auto-starts the matching workflow:

```bash
# List all global workflows
agent-workflow flows '{}'

# Search by keyword
agent-workflow flows '{"query":"review"}'
```

### triggers Field

Each workflow YAML can declare `triggers` (string array) describing natural language patterns:

```yaml
name: code-review
triggers:
  - "code review"
  - "review this MR"
  - "look at my code"
description: Scan → Review → User confirm → Report
```

Agent decision flow:

1. User says something
2. Agent calls `flows '{}'` to get available workflows
3. Matches `triggers` + `description` against user intent
4. Match found → `start '{"workflow":"code-review"}'`
5. No match → normal reasoning or create new workflow

---

## 5-Minute Quick Start

```bash
# 1) List globally available workflows
agent-workflow flows '{}'

# 2) Create from built-in template
agent-workflow create '{
  "action":"from_template",
  "template":"iterative-refine"
}'

# 3) Validate (by name)
agent-workflow validate '{"workflow":"iterative-refine"}'

# 4) Start run (by name)
agent-workflow start '{"workflow":"iterative-refine","caller":"manual"}'
# → {"result": {"action": "execute_agent" | "wait_user" | "continue" | "done", ...}}

# 5) Visualize in browser
agent-workflow view '{}'
```

`start` / `advance` / `resume` all return the same structure (see caller main loop below).

---

## Workflow YAML Reference

Minimal example with all node types:

```yaml
name: full-demo
description: Demonstrates all node types
triggers:
  - "run full demo"
  - "show all node types"

config:
  chain_timeout_ms: 25000

executors:
  claude:
    kind: spawn
    cmd: ["claude", "-p"]
    input_mode: stdin
    timeout_ms: 60000
    stall_timeout_ms: 30000

vars:
  topic: "OAuth login"
  api_key: "$ENV:OPENAI_API_KEY"
  _secrets: ["api_key"]

nodes:
  - alias: research
    type: agent_call
    executor: caller
    prompt: "Research 3 approaches for {{topic}}"
    output: ideas

  - alias: pick_one
    type: wait_user
    message: "Which approach? Give your choice and reason"
    schema:
      type: object
      required: [choice]
      properties:
        choice:   { type: string }
        reason:   { type: string, default: "" }

  - alias: cool_down
    type: sleep
    seconds: 1

  - alias: implement_loop
    type: loop
    condition: "{{review.approved}} == false"
    max_iterations: 5
    body:
      - alias: implement
        type: agent_call
        executor: claude
        prompt: "Implement based on {{pick_one.choice}}"
        output: code
      - alias: review
        type: wait_user
        message: "Review:\n{{code}}\nApprove?"
        schema:
          type: object
          required: [approved]
          properties:
            approved: { type: boolean }
            feedback: { type: string, default: "" }

  - alias: final_report
    type: agent_call
    executor: caller
    prompt: "Summarize: choice={{pick_one.choice}}, code={{code}}"
    output: report
```

Key points:

- **`alias`** is the human-readable ID, must be unique within the workflow.
- **`output: NAME`** writes node result to `vars.NAME`; downstream nodes reference with `{{NAME}}`.
- **`triggers`** (optional) enables progressive disclosure — AI matches user intent to decide if this workflow applies.
- **`loop` uses do-while semantics** on first iteration: undefined variables in condition are treated as truthy.

---

## 4 Node Types

### `agent_call` — reasoning node

| Field | Required | Description |
|---|---|---|
| `alias` | ✅ | Unique human-readable ID |
| `type` | ✅ | `agent_call` |
| `executor` | ✅ | `caller` or registered spawn executor |
| `prompt` | ✅ | Template string, supports `{{var}}` |
| `output` | Recommended | Writes result to `vars.<name>` |
| `agent` | Optional | v1.5.4+ context: `{role: "...", skills: [...]}` |

### `wait_user` — blocks until user input

| Field | Required | Description |
|---|---|---|
| `alias` | ✅ | |
| `type` | ✅ | `wait_user` |
| `message` | ✅ | Prompt shown to user (template) |
| `schema` | Optional | JSON Schema for input validation |

### `loop` — conditional loop

| Field | Required | Description |
|---|---|---|
| `alias` | ✅ | |
| `type` | ✅ | `loop` |
| `condition` | ✅ | Expression evaluated after each iteration |
| `body` | ✅ | Array of child nodes (≥1) |
| `max_iterations` | ✅ | 1–100, safety cap |

### `sleep` — atomic pause

| Field | Required | Description |
|---|---|---|
| `alias` | ✅ | |
| `type` | ✅ | `sleep` |
| `seconds` | ✅ | 0–300 |

---

## 11 CLI Commands

| Action | Purpose |
|---|---|
| `flows` | **v1.6** List globally available workflow definitions (progressive disclosure) |
| `create` | List templates / create from template / scaffold |
| `validate` | L1 YAML + L2 Schema + L3 references + L4 executor PATH |
| `start` | Create run (by name or path), enter first node |
| `advance` | Caller reports reasoning result, continue |
| `resume` | Resume wait_user with user input |
| `status` | Query single run state / history / events |
| `list` | List runs (JSON or table) |
| `abort` | Abort a run |
| `executors` | List registered executors and PATH status |
| `view` | Generate self-contained HTML visualization |

Full parameter and return specs in `SKILL.md`.

---

## IDE Agent Integration: Caller Main Loop

```python
import json, subprocess

def call(action, params):
    r = subprocess.run(
        ["agent-workflow", action, json.dumps(params)],
        capture_output=True, text=True, timeout=120
    )
    return json.loads(r.stdout)

# 1) Start (by name or path)
resp = call("start", {"workflow": "iterative-refine", "caller": "my-agent"})

while True:
    data = resp.get("result")
    err  = resp.get("error")

    if err:
        if err["retryable"]:
            # show err.message / err.suggestion to user, get fix, resume
            ...
            continue
        else:
            raise RuntimeError(err["message"])

    action = data["action"]
    run_id = data["run_id"]

    if action == "execute_agent":
        prompt = data["payload"]["prompt"]
        output = my_llm.infer(prompt)
        resp = call("advance", {"run_id": run_id, "result": {"output": output}})

    elif action == "wait_user":
        user_input = ask_user(data["payload"]["message"], data["payload"].get("schema"))
        resp = call("resume", {"run_id": run_id, "input": user_input})

    elif action == "continue":
        resp = call("advance", {"run_id": run_id})

    elif action == "done":
        print("Workflow finished:", data.get("vars"))
        break
```

---

## External LLM CLI Integration

Recommended executor overrides for headless mode:

```yaml
executors:
  claude:
    kind: spawn
    cmd: ["claude", "-p"]
    input_mode: stdin
    stall_timeout_ms: 30000
    timeout_ms: 60000
  codex:
    kind: spawn
    cmd: ["codex", "exec", "--skip-git-repo-check"]
    input_mode: stdin
    stall_timeout_ms: 30000
    timeout_ms: 60000
```

---

## view Command: Browser Visualization

```bash
agent-workflow view '{}'                                    # overview (auto-opens browser)
agent-workflow view '{"run_id":"wf-20260527-100647-6d81e3"}'  # single run detail
agent-workflow view '{"open":false}'                        # generate without opening
agent-workflow view '{"out":"./report.html"}'               # custom output path
```

Self-contained HTML (vanilla CSS + inline JS): node topology, cursor highlight, status pills, history timeline, events stream, vars. Offline-shareable.

---

## Long-Run Stability

| Mechanism | Default | Purpose |
|---|---|---|
| `chain_timeout_ms` | 25000 | CLI returns `action:"continue"` — caller immediately re-advances |
| `stall_timeout_ms` | 300000 | Force-kill silent external LLM → `EXECUTOR_STALLED` |
| `timeout_ms` | 600000 | Per-node hard timeout |
| caller handoff | — | New caller uses `list` → `status` → `resume` to continue |

---

## Secrets & ENV

```yaml
vars:
  api_key: "$ENV:OPENAI_API_KEY"
  _secrets: ["api_key"]
```

At `start`: CLI expands `$ENV:*`, collects secret values, auto-redacts them in `events.ndjson` / `audit.log` / `state.json.history` as `***REDACTED***`.

---

## Error Handling

All errors: `{ code, message, retryable, suggestion, location }`.

| Code | Retryable | Action |
|---|---|---|
| `SCHEMA_VIOLATION` | ✅ | Show message, user fixes input, resume |
| `RUN_BUSY` | ✅ | Wait 1s, retry |
| `WORKFLOW_INVALID` | ❌ | Terminal — fix YAML |
| `EXECUTOR_NOT_FOUND` | ❌ | Terminal — install CLI |
| `EXECUTOR_STALLED` | ❌ | Terminal — check external CLI |
| `LOOP_EXCEEDED` | ❌ | Terminal — adjust condition/max |

Full error code table in `SKILL.md`.

---

## Debugging

Each run has full audit trail at `~/.config/agent-workflow/runs/<run_id>/`:

```
state.json      # cursor + history + vars + last_payload + error
workflow.yaml   # snapshot at start
events.ndjson   # structured event stream
audit.log       # human-readable timeline
outputs/        # for results >10KB
```

```bash
agent-workflow status '{"run_id":"wf-...","include_events":true,"event_limit":50}'
agent-workflow view '{"run_id":"wf-..."}'
tail -f ~/.config/agent-workflow/runs/wf-.../events.ndjson | jq .
```

---

## Testing

```bash
python3 tests/agent-workflow/run_tests.py          # all tests
python3 -m unittest discover -s tests/agent-workflow/unit  # unit only
```

---

## Directory Structure

```
skills/agent-workflow/
├── SKILL.md                  # Agent spec (full)
├── README.md                 # Chinese user guide
├── README_EN.md              # English user guide (this file)
├── pyproject.toml
├── tool.py                   # CLI entry
├── schemas/workflow.schema.json
├── examples/                 # Built-in workflow templates
└── lib/                      # Engine implementation
    ├── engine.py store.py parser.py template.py logger.py errors.py
    ├── nodes/                # agent_call / wait_user / loop / sleep
    ├── executors/            # base/caller/mock + registry
    ├── builder/scaffold.py   # create command
    └── view/render.py        # view command: HTML rendering

~/.config/agent-workflow/     # Global storage (cross-project)
├── workflows/                # User workflow definitions
└── runs/                     # Run instances
```

---

## FAQ

**Q: Can it run without a caller?**
A: Yes. Replace all `executor: caller` with spawn executors (e.g. `claude` / `codex`), run `start` from a script/cron — CLI chains through the entire workflow internally.

**Q: IDE restarted mid-workflow?**
A: All state persists to `~/.config/agent-workflow/runs/`. Use `list` to find unfinished runs, `status` for `last_payload`, then `resume` / `advance`.

**Q: How to add my own workflow?**
A: Put YAML in `~/.config/agent-workflow/workflows/<name>.yaml`. `flows '{}'` auto-discovers it.

**Q: How big can workflows get?**
A: Tested with 100 nodes / 50 loop iterations / 15 min runtime. The bottleneck is external LLM CLI speed, not the engine.

---

More details: error code table, agent call conventions, authoring protocol → `SKILL.md`.
