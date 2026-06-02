# agent-workflow cwd 不可控问题：方案分析与最终建议

> 日期：2026-06-02
> 范围：`skills/agent-workflow`（v1.x，全局配置版）
> 起因：`pilot-task-full-cycle` 等 workflow 在不同会话 / 不同项目下产物不一致；根因是子进程 cwd 不受 workflow 控制。

---

## 1. 背景与问题陈述

`agent-workflow` 目前是**全局配置**：

- workflow YAML 存放在 `~/.config/agent-workflow/workflows/`
- 同一份 YAML 被多个项目（`data-governance-metadata` / `DiskMind` / …）复用
- 跨会话 / 跨 IDE 调用时，CLI 自己的 cwd 不一定等于"目标项目根"

**症状**：YAML 里跑的 `claude` / `codex` / 自定义 spawn executor 继承的工作目录是**调用 `agent-workflow` 时的 shell cwd**，而不是 workflow 真正"属于"的那个项目。结果是：

1. 子 LLM 读不到正确的 `CLAUDE.md` / `.cursor/rules` / 项目文件
2. `context_files: ["./README.md"]` 这种相对路径解析到错的目录
3. 同一份 workflow 在不同项目跑出来的产物完全不同，不可复现
4. 事后追溯困难——`state.json` 里没有记录"这次 run 跑在哪个项目根"

---

## 2. 源码事实核查（修正初版判断）

在写方案前，先把 `lib/parser.py` / `lib/executors/base.py` / `lib/executors/registry.py` / `lib/engine.py` / `schemas/workflow.schema.json` 全部读过一遍，澄清几个**会影响选型**的事实：

### 2.1 schema 对 `executors:` 段非常宽松

```json
// schemas/workflow.schema.json:24
"executors": {"type": "object"},
```

没有 `additionalProperties: false`，也没有任何子字段约束。**YAML 里写任何 key 都不会被 L2 schema 拒掉**——包括 `cwd: xxx`。

### 2.2 `SpawnExecutor` 构造函数**已经原生支持 `cwd`**

```python
# lib/executors/base.py:147-184
class SpawnExecutor(BaseExecutor):
    def __init__(
        self,
        name: str,
        *,
        cmd: list[str],
        ...
        env: dict[str, str] | None = None,
        cwd: Path | None = None,        # ← 已有
    ) -> None:
        ...
        self.cwd = cwd
```

```python
# lib/executors/base.py:195
cwd = self.cwd or Path(run_context.get("project_root") or Path.cwd())
...
proc = subprocess.Popen(..., cwd=str(cwd), ...)
```

**关键**：fallback 链是 `self.cwd → run_context.project_root → Path.cwd()`，整条链路完整可用。

### 2.3 `registry.get_executor` **没有把 `spec["cwd"]` 透传给构造函数**

```python
# lib/executors/registry.py:136-146
if kind == "spawn":
    cfg = config or {}
    return SpawnExecutor(
        name=name,
        cmd=spec["cmd"],
        input_mode=spec.get("input_mode", "stdin"),
        output_parser=spec.get("output_parser", "text"),
        stall_timeout_ms=int(spec.get("stall_timeout_ms") or cfg.get("stall_timeout_ms") or 300_000),
        total_timeout_ms=int(spec.get("timeout_ms") or cfg.get("total_timeout_ms") or 600_000),
        env=spec.get("env") or None,
        # ❌ 缺：cwd=spec.get("cwd"),
    )
```

**所以 prompts.txt 初版说"parser 不读 cwd"只对了一半**——真正断链点在 `registry.get_executor`，不是 parser。L2 schema 不会拦截，但 registry 直接丢弃了 `cwd` 字段。

### 2.4 `state["project_root"]` 是"幽灵字段"

`_build_run_context` 和 `status_action` 都会**读** `state["project_root"]`：

```python
# lib/engine.py:213-218
def _build_run_context(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state.get("run_id"),
        "project_root": state.get("project_root"),    # ← 读
        "caller": state.get("caller"),
    }

# lib/engine.py:735
"project_root": state.get("project_root"),  # ← status_action 返回
```

但 `store.create_run` 和 `start_action` **从来不写**：

```python
# lib/store.py:121-134（create_run 初始化 state）
state: dict[str, Any] = {
    "run_id": run_id,
    "workflow_name": ...,
    "workflow_source": ...,
    "caller": caller or "",
    "status": "awaiting_agent",
    "cursor": {...},
    "vars": ...,
    "history": [],
    "last_payload": None,
    "error": None,
    "created_at": ...,
    "updated_at": ...,
    # ❌ 没有 project_root
}
```

