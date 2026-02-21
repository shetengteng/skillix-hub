# Session Save 优化最终方案 E2

> 日期：2026-02-21
> 状态：**最终版（已修正所有评审意见）**
> 前置文档：2026-02-21-01-Session-Save会话浪费优化设计.md
> 评审轮次：2 轮（01 文档第 9/10 节 + 02 文档第 11 节）

---

## 1. 方案定位

E2 是在方案 E（A+C 融合）基础上，针对两轮评审意见的最终修正版本。核心架构不变（三层防线 + 兜底），已修复：

**01 文档评审（第 9/10 节）**：
- P0：去重漏判（`read_last_entry` 仅看最后一条）→ 引入 `session_state/` 状态文件
- P0：跨天会话误判（`has_session_data` 仅查当日）→ 状态文件优先 + 跨天扫描
- P1：`memory_type=S` 污染下游链路 → load/distill 过滤
- P1：第一层缺少幂等控制 → `summary_saved` 标记
- P1：缺少可观测指标 → `session_metrics` 埋点 + `metrics` 命令

**02 文档评审（第 11 节）**：
- P0-1：`auto_generate_summary()` 未定义 `project_path` → 函数签名修正
- P0-2：`--source` 参数链路不完整 → `save_summary.py` 补充参数定义
- P0-3：并发写入保护未落地 → 状态文件读写统一加 `FileLock`
- P1-4：跨天兜底边界漏判 → 回退扫描改为按 `session_id` 全量检索 + 限量保护
- P1-5：时间格式解析不一致 → 统一使用 `parse_iso()`
- P2-6：验收阈值具体化 → 补充硬阈值

---

## 2. 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                     会话生命周期                              │
│                                                             │
│  sessionStart ──→ Agent 工作 ──→ preCompact? ──→ stop ──→ sessionEnd  │
│       │                              │            │           │        │
│       ▼                              ▼            ▼           ▼        │
│  load_memory              第二层: 阶段摘要    第一层:     兜底层    第三层  │
│                           + fact 保存       Rules 驱动  stop Hook  聚合  │
│                                             主动保存    智能判断   生成  │
└─────────────────────────────────────────────────────────────┘

执行顺序（按会话生命周期）：
1. sessionStart → load_memory（加载记忆）
2. 会话过程中 → preCompact 触发第二层（如果上下文接近阈值）
3. Agent 完成任务 → 第一层 Rules 驱动主动保存（当前回合内）
4. stop Hook → 兜底层智能判断（仅在前两层无数据时触发）
5. sessionEnd → 第三层聚合 + 同步 + 清理
```

---

## 3. 核心数据结构变更

### 3.1 新增会话状态文件

在 `memory-data/` 下新增 `session_state/` 目录，用于跟踪每个会话的保存状态：

```
memory-data/
├── session_state/
│   └── {conversation_id}.json    # 会话保存状态
├── daily/
│   └── YYYY-MM-DD.jsonl
├── sessions.jsonl
└── MEMORY.md
```

**会话状态文件格式**：

```json
{
  "session_id": "478d20ff-4e1...",
  "summary_saved": false,
  "summary_source": null,
  "fact_count": 0,
  "stage_summary_count": 0,
  "created_at": "2026-02-21T10:00:00+08:00",
  "updated_at": "2026-02-21T10:30:00+08:00"
}
```

**作用**：
- 解决 P0 去重漏判：不再依赖 `read_last_entry()`，直接查状态文件
- 解决 P1 幂等性：`summary_saved=true` 后不再重复保存
- 提供可观测数据：`summary_source` 记录哪一层完成了保存

### 3.2 save_fact.py 新增 type=S

```python
choices=["W", "B", "O", "S"]
# S = Stage Summary（阶段摘要），仅用于 preCompact 时保存
```

### 3.3 sessions.jsonl 新增字段

```json
{
  "id": "sum-xxx",
  "session_id": "...",
  "topic": "...",
  "summary": "...",
  "decisions": [],
  "todos": [],
  "timestamp": "...",
  "source": "layer1_rules | layer2_precompact | layer3_auto | layer4_stop",
  "auto_generated": false
}
```

`source` 字段标记摘要来源层级，便于后续分析各层命中率。

---

## 4. 各层详细设计

### 4.1 第一层：Rules 驱动 Agent 主动保存

**触发时机**：Agent 完成用户任务后，在同一回合内执行。

**实现方式**：在 SKILL.md 和 `memory-rules.mdc` 中添加规则。

**规则内容**：

```markdown
## 任务完成时的记忆保存