```python
# lib/engine.py:515-549（start_action 入口）
def start_action(params: dict[str, Any]) -> dict[str, Any]:
    workflow_raw = params.get("workflow")
    initial_vars = params.get("vars") or {}
    caller = params.get("caller") or ""
    # ❌ 没接 project_root
    ...
```

**结论**：v1 里 `state["project_root"]` 永远是 `None`，所有 spawn 子进程一律 fallback 到 `Path.cwd()`。这就是"产物不定"的根本原因。

### 2.5 SKILL.md 没有暴露 cwd / project_root 入参

`start` 的参数文档（README §10、SKILL.md L170）只列了 `workflow / vars / caller / allow_missing_executors`，**完全没提**这两个字段，所以 caller 也无法主动声明。

---

## 3. 方案全景对比

把 prompts.txt 里的 4 个方案逐一打分，**新增方案 5**（基于 2.4 的发现）和**方案 6 = 根本解（零人工）**：

### 3.0 评估标准（第一性原理）

"根本解决"必须同时满足 4 条标准：

| 标准 | 含义 |
|---|---|
| **零人工** | caller 不需要每次显式传，也不需要 workflow 作者写 cwd |
| **零歧义** | 同一份 workflow 在同一项目跑，永远跑出可复现结果 |
| **可追溯** | run 结束后能看出"这次跑在哪里、读了哪个项目的文件" |
| **可覆盖** | 真要跨项目调用，能显式 override（避免自动检测踩坑时无路可走）|

### 3.1 总表

| # | 方案 | 真的可行 | 改动量 | 零人工 | 零歧义 | 可追溯 | 可覆盖 | 推荐 |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | caller 每次手动 `cd` | ✅ 立即可用 | 0 | ❌ | ❌ | ❌ | ✅ | △ 临时止血 |
| 2 | YAML `executors.cwd: /abs/path` 硬编码 | ❌ registry 不读 cwd | 0 | ✅ | ❌ 路径硬编码 | ❌ | ❌ | ✘ |
| 3 | YAML `vars.project_root` + 模板 | ❌ 双重不通 | 引擎要改 | ❌ | ⚠️ | ⚠️ | ✅ | ✘ |
| 4 | `start` 加 `--project-root` 入参 | ✅ | ~10 行 | ❌ | ✅ | ✅ | ✅ | ★★★★ |
| 5 | = 方案 4 + registry 透传 cwd | ✅ | ~15 行 | ❌ | ✅✅ | ✅✅ | ✅✅ | ★★★★ |
| **6** | **= 方案 5 + CLI 自动检测 project_root** | ✅ | ~40 行 | **✅** | ✅✅ | ✅✅ | ✅✅ | **★★★★★** |

### 3.1 方案 2 / 3 为何"看上去对，实际不行"

prompts.txt 初版判断 "parser 不读 cwd 所以 YAML 写了没用" — **结论对，原因错**：

- ✅ 现象正确：YAML 里 `executors.<name>.cwd: xxx` 写了不生效
- ❌ 原因不在 parser/schema（L2 schema 是宽松对象，根本不校验 executor 内部字段）
- ✅ 真实断链点：**`registry.get_executor` 在构造 `SpawnExecutor` 时没传 `cwd=spec.get("cwd")`**

所以方案 2/3 想活，**必须先做方案 5 的 registry 补丁**——也就是说，方案 2/3 不是"独立可选项"，是方案 5 的子集。

### 3.3 方案 4 vs 方案 5 vs 方案 6

| 维度 | 方案 4 | 方案 5 | 方案 6 |
|---|---|---|---|
| 触发方式 | caller `start` 显式传 | 同 + YAML 可锁特定 executor | 同 + CLI 自动检测 |
| caller 负担 | 每次必须传 | 每次必须传 | **完全不需要传** |
| 跨 IDE 接力 | 接力 caller 也必须知道项目 | 同 4 | 接力 caller 即使在不同 cwd，也能从 state 读到上次的 project_root |
| 老 caller 兼容 | 不传 → 退回 cwd（同今天） | 同 4 | 不传 → 自动检测，**比今天更准** |

**方案 6 = 方案 5 + 自动检测** 是真正的"根本解"——满足全部 4 条标准。

---

## 4. 推荐方案：**方案 6（最终解）**

### 4.0 为什么方案 5 还不够

方案 5 把 cwd 链路打通了，但 caller 必须每次记得显式传 `project_root`。实际使用中：

- IDE Agent 多轮对话切项目时容易漏传
- 跨会话接力（场景 §1.3：会话 A 启动，关掉，会话 B 继续）时，B 不知道 A 的项目根
- 用户**最常见的体验** 还是 "为什么这次又跑歪了"

**根本解必须让 CLI 自己识别 project_root**，让 caller 只在反常场景才手动 override。

### 4.1 project_root 解析优先级（核心算法）

定义一个统一的解析函数 `resolve_project_root()`，按以下优先级返回最终 cwd。**只要走这个统一入口，caller / YAML / 自动检测三层就不会打架**：

```
1. caller 显式传：start params.project_root  ← 最高优先级（人为意图最强）
2. workflow YAML 声明：workflow.project_root（可选字段，新增）
3. 环境变量：AGENT_WORKFLOW_PROJECT_ROOT
4. IDE 工作区：CURSOR_WORKSPACE_LABEL → 解析为路径
                VSCODE_WORKSPACE_FOLDERS → JSON 解析
5. 从当前 cwd 向上找 marker（git repo root 等）：
   - .git/        ← 最权威
   - .agent-workflow/   ← 本工具自留 marker（次优先）
   - CLAUDE.md / AGENTS.md / .cursorrules / .cursor/
   - package.json / pyproject.toml / Cargo.toml / go.mod
6. 都没有 → Path.cwd()（最后兜底，保持今天的行为）
```

**关键设计点**：

- **5 个 marker 之间用"权威性"排序**（git 最高，包管理文件最低），不是"就近"——避免 monorepo 子模块里有 `package.json` 但 `.git` 在更上层时跑歪
- **检测结果落 state 持久化** —— `state.project_root` 一旦写入就锁定，`advance/resume/retry` 永远复用同一个，**不再重新检测**（避免接力 caller 在不同 cwd 时把 run 跑到新地方）
- **决策可审计** —— state 里同时记录 `project_root_source: "caller_explicit" | "workflow_yaml" | "env" | "ide_label" | "marker:.git" | "fallback_cwd"`，事后能查"这次的 cwd 怎么定的"

### 4.2 实施 patch 清单（共 ~40 行）

#### ① 新增 `lib/project_root.py`（~30 行）

```python
"""project_root 解析：caller > YAML > env > IDE > marker > cwd 六级 fallback。"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path

MARKERS_BY_AUTHORITY = [
    ".git",
    ".agent-workflow",
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".cursor",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
]

@dataclass
class ProjectRootDecision:
    path: Path
    source: str  # caller_explicit / workflow_yaml / env / ide_label / marker:.git / fallback_cwd

def _find_upward(start: Path, marker: str) -> Path | None:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / marker).exists():
            return parent
    return None

def resolve_project_root(
    *,
    caller_param: str | None,
    workflow: dict | None,
    env: dict[str, str] | None = None,
) -> ProjectRootDecision:
    env = env if env is not None else os.environ
    cwd = Path.cwd()

    # 1. caller 显式
    if caller_param:
        return ProjectRootDecision(Path(caller_param).expanduser().resolve(), "caller_explicit")

    # 2. workflow YAML
    yaml_root = (workflow or {}).get("project_root")
    if yaml_root:
        return ProjectRootDecision(Path(yaml_root).expanduser().resolve(), "workflow_yaml")

    # 3. env 变量
    if env.get("AGENT_WORKFLOW_PROJECT_ROOT"):
        return ProjectRootDecision(
            Path(env["AGENT_WORKFLOW_PROJECT_ROOT"]).expanduser().resolve(), "env"
        )

    # 4. IDE label
    cursor_label = env.get("CURSOR_WORKSPACE_LABEL")
    if cursor_label:
        # CURSOR_WORKSPACE_LABEL 是 workspace 名字，需要结合 PWD 反推
        pwd = Path(env.get("PWD") or cwd)
        if cursor_label in str(pwd):
            # 在路径里截到 label 那一段
            for parent in [pwd, *pwd.parents]:
                if parent.name == cursor_label:
                    return ProjectRootDecision(parent.resolve(), "ide_label")

    # 5. marker 向上搜索（按权威性顺序）
    for marker in MARKERS_BY_AUTHORITY:
        hit = _find_upward(cwd, marker)
        if hit is not None:
            return ProjectRootDecision(hit, f"marker:{marker}")

    # 6. fallback
    return ProjectRootDecision(cwd.resolve(), "fallback_cwd")
```

#### ② `lib/executors/registry.py` — 透传 cwd（+3 行）