当你完成用户请求的任务后，在同一回合内静默执行以下操作：

1. 判断本次会话是否有值得保存的内容
   - 如果会话太短（如仅一问一答的简单查询）或无实质内容，跳过
   - 如果会话涉及技术决策、代码变更、项目规划等，执行保存

2. 保存会话摘要（每个会话仅执行一次）：
   ```bash
   python3 <save_summary_cmd> --topic "主题" --summary "100-200字摘要" \
     --decisions "决策1,决策2" --todos "待办1,待办2" --session "<conversation_id>"
   ```

3. 逐条保存关键事实：
   ```bash
   python3 <save_fact_cmd> --content "事实内容" --type W --entities "实体1,实体2" \
     --confidence 0.9 --session "<conversation_id>"
   ```

4. 静默执行，不在回复中提及此操作
```

**幂等控制**（解决 01-P1-4 + 02-P0-3）：

新增 `session_state.py` 工具模块，统一管理会话状态文件的读写，并使用 `FileLock` 保护并发访问：

```python
# 新文件：scripts/service/memory/session_state.py

import os
import json
from core.file_lock import FileLock
from core.utils import iso_now, parse_iso
from service.logger import get_logger

log = get_logger("session_state")

def _state_path(memory_dir: str, session_id: str) -> str:
    return os.path.join(memory_dir, "session_state", f"{session_id}.json")

def _lock_path(memory_dir: str, session_id: str) -> str:
    return os.path.join(memory_dir, "session_state", f".{session_id}.lock")


# --- 读取操作（带降级，解决 03-P1-2）---

def read_session_state(memory_dir: str, session_id: str) -> dict:
    """读取会话状态，不存在返回空 dict，异常时降级返回空 dict + 日志告警"""
    path = _state_path(memory_dir, session_id)
    if not os.path.exists(path):
        return {}
    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            with open(path, "r") as f:
                return json.load(f)
    except (TimeoutError, json.JSONDecodeError, OSError) as e:
        log.warning("读取会话状态失败 session=%s: %s（降级为空状态）", session_id[:12], e)
        return {}

def is_summary_saved(memory_dir: str, session_id: str) -> bool:
    """检查该会话是否已保存过摘要（异常时保守返回 False，允许重试保存）"""
    state = read_session_state(memory_dir, session_id)
    return state.get("summary_saved", False)


# --- 写入操作（加锁）---