```python
# lib/executors/registry.py:136-146
if kind == "spawn":
    cfg = config or {}
    spec_cwd = spec.get("cwd")
    return SpawnExecutor(
        name=name,
        cmd=spec["cmd"],
        input_mode=spec.get("input_mode", "stdin"),
        output_parser=spec.get("output_parser", "text"),
        stall_timeout_ms=int(spec.get("stall_timeout_ms") or cfg.get("stall_timeout_ms") or 300_000),
        total_timeout_ms=int(spec.get("timeout_ms") or cfg.get("total_timeout_ms") or 600_000),
        env=spec.get("env") or None,
        cwd=Path(spec_cwd).expanduser() if spec_cwd else None,  # ← 新增
    )
```

#### ③ `lib/engine.py::start_action` — 调 resolver（+5 行）

```python
def start_action(params: dict[str, Any]) -> dict[str, Any]:
    workflow_raw = params.get("workflow")
    if workflow_raw is None:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "workflow is required")
    initial_vars = params.get("vars") or {}
    caller = params.get("caller") or ""
    caller_project_root = params.get("project_root")
    allow_missing = bool(params.get("allow_missing_executors", False))

    workflow = load_workflow(workflow_raw)

    from lib.project_root import resolve_project_root
    pr_decision = resolve_project_root(
        caller_param=caller_project_root,
        workflow=workflow,
    )
    ...
    run_id, run_dir = create_run(
        workflow=workflow,
        workflow_source=workflow_raw if isinstance(workflow_raw, str) else None,
        initial_vars=merged_vars,
        caller=caller,
        project_root=str(pr_decision.path),
        project_root_source=pr_decision.source,
    )
```

#### ④ `lib/store.py::create_run` — 把决策写进 state（+5 行）

```python
def create_run(
    *,
    workflow: dict[str, Any],
    workflow_source: str | None,
    initial_vars: dict[str, Any],
    caller: str | None,
    project_root: str | None = None,
    project_root_source: str | None = None,
    runs_root_override: Path | None = None,
) -> tuple[str, Path]:
    ...
    state: dict[str, Any] = {
        "run_id": run_id,
        ...
        "caller": caller or "",
        "project_root": project_root or "",
        "project_root_source": project_root_source or "",
        ...
    }
```

#### ⑤ schema 新增 `workflow.project_root` 字段（+3 行 JSON）

让 workflow 作者可以为特殊 workflow 锁定一个项目（极少数场景）：

```json
"properties": {
  ...
  "project_root": {"type": "string", "minLength": 1,
    "description": "可选；workflow 自声明的项目根，优先级低于 caller 入参"}
}
```

#### ⑥ schema executors 段严格化（可选，+5 行 JSON）

为了让 YAML 层 `cwd` 有形式约束（避免拼写错误成 `cmd: cwd` 之类），可以把 `executors` schema 紧一点：

```json
"executors": {
  "type": "object",
  "additionalProperties": {
    "type": "object",
    "properties": {
      "kind": {"enum": ["spawn", "caller", "mock"]},
      "cmd": {"oneOf": [{"type": "string"}, {"type": "array"}]},
      "args": {"type": "array"},
      "input_mode": {"enum": ["stdin", "arg"]},
      "output_parser": {"enum": ["text", "json"]},
      "stall_timeout_ms": {"type": "integer", "minimum": 100},
      "timeout_ms": {"type": "integer", "minimum": 100},
      "env": {"type": "object"},
      "cwd": {"type": "string", "minLength": 1}
    }
  }
}
```

（⑤⑥ 是衍生加固，**先把 ①②③④ 落下**，运行时就完整打通。）

### 4.3 caller 侧使用（三档体验）

| 用户场景 | caller 怎么做 | CLI 怎么定 cwd |
|---|---|---|
| **99% 默认场景** | `start '{"workflow":"X"}'` | 自动检测：`.git` → 命中项目根，零人工 |
| **跨项目调用** | `start '{"workflow":"X","project_root":"/path/to/other"}'` | 用 caller 传的值（最高优先级） |
| **CI/cron 远程跑** | `AGENT_WORKFLOW_PROJECT_ROOT=/repo start '{"workflow":"X"}'` | 用环境变量 |
| **某 workflow 只允许在某项目跑** | YAML 里写 `project_root: /opt/sandbox` | 用 YAML 值（caller 没传时） |
| **跨会话接力**（核心场景） | 会话 B `resume '{"run_id":"..."}'` 即可 | **state.project_root 锁定，不重新检测** |

**关键体验对比**：

- 今天：caller 必须自己 cd 到对的目录，否则产物错乱（且事后看不出来错在哪）
- 方案 4/5：caller 必须每次显式传 `project_root`（容易漏）
- **方案 6：caller 不传也对**，且 `status` 能看出来 "这次 cwd 取自 `.git` marker / `CURSOR_WORKSPACE_LABEL` / caller 显式"，事后可追责

### 4.4 向后兼容性

| patch | 老 caller / 老 run 行为 |
|---|---|
| ① resolver 模块 | 新文件，老代码不调用就无影响 |
| ② registry cwd 透传 | spec 没 cwd 时传 None，等价于今天 |
| ③ start_action 调 resolver | caller 不传 project_root + workflow 没声明 + 无 env + 无 IDE label → fallback 到 marker / cwd，**比今天更准（今天就是裸 cwd）** |
| ④ state 新增 2 字段 | 只增不改，老 state.json 读出来这俩字段是 None，符合 `_build_run_context` 现有预期 |
| ⑤⑥ schema 微调 | 新字段都 optional，老 YAML 不动 |

**零升级风险**。**老的 caller 不仅不会 break，反而会自动获得比今天更准的 cwd 行为**——这是方案 6 相对方案 4/5 的关键优势。

---

## 5. 收尾建议

### 5.1 必做（让"产物不定"问题根本消失）

- [ ] **patch ① 新增 `lib/project_root.py`**（~30 行，含 6 级 fallback resolver）
- [ ] **patch ② registry 透传 cwd**（~3 行）
- [ ] **patch ③ start_action 调 resolver + 落 state**（~5 行）
- [ ] **patch ④ create_run 接 project_root + project_root_source**（~5 行）
- [ ] SKILL.md 在 `start` 参数表新增 `project_root`（optional）说明
- [ ] README.md §10 同步，加一节 "project_root 解析优先级"

### 5.2 可选加固（不阻塞主线）

- [ ] patch ⑤ workflow.project_root schema 字段
- [ ] patch ⑥ executors 段 schema 严格化（防 cwd 拼写错误）
- [ ] `view` 总览页 footer 显示每个 run 的 `project_root` 和 `project_root_source`（render.py 已经接收 project_root，UI 微调）
- [ ] `list` 增加 `--project-root` filter（"看这个项目跑过哪些 workflow"）
- [ ] `resume` / `advance` / `retry` 显式拒绝带 `project_root`（避免半路改 cwd 导致 history 错乱）

---

## 6. 跨 LLM CLI 适配性分析（claude / codex / opencode / cursor-agent）

`agent-workflow` 实际场景里 spawn 的不只是单一 CLI——`pilot-task-full-cycle.yaml` 用的是 **`tt-claude`**（Claude Code 包装），`cross-llm-pipeline.yaml` 同时用 **claude + codex**，未来还要接 **opencode** 和 **cursor-agent**。方案 6 必须对四家都成立才算"根本解"。

> **特别说明 — Cursor 的两个不同角色**：
>
> | 角色 | 在 agent-workflow 中的位置 | 受方案 6 影响的层 |
> |---|---|---|
> | **Cursor IDE 作为 caller**（我自己跑 `agent-workflow start`） | caller 侧 | §4.1 Layer 4：`CURSOR_WORKSPACE_LABEL` 自动检测 |
> | **cursor-agent CLI 作为 spawn executor**（让 workflow spawn cursor 节点） | executor 侧 | §6 的"四家 CLI 适配"，下文展开 |
>
> 这两个角色互相独立、互不冲突。本节同时给两层结论。

### 6.1 四家 CLI 的"项目根"识别机制对照

| CLI | 项目根来源 | 受 subprocess cwd 影响 | 有 `--cwd` / 等价 flag | 特殊限制 |
|---|---|:---:|:---:|---|
| **claude / tt-claude** | 从 cwd 向上找 `CLAUDE.md` / `.claude/` / git root；project memory 以 git root 为 key | ✅ 完全依赖 | ❌ 无（只能靠 subprocess cwd） | 无 |
| **codex** | 从 cwd 找；可用 `--cd` / `-C` 覆盖；要求 git repo（否则 `--skip-git-repo-check`） | ✅✅ 双通道 | ✅ `--cd <DIR>` / `-C <DIR>` | 非 git → 必须 `--skip-git-repo-check`；trusted directory 机制 |
| **opencode** | 从 cwd 向上找 `AGENTS.md` / `CLAUDE.md`；首个命中即停；命中 git root | ✅ 完全依赖 | ❌ 无 | `permission.external_directory: deny` 可关掉跨边界上行 |
| **cursor-agent** | 以 `--workspace` 为根（或 cwd），从根读 `.cursor/rules/*.mdc` + `.cursorrules`（legacy）+ `AGENTS.md`（含子目录嵌套） | ✅✅ 双通道（同 codex） | ✅ `--workspace <PATH>` | headless 必须配 `-p --force --trust`；订阅生效；`.cursorrules` 是 legacy（已 deprecated），新版以 `.cursor/rules/*.mdc` 为主 |