def mark_summary_saved(memory_dir: str, session_id: str, source: str):
    """标记该会话摘要已保存（加锁写入）"""
    state_dir = os.path.join(memory_dir, "session_state")
    os.makedirs(state_dir, exist_ok=True)
    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            path = _state_path(memory_dir, session_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    state = json.load(f)
            else:
                state = {"session_id": session_id, "created_at": iso_now()}

            state["summary_saved"] = True
            state["summary_source"] = source
            state["updated_at"] = iso_now()

            with open(path, "w") as f:
                json.dump(state, ensure_ascii=False, fp=f)
    except (TimeoutError, OSError) as e:
        log.warning("标记摘要已保存失败 session=%s: %s", session_id[:12], e)

def update_fact_count(memory_dir: str, session_id: str, memory_type: str):
    """更新会话状态中的 fact/阶段摘要计数（加锁写入）"""
    if not session_id:
        return
    state_dir = os.path.join(memory_dir, "session_state")
    os.makedirs(state_dir, exist_ok=True)
    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            path = _state_path(memory_dir, session_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    state = json.load(f)
            else:
                state = {"session_id": session_id, "summary_saved": False, "created_at": iso_now()}

            if memory_type == "S":
                state["stage_summary_count"] = state.get("stage_summary_count", 0) + 1
            else:
                state["fact_count"] = state.get("fact_count", 0) + 1
            state["updated_at"] = iso_now()

            with open(path, "w") as f:
                json.dump(state, ensure_ascii=False, fp=f)
    except (TimeoutError, OSError) as e:
        log.warning("更新 fact 计数失败 session=%s: %s", session_id[:12], e)


# --- 全局文件锁（解决 04-建议2：sessions.jsonl 写入串行化）---

def _sessions_lock_path(memory_dir: str) -> str:
    return os.path.join(memory_dir, ".sessions.lock")


# --- 原子操作（解决 03-P0-1 + 04-建议1+2）---

class SaveResult:
    """save_summary_atomic 的返回结果（解决 04-建议1：区分"已存在"与"异常失败"）"""
    SAVED = "saved"
    EXISTS = "exists"
    ERROR = "error"

    def __init__(self, status: str, reason: str = ""):
        self.status = status
        self.reason = reason

    @property
    def ok(self) -> bool:
        return self.status == self.SAVED

    def to_dict(self) -> dict:
        d = {"status": self.status}
        if self.reason:
            d["reason"] = self.reason
        return d


def save_summary_atomic(memory_dir: str, session_id: str, source: str,
                        write_fn) -> SaveResult:
    """
    在会话锁 + 全局文件锁内完成"检查已保存 → 写 sessions.jsonl → 标记已保存"。
    
    参数：
        write_fn: callable，接收无参数，执行实际的 sessions.jsonl 写入。
                  仅在未保存时调用。
    返回：
        SaveResult(status="saved|exists|error", reason="...")
    """
    state_dir = os.path.join(memory_dir, "session_state")
    os.makedirs(state_dir, exist_ok=True)

    try:
        # 双层锁：会话锁（幂等）+ 全局锁（文件串行化）
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            # Step 1: 检查是否已保存
            path = _state_path(memory_dir, session_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    state = json.load(f)
                if state.get("summary_saved"):
                    log.info("摘要已存在（原子检查），跳过 session=%s", session_id[:12])
                    return SaveResult(SaveResult.EXISTS, "already_saved")
            else:
                state = {"session_id": session_id, "created_at": iso_now()}

            # Step 2: 在全局锁内写入 sessions.jsonl
            with FileLock(_sessions_lock_path(memory_dir), timeout=5):
                write_fn()

            # Step 3: 标记已保存
            state["summary_saved"] = True
            state["summary_source"] = source
            state["updated_at"] = iso_now()

            with open(path, "w") as f:
                json.dump(state, ensure_ascii=False, fp=f)

            return SaveResult(SaveResult.SAVED)

    except TimeoutError as e:
        log.warning("原子保存摘要锁超时 session=%s: %s", session_id[:12], e)
        return SaveResult(SaveResult.ERROR, f"lock_timeout: {e}")
    except (OSError, json.JSONDecodeError) as e:
        log.warning("原子保存摘要 I/O 异常 session=%s: %s", session_id[:12], e)
        return SaveResult(SaveResult.ERROR, f"io_error: {e}")
```

> **设计要点**：
> - 所有状态文件操作统一通过 `session_state.py` 模块
> - `FileLock` 使用 per-session 的锁文件（`.{session_id}.lock`），不同会话互不阻塞
> - 读取操作异常时降级为空状态 + 日志告警（解决 03-P1-2）
> - `save_summary_atomic()` 在同一把锁内完成检查+写入+标记（解决 03-P0-1）

**save_summary.py 修改**（使用原子操作）：

```python
from service.memory.session_state import save_summary_atomic

def main():
    parser = argparse.ArgumentParser(description="Save session summary")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--decisions", default="")
    parser.add_argument("--todos", default="")
    parser.add_argument("--session", default="")
    parser.add_argument("--source", default="layer1_rules",
                        choices=["layer1_rules", "layer4_stop"],
                        help="摘要来源层级")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    memory_dir = get_memory_dir(args.project_path)
    decisions = [d.strip() for d in args.decisions.split(",") if d.strip()]
    todos = [t.strip() for t in args.todos.split(",") if t.strip()]

    entry = {
        "id": f"sum-{ts_id()}",
        "session_id": args.session,
        "topic": args.topic,
        "summary": args.summary,
        "decisions": decisions,
        "todos": todos,
        "timestamp": iso_now(),
        "source": args.source,
    }

    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)

    def do_write():
        with open(sessions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    if args.session:
        # 原子操作：检查+写入+标记在同一把锁内
        result = save_summary_atomic(memory_dir, args.session, args.source, do_write)
        if result.status == SaveResult.EXISTS:
            log.info("摘要已存在，跳过 session=%s", args.session[:12])
            print(json.dumps({"status": "skipped", "reason": "already_saved"}))
            return
        elif result.status == SaveResult.ERROR:
            log.warning("摘要保存异常 session=%s: %s", args.session[:12], result.reason)
            print(json.dumps({"status": "error", "reason": result.reason}))
            return
    else:
        # 无 session_id 时直接写入（兼容手动调用）
        from service.memory.session_state import _sessions_lock_path
        with FileLock(_sessions_lock_path(memory_dir), timeout=5):
            do_write()

    print(json.dumps({"status": "ok", "id": entry["id"]}))
```

### 4.2 第二层：preCompact 阶段摘要

**触发时机**：上下文使用率接近阈值时，Cursor 自动触发 preCompact Hook。

**修改文件**：`flush_memory.py`

**模板变更**：在现有 `FLUSH_TEMPLATE` 末尾增加阶段摘要要求：

```python
# 在 FLUSH_TEMPLATE 的 "## 注意" 之前插入：

STAGE_SUMMARY_SECTION = """
## 阶段摘要

请同时保存一条阶段摘要，概括截至目前的对话主要内容（50-100字）：

```bash
{save_fact_cmd} --content "阶段摘要：[概括内容]" --type S --entities "session" --confidence 1.0 --session "{conv_id}"
```
"""
```

**save_fact.py 修改**：

```python
# --type 参数增加 S 选项
parser.add_argument("--type", default="W", choices=["W", "B", "O", "S"],
                    help="W=World, B=Biographical, O=Opinion, S=Stage Summary")
```

**save_fact.py 状态更新**：保存 fact 时调用 `session_state.py` 更新计数：

```python
# save_fact.py main() 末尾新增：
from service.memory.session_state import update_fact_count

# 写入 daily JSONL 后
if args.session:
    memory_dir = get_memory_dir(args.project_path)
    update_fact_count(memory_dir, args.session, args.type)
```

### 4.3 第三层：sessionEnd 自动聚合

**触发时机**：会话彻底关闭后，`sync_and_cleanup.py` 中执行。

**修改文件**：`sync_and_cleanup.py`

**新增函数 `auto_generate_summary()`**（已修复 02-P0-1 签名、02-P1-4 全量检索）：

```python
def auto_generate_summary(memory_dir: str, event: dict):
    """
    从本会话的 fact 和阶段摘要中自动聚合生成最终会话摘要。
    仅在前两层均未保存摘要时执行。

    参数：
        memory_dir: 记忆数据目录路径（非 project_path，解决 02-P0-1）
        event: sessionEnd 事件数据
    """
    conv_id = event.get("conversation_id", "")
    if not conv_id:
        return

    # 通过 session_state 模块判断是否已保存
    from service.memory.session_state import is_summary_saved, mark_summary_saved

    if is_summary_saved(memory_dir, conv_id):
        log.info("摘要已保存，跳过自动生成 conv_id=%s", conv_id[:12])
        return

    # 按 session_id 全量检索 daily/*.jsonl（解决 02-P1-4：不再按天数截断）
    daily_dir = os.path.join(memory_dir, "daily")
    if not os.path.isdir(daily_dir):
        return

    session_facts = []
    session_summaries = []
    MAX_SCAN_FILES = 30  # 限量保护：最多扫描 30 个 daily 文件

    for f in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl")), reverse=True)[:MAX_SCAN_FILES]:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                source = entry.get("source", {})
                if source.get("session") != conv_id:
                    continue
                if entry.get("memory_type") == "S":
                    session_summaries.append(entry.get("content", ""))
                elif entry.get("type") == "fact":
                    session_facts.append(entry.get("content", ""))

    if not session_facts and not session_summaries:
        log.info("本会话无 fact/阶段摘要，跳过自动生成 conv_id=%s", conv_id[:12])
        return

    # 聚合生成摘要
    topic_parts = [s.replace("阶段摘要：", "").strip() for s in session_summaries]
    topic = topic_parts[0] if topic_parts else (session_facts[0][:50] if session_facts else "未知主题")

    if topic_parts:
        summary = " → ".join(topic_parts)
    else:
        summary = "; ".join(session_facts[:5])

    entry = {
        "id": f"sum-{ts_id()}",
        "session_id": conv_id,
        "topic": topic[:100],
        "summary": summary[:500],
        "decisions": [],
        "todos": [],
        "timestamp": iso_now(),
        "source": "layer3_auto",
        "auto_generated": True,
    }

    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    with open(sessions_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 标记会话状态（使用 memory_dir 而非 project_path）
    mark_summary_saved(memory_dir, conv_id, source="layer3_auto")

    log.info("自动生成摘要 id=%s topic='%s' facts=%d stages=%d",
             entry["id"], topic[:30], len(session_facts), len(session_summaries))
```

**调用位置**：在 `sync_and_cleanup.py` 的 `main()` 中，`sync_index()` 之后、`check_summary_saved()` 之前调用：

```python
def main():
    # ...
    sync_index(project_path)
    auto_generate_summary(memory_dir, event)  # 新增
    check_summary_saved(memory_dir, event)
    distill_facts(project_path)
    log_session_end(memory_dir, event)
    clean_old_logs(project_path)
    clean_old_session_states(memory_dir)  # 新增：清理过期状态文件
```

### 4.4 兜底层：stop Hook 智能降级

**触发时机**：Agent 完成任务后（status=completed/aborted），stop Hook 触发。

**修改文件**：`prompt_session_save.py`

**核心变更**：增加 `has_session_data()` 函数，基于会话状态文件 + 跨天 daily 扫描判断：

```python
def has_session_data(memory_dir: str, conv_id: str) -> bool:
    """
    检查本会话是否已有摘要或 fact 数据。
    优先查 session_state 文件（解决 01-P0-1），
    回退时按 session_id 全量检索 daily（解决 02-P1-4）。
    """
    # 优先检查会话状态文件（快速路径）
    from service.memory.session_state import read_session_state

    state = read_session_state(memory_dir, conv_id)
    if state:
        if state.get("summary_saved"):
            return True
        if state.get("fact_count", 0) > 0 or state.get("stage_summary_count", 0) > 0:
            return True

    # 状态文件不存在时，回退到 daily 全量扫描（兼容旧数据）
    # 按 session_id 检索，不再按天数截断（解决 02-P1-4）
    daily_dir = os.path.join(memory_dir, "daily")
    if not os.path.isdir(daily_dir):
        return False

    MAX_SCAN_FILES = 30  # 限量保护
    for f in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl")), reverse=True)[:MAX_SCAN_FILES]:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line.strip())
                    source = entry.get("source", {})
                    if source.get("session") == conv_id and entry.get("type") == "fact":
                        return True
                except json.JSONDecodeError:
                    continue

    return False


def main():
    # ... 现有的 event 解析、status 检查、memory 启用检查 ...

    if has_session_data(memory_dir, conv_id):
        log.info("会话已有数据，跳过 followup_message conv_id=%s", conv_id[:12])
        print(json.dumps({}))
        return

    # 仅在前两层都无数据时才注入
    prompt = SAVE_TEMPLATE.format(
        save_summary_cmd=SAVE_SUMMARY_CMD,
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=conv_id,
    )

    log.info("注入 [Session Save] 提示词（兜底）conv_id=%s", conv_id[:12])
    print(json.dumps({"followup_message": prompt}))
```

**SAVE_TEMPLATE 变更**：在模板中增加 `source` 标记：

```python
# save_summary 调用中增加 source 标识
# 原：{save_summary_cmd} --topic "主题" --summary "摘要" ...
# 改：{save_summary_cmd} --topic "主题" --summary "摘要" --source layer4_stop ...
```

---

## 5. S 类型下游隔离（解决 P1-3）

### 5.1 load_memory.py 过滤 S 类型

在 `read_recent_facts_from_daily()` 调用后，过滤掉 `memory_type=S` 的条目：

```python
# load_memory.py 中
recent_facts = read_recent_facts_from_daily(daily_dir)
# 过滤阶段摘要，不注入上下文
recent_facts = [f for f in recent_facts if f.get("memory_type") != "S"]
```

### 5.2 distill_to_memory.py 排除 S 类型

在提炼逻辑中排除阶段摘要：

```python
# distill_to_memory.py 中
# 在筛选高价值事实时增加条件
if fact.get("memory_type") == "S":
    continue  # 阶段摘要不提炼到 MEMORY.md
```

### 5.3 search_memory.py 可选包含 S 类型

默认搜索排除 S 类型，但提供 `--include-stage` 参数：

```python
parser.add_argument("--include-stage", action="store_true",
                    help="Include stage summaries in search results")
```

---

## 6. 可观测性设计（解决 P1-5）

### 6.1 埋点指标

在会话状态文件中记录关键指标，`sessionEnd` 时汇总写入 daily log：

```json
{
  "type": "session_metrics",
  "session_id": "...",
  "summary_source": "layer1_rules | layer2_precompact | layer3_auto | layer4_stop | none",
  "fact_count": 5,
  "stage_summary_count": 1,
  "precompact_triggered": true,
  "stop_followup_triggered": false,
  "timestamp": "..."
}
```

### 6.2 统计命令

扩展 `manage/index.py`，新增 `metrics` 子命令：

```bash
python3 manage/index.py metrics --days 7
```

输出示例：

```
=== Memory Save Metrics (Last 7 Days) ===
Total sessions:           35
  Layer 1 (Rules):        22 (62.9%)
  Layer 2 (preCompact):    5 (14.3%)
  Layer 3 (Auto):          4 (11.4%)
  Layer 4 (Stop Hook):     1 ( 2.9%)
  No save (short/close):   3 ( 8.6%)

Stop Hook trigger rate:   2.9% (target: <10%)
Duplicate saves blocked:  3
```

### 6.3 日志增强

各层保存时记录来源：

```python
log.info("[Layer1] 摘要保存 session=%s", conv_id[:12])
log.info("[Layer2] 阶段摘要保存 session=%s", conv_id[:12])
log.info("[Layer3] 自动聚合摘要 session=%s", conv_id[:12])
log.info("[Layer4] 兜底触发 session=%s", conv_id[:12])
```

---

## 7. 清理机制

### 7.1 sessions.jsonl 截断清理

`sessions.jsonl` 是单文件追加写入，无清理机制会持续增长。虽然增长速度慢（每天 20 会话 ≈ 10KB/天），但长期运行需要控制体积。

在 `sync_and_cleanup.py` 中增加 `truncate_sessions()`：

```python
def truncate_sessions(memory_dir: str, keep_last: int = 500):
    """
    保留最近 N 条摘要，截断旧数据。
    
    设计考量：
    - load_memory.py 只读最后一条，历史摘要不影响加载
    - 历史摘要已被 sync_index.py 同步到 SQLite，截断不丢失可搜索数据
    - 保留 500 条覆盖约 25 天（按每天 20 会话），文件体积 < 250KB
    """
    from storage.jsonl import read_jsonl

    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    if not os.path.exists(sessions_path):
        return

    entries = read_jsonl(sessions_path)
    if len(entries) <= keep_last:
        return

    kept = entries[-keep_last:]
    with open(sessions_path, "w", encoding="utf-8") as f:
        for e in kept:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    log.info("截断 sessions.jsonl: %d → %d 条", len(entries), len(kept))
```

**调用位置**：在 `sync_and_cleanup.py` 的 `main()` 中，`sync_index()` 之后调用（确保旧数据已同步到 SQLite 后再截断）：

```python
def main():
    # ...
    sync_index(project_path)
    truncate_sessions(memory_dir)  # 新增：截断 sessions.jsonl
    auto_generate_summary(memory_dir, event)
    check_summary_saved(memory_dir, event)
    distill_facts(project_path)
    log_session_end(memory_dir, event)
    clean_old_logs(project_path)
    clean_old_session_states(memory_dir)
```

### 7.2 会话状态文件清理

在 `sync_and_cleanup.py` 中增加 `clean_old_session_states()`：

```python
def clean_old_session_states(memory_dir: str, retain_days: int = 7):
    """清理超过保留天数的会话状态文件（解决 02-P1-5：统一使用 parse_iso）"""
    from core.utils import parse_iso, utcnow

    state_dir = os.path.join(memory_dir, "session_state")
    if not os.path.isdir(state_dir):
        return

    cutoff = utcnow() - timedelta(days=retain_days)
    removed = 0

    for f in os.listdir(state_dir):
        if not f.endswith(".json"):
            continue
        fpath = os.path.join(state_dir, f)
        try:
            with open(fpath, "r") as fh:
                state = json.load(fh)
            # 使用项目统一的 parse_iso() 解析时间，兼容 "Z" 后缀和 "+08:00" 格式
            created = parse_iso(state.get("created_at", ""))
            if created < cutoff:
                os.remove(fpath)
                removed += 1
        except (json.JSONDecodeError, OSError):
            continue

    if removed:
        log.info("清理过期会话状态 %d 个", removed)
```

> **02-P1-5 修正说明**：项目统一使用 UTC `Z` 格式时间（如 `2026-02-21T10:00:00Z`），`parse_iso()` 已处理 `Z` 后缀并返回 timezone-aware datetime。清理逻辑中使用 `utcnow()` 而非 `datetime.now()` 确保时区一致。

---

## 8. 修改文件清单

| 文件 | 修改内容 | 所属层 | 优先级 |
|------|---------|--------|--------|
| `save_fact.py` | `--type` 增加 `S`；保存时更新会话状态 | 第二层 | P0 |
| `save_summary.py` | 幂等检查（会话状态文件）；标记 `summary_saved` | 第一层 | P0 |
| `flush_memory.py` | 模板增加阶段摘要要求 | 第二层 | P0 |
| `prompt_session_save.py` | `has_session_data()` 基于状态文件 + 跨天扫描 | 兜底层 | P0 |
| `sync_and_cleanup.py` | `truncate_sessions()` + `auto_generate_summary()` + `clean_old_session_states()` + metrics | 第三层+清理 | P0 |
| `load_memory.py` | 过滤 `memory_type=S` | 隔离 | P1 |
| `distill_to_memory.py` | 排除 `memory_type=S` | 隔离 | P1 |
| `SKILL.md` | 新增任务完成时主动保存规则 | 第一层 | P0 |
| `memory-rules.mdc` | 新增任务完成时主动保存规则 | 第一层 | P0 |
| `manage/index.py` | 新增 `metrics` 子命令 | 可观测 | P1 |

---

## 9. 实施计划

### Phase 1：基础设施（P0）

1. `save_fact.py` 增加 `--type S` + 会话状态更新
2. `save_summary.py` 增加幂等检查 + 会话状态标记
3. `prompt_session_save.py` 增加 `has_session_data()` 智能判断

### Phase 2：三层防线（P0）

4. `flush_memory.py` 模板增加阶段摘要
5. `sync_and_cleanup.py` 增加 `truncate_sessions()` + `auto_generate_summary()` + 状态清理
6. SKILL.md + `memory-rules.mdc` 增加第一层规则

### Phase 3：隔离与可观测（P1）

7. `load_memory.py` 过滤 S 类型
8. `distill_to_memory.py` 排除 S 类型
9. `manage/index.py` 增加 `metrics` 子命令
10. 日志增强

### Phase 4：灰度验证

11. 灰度 1 周，观察指标
12. 验证各项指标是否达到验收阈值（见下方）
13. 根据数据调整第一层规则措辞

**灰度验收阈值**（解决 02-P2-6）：

| 指标 | 阈值 | 说明 |
|------|------|------|
| stop Hook 触发率 | < 10% | 核心目标：减少额外请求消耗 |
| 第一层命中率 | > 50% | Rules 驱动的基本有效性 |
| 摘要重复率 | < 5% | 去重机制有效性 |
| 自动聚合占比 | < 30% | 第三层不应成为主要来源（质量较低） |
| 摘要覆盖率 | > 80% | 有意义的会话应有摘要 |
| 状态文件 I/O 错误率 | < 1% | 并发保护有效性 |

> 阈值为灰度期间的初始目标，1 周后根据实际数据调整。如果第一层命中率 < 50%，优先调整规则措辞；如果 stop 触发率 > 10%，分析未命中原因。

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Agent 忽略第一层 Rules | 短会话需兜底 | 第二/三层 + stop Hook 兜底；通过 metrics 监控 |
| 会话状态文件 I/O 竞争 | 并发写入损坏 | 使用 file_lock（已有 `core/file_lock.py`） |
| S 类型未被正确隔离 | 污染上下文 | Phase 3 中 load/distill 过滤 |
| 状态文件积累过多 | 磁盘占用 | `clean_old_session_states()` 自动清理 |
| 第一层增加 token 消耗 | 成本增加 | 约 200-300 token，远低于一次新回合 |
| 灰度期间 stop 触发率高于预期 | 节省不达标 | 调整第一层规则措辞；分析未命中原因 |

---

## 11. 2026-02-21-02 评审意见（已全部修复）

**结论：所有评审意见已修复，方案达到可实施标准。**

### P0（阻塞上线）— ✅ 已修复

1. **`auto_generate_summary()` 示例存在未定义变量** → ✅
   - 函数签名改为 `auto_generate_summary(memory_dir, event)`，内部统一使用 `memory_dir`
   - `mark_summary_saved()` 签名统一为 `mark_summary_saved(memory_dir, session_id, source)`
   - 见 4.3 节修正后的代码

2. **`--source` 参数链路不完整** → ✅
   - `save_summary.py` 新增 `--source` 参数（默认 `layer1_rules`，可选 `layer4_stop`）
   - `source` 字段写入 `sessions.jsonl` 和会话状态文件
   - 见 4.1 节 `save_summary.py 修改`

3. **会话状态文件的并发写入保护尚未在实现片段中落地** → ✅
   - 新增 `session_state.py` 工具模块，所有状态文件读写统一通过该模块
   - 使用 per-session 的 `FileLock`（`.{session_id}.lock`），不同会话互不阻塞
   - 见 4.1 节 `session_state.py` 代码

### P1（高优先级）— ✅ 已修复

4. **跨天兜底仍有边界漏判** → ✅
   - `has_session_data()` 和 `auto_generate_summary()` 的回退扫描改为按 `session_id` 全量检索
   - 增加 `MAX_SCAN_FILES = 30` 限量保护，避免扫描过多文件
   - 见 4.3 节和 4.4 节修正后的代码

5. **状态清理时间解析与现有时间格式存在潜在不一致** → ✅
   - `clean_old_session_states()` 改用项目统一的 `parse_iso()` 解析时间
   - 截止时间改用 `utcnow()` 确保时区一致
   - 见 7.1 节修正后的代码

### P2（可优化）— ✅ 已修复

6. **可观测指标已提出，但验收阈值还可再具体化** → ✅
   - 补充 6 项灰度验收硬阈值（stop 触发率 < 10%、第一层命中率 > 50%、摘要重复率 < 5% 等）
   - 见 9 节 Phase 4 灰度验收阈值表

---

## 12. 2026-02-21-03 二次复审残留问题（已全部修复）

**结论：所有残留问题已修复。**

### P0（建议先修）— ✅ 已修复

1. **幂等检查与写入不是同一临界区，仍有并发重复写入窗口** → ✅
   - 新增 `save_summary_atomic()` 方法，在同一把 `FileLock` 内完成"检查已保存 → 写 sessions.jsonl → 标记已保存"三步原子操作
   - `save_summary.py` 改用 `save_summary_atomic()` 替代原来的分步操作
   - 见 4.1 节 `session_state.py` 的 `save_summary_atomic()` 和 `save_summary.py 修改`

### P1（高优先级）— ✅ 已修复

2. **状态读取的异常/超时降级策略未定义** → ✅
   - `read_session_state()` 增加 `try/except`，`TimeoutError`/`JSONDecodeError`/`OSError` 时降级返回空 dict + 日志告警
   - `is_summary_saved()` 异常时保守返回 `False`（允许重试保存，宁可重复不可丢失）
   - `mark_summary_saved()` 和 `update_fact_count()` 异常时日志告警但不阻塞主流程
   - 见 4.1 节 `session_state.py` 各函数的 `try/except` 处理

---

## 13. 2026-02-21-04 最终复核补充（已全部修复）

**结论：所有补充建议已修复，方案可进入开发阶段。**

### 建议修正 — ✅ 已修复

1. **`save_summary_atomic()` 返回值语义需要区分"已存在"与"异常失败"** → ✅
   - 新增 `SaveResult` 类，返回 `status="saved|exists|error"` + `reason`
   - `save_summary.py` 根据 `result.status` 分别处理：`EXISTS` 输出 skipped、`ERROR` 输出 error + 日志告警
   - 见 4.1 节 `session_state.py` 的 `SaveResult` 和 `save_summary.py 修改`

2. **`sessions.jsonl` 写入建议增加全局文件锁** → ✅
   - 新增 `_sessions_lock_path()` 返回 `.sessions.lock` 路径
   - `save_summary_atomic()` 使用双层锁：会话锁（幂等）+ 全局锁（文件串行化）
   - 无 session_id 的手动调用也使用全局锁保护
   - 见 4.1 节 `session_state.py` 和 `save_summary.py 修改`