**关键结论**：四家都把 **subprocess cwd 当作项目根的主要信号**。方案 6 把 `cwd` 设到 project_root，四家都会自动读到正确的项目规则文件（`CLAUDE.md` / `AGENTS.md` / `.cursor/rules`）和 project memory。

### 6.2 四家适配性逐项打分

| 维度 | claude (tt-claude) | codex | opencode | cursor-agent |
|---|:---:|:---:|:---:|:---:|
| 方案 6 的 `cwd=X` 是否生效 | ✅ | ✅ | ✅ | ✅ |
| 是否读到 X 下的项目规则 | ✅ CLAUDE.md | ✅ AGENTS.md + .codex/ | ✅ AGENTS.md/CLAUDE.md | ✅ .cursor/rules/*.mdc + AGENTS.md |
| 是否需要额外 flag | ❌ 无 | ⚠️ 非 git 需 `--skip-git-repo-check` | ❌ 无 | ⚠️ headless 必须 `-p --force --trust` |
| 跨 cwd "越界读"风险 | 低（只往上找到 git root 止）| 低（同上） | 中（默认到 `/`，issue #6479）| 低（以 `--workspace` 为根，子目录嵌套 AGENTS.md 受控）|
| 推荐双通道（同步 `--cwd` flag） | — | ✅ 推荐 `--cd {{cwd}}` | — | ✅ 推荐 `--workspace {{cwd}}` |

### 6.3 codex 的"双通道 cwd"考虑

codex 有两个独立的 cwd 概念：
- **subprocess cwd**（Python `Popen(cwd=...)`，方案 6 控制的就是这个）
- **`--cd` flag**（codex 自己的"working root"，影响 sandbox 边界、relative path 解析、profile 选择）

两者**通常一致**，但有边缘场景会脱钩。**推荐的稳妥策略**：在 `executors.codex.cmd` 里同时显式追加 `--cd` 模板，让 codex 内部 cwd 和外部 cwd 双重对齐。

**实现方式**（基于已有 §4.2 patch ②，registry 透传 cwd 时同步注入到 cmd 模板）：

```yaml
# 用户在 YAML 里这样写
executors:
  codex:
    kind: spawn
    cmd: ["codex", "exec", "--skip-git-repo-check", "--cd", "{{project_root}}"]
    input_mode: stdin
```

但 `{{project_root}}` 在 executor 的 `cmd` 字段里渲染需要新增 1 个能力——**registry 在构造 SpawnExecutor 时对 cmd 数组做一次模板替换**。这是 §4.2 patch ② 的延伸（再 +5 行），让 codex / opencode / claude / 任意 spawn CLI 都能在 cmd flag 里引用 cwd。

#### patch ⑦ registry 渲染 cmd 模板（可选，+5 行）

```python
# lib/executors/registry.py:138
if kind == "spawn":
    cfg = config or {}
    spec_cwd = spec.get("cwd")
    resolved_cwd = Path(spec_cwd).expanduser() if spec_cwd else None

    # 把 cmd 里的 {{cwd}} / {{project_root}} 替换为实际 cwd（如果有）
    cmd_template = spec["cmd"]
    if resolved_cwd:
        cmd_template = [
            arg.replace("{{cwd}}", str(resolved_cwd))
               .replace("{{project_root}}", str(resolved_cwd))
            if isinstance(arg, str) else arg
            for arg in cmd_template
        ]

    return SpawnExecutor(
        name=name,
        cmd=cmd_template,
        ...
        cwd=resolved_cwd,
    )
```

注意**这里 `{{cwd}}` 的渲染是在 registry 层做**，不走 lib/template.py 的 vars 渲染（vars 在 engine 层针对节点的 prompt 字段）。两层互不干扰。

### 6.4 四家 CLI 的最佳 YAML 模板（落地后即用）

```yaml
executors:
  # Claude Code（含 tt-claude 包装）—— 默认行为最干净，零额外 flag
  claude:
    kind: spawn
    cmd: ["claude", "-p", "--dangerously-skip-permissions"]
    # 不需要 cwd 字段（agent-workflow 会从 state.project_root 自动注入）

  tt-claude-sonnet:
    kind: spawn
    cmd: ["tt-claude", "--model", "sonnet", "-p", "--dangerously-skip-permissions"]

  # codex —— 推荐双通道（subprocess cwd + --cd flag）
  codex:
    kind: spawn
    cmd: ["codex", "exec", "--skip-git-repo-check", "--cd", "{{cwd}}"]
    # {{cwd}} 会被 registry 渲染为方案 6 解析出的 project_root

  # opencode —— 默认行为 OK，可选锁定 external_directory
  opencode:
    kind: spawn
    cmd: ["opencode", "run", "--format", "json", "--dangerously-skip-permissions"]
    # 如需禁止上行越界读，在项目根放 opencode.json:
    #   {"permission": {"external_directory": "deny"}}

  # cursor-agent —— headless 必须 -p / --force / --trust，推荐 --workspace 双通道
  cursor-agent:
    kind: spawn
    cmd:
      - "cursor-agent"
      - "-p"                       # 非交互式 print mode
      - "--force"                  # = --yolo，禁止 approval 卡住
      - "--trust"                  # headless 信任 workspace
      - "--workspace"
      - "{{cwd}}"                  # 双通道：subprocess cwd + --workspace
      - "--output-format"
      - "text"                     # 也可用 json / stream-json
    # 模型可用 --model 指定（cursor-agent 自己路由到 OpenAI/Anthropic/Gemini）
```

### 6.5 cursor-agent 的两个易踩坑点

| 现象 | 原因 | 处理 |
|---|---|---|
| `cursor-agent: command not found` | 没装 / 没在 PATH | 让用户先安装 cursor CLI 并 `cursor-agent --help` 验证 |
| 子进程在等审批提示卡死 → `EXECUTOR_STALLED` | 没传 `--force` / `--yolo` | cmd 必加 `-p --force --trust`（headless 必备） |
| MCP server 弹"approve me" 卡死 | 没传 `--approve-mcps` | 视场景加 `--approve-mcps` |
| 订阅 / 模型配额超 → `EXECUTOR_NONZERO_EXIT` | cursor-agent 用同账号 quota | 用 `--model` 切到便宜模型，或回退到 claude/codex |
| 输出不是预期格式 → `NODE_EMPTY_OUTPUT` | 默认 `--output-format text` 可能带前后噪声 | YAML 加 `output_parser: text`，或改 `--output-format json` + `output_parser: json` |

### 6.6 适配性结论

| CLI | 方案 6 适配性 | 需额外配置 |
|---|:---:|---|
| claude / tt-claude | ★★★★★ 完美 | 无 |
| opencode | ★★★★★ 完美 | 无（项目根放 AGENTS.md 即可被识别）|
| codex | ★★★★☆ 完美 + 1 个建议加固 | 推荐 cmd 加 `--cd {{cwd}}` 双通道（patch ⑦）|
| **cursor-agent** | ★★★★☆ 完美 + headless 必备 flag | 推荐 cmd 加 `--workspace {{cwd}}` + `-p --force --trust`（patch ⑦）|

**总结：方案 6 对四家 LLM CLI 全部适配。**
- claude / opencode：零适配代码，落 Phase 1 即用。
- codex / cursor-agent：建议落 patch ⑦（cmd 模板渲染），让 subprocess cwd 和 CLI 自己的 `--cd` / `--workspace` 双通道对齐；不做也能跑，做了更稳。

### 6.7 Cursor 作为 caller 的特殊收益（与 executor 侧无关）

回到 §6 开头那张表里"Cursor IDE 作为 caller"那一行——这是**完全独立的另一个收益**：

| 场景 | 今天 | 方案 6 落地后 |
|---|---|---|
| 用户在 Cursor 里跑 `agent-workflow start ...` | shell cwd 是什么就用什么 | **自动读 `CURSOR_WORKSPACE_LABEL=skillix-hub` → 推断 workspace 路径 → state.project_root_source = "ide_label"** |
| 用户在 Cursor 里切换到另一个 workspace 再跑 | shell cwd 可能还停在老目录 → 跑歪 | `CURSOR_WORKSPACE_LABEL` 变了 → 新 run 自动绑定新 workspace |
| 用户在 Cursor 里看 `status` 某个 run | 看不到这次跑的是哪个项目 | `project_root` + `project_root_source` 都展示出来 |

**这条收益 cursor-agent CLI 也能享受到**——只要它通过 shell 启动子进程，Cursor 注入的 env 自然被继承。

---

## 7. 测试覆盖

### 7.1 项目根解析单元测试（建议）

| 测试用例 | 期望 |
|---|---|
| caller 显式传 `project_root: "/A"` | state.project_root = "/A"，source = "caller_explicit"，子进程 cwd = /A |
| caller 不传，cwd 在 git repo `/B` 内 | source = "marker:.git"，子进程 cwd = /B（git root） |
| caller 不传 + 不在 git repo + 没 marker | source = "fallback_cwd"，行为等价于今天 |
| `CURSOR_WORKSPACE_LABEL=foo` + cwd 在 `/x/foo/bar/` | source = "ide_label"，cwd = /x/foo |
| 老 run（state.json 没 project_root 字段） | status 返回 project_root = ""（不崩） |
| `resume` 一个老 run | 用 state 里锁定的 project_root，不重新检测 |

### 7.2 四家 LLM CLI 集成测试（建议）

| 测试用例 | 期望 |
|---|---|
| project_root = repo_A，executor=tt-claude，prompt="读 CLAUDE.md 第一行" | 输出 = repo_A/CLAUDE.md 首行 |
| project_root = repo_A，executor=opencode，prompt="读 AGENTS.md 第一行" | 输出 = repo_A/AGENTS.md 首行 |
| project_root = repo_A，executor=codex（cmd 含 `--cd {{cwd}}`） | codex `/status` 显示 workspace = repo_A |
| project_root = 非 git 目录，executor=codex（cmd 含 `--skip-git-repo-check`） | 正常跑通 |
| project_root = repo_A，executor=codex（cmd 不含 `--skip-git-repo-check`，且 repo_A 不是 git repo） | `EXECUTOR_NONZERO_EXIT` + stderr 含 `Not inside a trusted directory` |
| project_root = repo_A，executor=cursor-agent（cmd 含 `--workspace {{cwd}}` + `-p --force --trust`），prompt="列出当前 workspace 下的 .cursor/rules/*.mdc" | 列出 repo_A/.cursor/rules/*.mdc |
| project_root = repo_A，executor=cursor-agent（cmd 缺 `--force`） | 大概率 `EXECUTOR_STALLED`（卡在 approval prompt）|
| 同一 run 中先 tt-claude 后 codex 后 cursor-agent，project_root 一致 | 三个 executor 都识别为同一项目（产物落地都到 repo_A/）|
| caller = Cursor IDE 的 Agent，shell cwd 在 `/x/foo/bar/`，`CURSOR_WORKSPACE_LABEL=foo` | state.project_root_source = `"ide_label"`，state.project_root = `/x/foo` |

### 7.3 明确拒绝的方案

| 方案 | 拒绝理由 |
|---|---|
| 1（caller 手动 cd） | 人肉操作不可靠；跨会话/跨 IDE 必失效；事后无法追溯 |
| 2（YAML 硬编码绝对路径） | 与"全局复用 workflow"理念冲突；换台机器即废 |
| 3（YAML vars + 模板） | 方案 6 已经能让 caller / YAML / 自动检测三层协作，不需要再绕模板渲染 |
| 4（只接 start 入参，不做自动检测） | 不满足"零人工"标准；caller 漏传时回到今天的问题 |

---

## 8. 影响面与落地计划

| 维度 | 影响 |
|---|---|
| 用户感知 | **绝大多数 caller 完全不用改**，自动获得稳定 cwd 行为；进阶用户可显式 override |
| 性能 | resolver 最多 1 次磁盘搜索（最多 20 层向上遍历），可忽略 |
| 兼容性 | 完全向后兼容（6 个新字段全部 optional + 自动检测兜底比裸 cwd 更准） |
| 维护成本 | 新增 1 个独立模块 `project_root.py`，可单独测试，单独演进 |
| 文档 | SKILL.md + README §10 + 本设计文档 |

### 落地节奏建议

**Phase 1（解决根本问题 + 三家 CLI 适配，1 个 PR）**：
patch ①②③④ + SKILL.md/README 更新 + §7.1 §7.2 测试用例。**完成后"产物不定"问题彻底消失，claude/tt-claude/opencode 全部受益**。

**Phase 2（codex 加固 + 体验加固，可滚动小 PR）**：
patch ⑤⑥⑦ + view UI 显示 project_root + list filter + codex `--cd {{cwd}}` 双通道模板。Phase 2 落地后 codex 也彻底打通。

### 立即可做的临时止血

在 Phase 1 PR 合入之前，调用方可以用 env 变量临时缓解：

```bash
export AGENT_WORKFLOW_PROJECT_ROOT=/Users/.../data-governance-metadata
agent-workflow start '{"workflow":"pilot-task-full-cycle","vars":{...}}'
```

（前提是 §4.1 §3 `env` 这一级先落地——只需 patch ①③ 两个文件，~10 行就能让这条临时通路通。）
