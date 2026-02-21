# Session Save 会话浪费优化设计

> 日期：2026-02-21
> 状态：设计中

---

## 1. 问题描述

当前 Memory Skill 的会话摘要保存流程会**额外消耗一次 Cursor 使用次数**。

### 当前流程

```
用户任务完成
  ↓
Cursor 触发 stop Hook (status=completed)
  ↓
prompt_session_save.py 输出 {"followup_message": "[Session Save] ..."}
  ↓
Cursor 注入 followup_message，开启 **新的 Agent 回合**  ← 消耗1次使用次数
  ↓
Agent 回顾对话，调用 save_summary.py + save_fact.py
  ↓
摘要和事实保存完成
```

**问题**：`followup_message` 机制会触发一个新的 Agent 回合，这意味着每次会话结束都会额外消耗一次 Cursor 使用配额。对于频繁使用的用户，这是不可忽视的浪费。

### 影响量化

- 每次会话结束：+1 次额外请求
- 假设每天 20 个会话：每天浪费 20 次请求
- 每月（按 22 个工作日）：约 440 次浪费

---

## 2. 根因分析

### 为什么需要新回合？

当前设计中，摘要生成依赖 **Agent 的语义理解能力**：

1. Agent 需要回顾整个对话上下文
2. Agent 需要判断哪些内容值得保存
3. Agent 需要生成结构化的摘要文本
4. Agent 需要分类提取事实（W/B/O）

这些操作在 `stop` Hook 触发时无法由纯 Python 脚本完成，因为 Hook 脚本没有对话上下文，也没有 LLM 推理能力。

### Hook 机制约束

| Hook | 触发时机 | 输出能力 | 是否消耗配额 |
|------|----------|----------|-------------|
| `preCompact` | 上下文压缩前 | `user_message` 注入 | 是（当前回合内） |
| `stop` | 任务完成后 | `followup_message` 注入 | **是（新回合）** |
| `sessionEnd` | 会话彻底关闭 | 无输出（fire-and-forget） | 否 |

关键发现：`stop` Hook 的 `followup_message` 必然触发新回合，这是 Cursor Hook 机制的设计——`stop` 意味着当前回合已结束。

---

## 3. 可选方案对比

### 方案 A：将摘要保存移入 Agent 最后一次回复中（Rules 驱动）

**思路**：不再依赖 `stop` Hook 注入提示词，而是通过 Rules 文件（`.cursor/rules/memory-rules.mdc`）在 Agent 的行为规范中要求：每次完成用户任务后，在同一回合内主动执行摘要保存。

**实现**：
- 删除 `stop` Hook 中的 `prompt_session_save.py`
- 在 `memory-rules.mdc` 或 SKILL.md 中添加规则：Agent 在完成任务后，自动执行 `save_summary.py` 和 `save_fact.py`
- `sessionEnd` Hook 做兜底检测（已有）

**优点**：
- 零额外请求消耗
- 实现简单，只需修改规则文件

**缺点**：
- 依赖 Agent 的规则遵从性，可能被忽略
- Agent 可能在复杂任务中忘记执行
- 增加每次回复的 token 消耗（Agent 需要额外执行保存命令）
- 与 `userinput.py` 等其他任务完成后的操作可能冲突

**可靠性评估**：⭐⭐（低，Agent 规则遵从不稳定）

---

### 方案 B：sessionEnd Hook 中用脚本自动生成摘要（无 LLM）

**思路**：在 `sessionEnd` Hook（fire-and-forget，不消耗配额）中，用纯 Python 脚本从已有数据中提取摘要，不依赖 Agent。

**实现**：
- `sessionEnd` 的 `sync_and_cleanup.py` 中增加自动摘要生成逻辑
- 从当日 `daily/*.jsonl` 中读取本会话产生的所有 fact
- 基于 fact 的 entities、content 自动聚合生成摘要
- 如果 `preCompact` 已触发过（有 flush 的 fact），则摘要质量较高
- 如果是短会话（无 fact），则跳过或生成极简摘要

**优点**：
- 零额外请求消耗
- 完全自动化，不依赖 Agent 行为
- `sessionEnd` 是 fire-and-forget，不影响用户体验

**缺点**：
- 摘要质量显著下降（无 LLM 语义理解）
- 无法提取会话中未被 `preCompact` 捕获的事实
- 短会话（未触发 preCompact）几乎无法生成有意义的摘要
- 需要额外的文本聚合逻辑

**可靠性评估**：⭐⭐⭐⭐（高，但质量低）

---

### 方案 C：混合方案——preCompact 增量保存 + sessionEnd 兜底聚合

**思路**：将摘要保存的工作分散到会话过程中，而不是集中在结束时。

**实现**：
1. **preCompact 增强**：在 `[Memory Flush]` 提示词中增加"阶段性摘要"要求，Agent 在每次上下文压缩前不仅保存事实，还保存一个阶段摘要
2. **sessionEnd 聚合**：在会话结束时，`sync_and_cleanup.py` 从所有阶段摘要 + fact 中聚合生成最终会话摘要
3. **stop Hook 降级**：`prompt_session_save.py` 仅在检测到会话无任何 fact/阶段摘要时才注入 `followup_message`（极少触发）

**实现细节**：

```
preCompact 触发时（当前回合内，不额外消耗）:
  ↓
Agent 保存 fact + 阶段摘要（save_fact.py --type S）
  ↓
sessionEnd 触发时（fire-and-forget，不消耗）:
  ↓
sync_and_cleanup.py 聚合所有阶段摘要 → 最终 session 摘要
  ↓
仅当无任何数据时，stop Hook 才注入 followup_message（兜底）
```

**优点**：
- 大幅减少额外请求（仅极端情况触发）
- 长会话摘要质量高（preCompact 时 Agent 有完整上下文）
- 短会话也有兜底机制
- 渐进式改造，风险低

**缺点**：
- 短会话（未触发 preCompact）仍可能需要 stop Hook 兜底
- 需要新增阶段摘要的存储格式
- preCompact 的提示词变长，增加少量 token 消耗

**可靠性评估**：⭐⭐⭐⭐（高，且质量较好）

---

### 方案 D：afterAgentResponse Hook 中渐进式保存

**思路**：利用已有的 `afterAgentResponse` Hook，在每次 Agent 回复后由脚本分析回复内容，自动提取并保存事实和摘要片段。

**实现**：
- `audit_response.py` 增强：解析 Agent 回复内容，提取关键信息
- 使用简单的规则引擎（关键词匹配、模式识别）提取事实
- 会话结束时由 `sessionEnd` 聚合

**优点**：
- 零额外请求
- 实时渐进式保存

**缺点**：
- 规则引擎的提取质量远不如 LLM
- `afterAgentResponse` 的 event 中可能不包含完整回复内容
- 实现复杂度高，维护成本大

**可靠性评估**：⭐⭐⭐（中等，实现复杂）

---

### 方案 E：A+C 融合——Rules 主动保存 + preCompact 增量 + sessionEnd 兜底

**思路**：将方案 A 的"Agent 主动保存"作为第一道防线，方案 C 的"preCompact 阶段摘要 + sessionEnd 聚合"作为第二、第三道防线，形成三层保障。

**三层保障机制**：

```
第一层：Rules 驱动（当前回合内）
  Agent 完成任务后，在同一回合内主动执行 save_summary + save_fact
  ↓ 如果 Agent 忘记执行...

第二层：preCompact 增量（当前回合内）
  上下文压缩前，Agent 保存阶段摘要 + fact
  ↓ 如果是短会话未触发 preCompact...

第三层：sessionEnd 聚合（零消耗）
  会话关闭后，脚本自动从已有数据聚合生成摘要
  ↓ 如果以上全部无数据...

兜底：stop Hook（极少触发）
  仅在会话无任何 fact 且 Agent 未主动保存时才注入 followup_message
```

**实现**：
1. **SKILL.md / Rules 层**：在 Agent 行为规范中明确要求——完成用户任务后，在回复的最后静默执行 `save_summary.py` 和 `save_fact.py`
2. **preCompact 层**：保持方案 C 的阶段摘要机制
3. **sessionEnd 层**：保持方案 C 的自动聚合逻辑
4. **stop Hook 层**：增加智能判断，仅在无数据时触发

**优点**：
- 三层冗余，极高可靠性
- 正常情况下 Agent 主动保存（第一层），摘要质量最高
- 即使 Agent 忽略规则，后续层仍能保障
- 额外请求消耗趋近于零

**缺点**：
- Agent 主动保存时增加每次回复的 token 消耗（约 200-300 token）
- 可能出现重复保存（Agent 主动保存 + preCompact 再次保存），需要去重
- 实现涉及多个层面，调试复杂度略高

**可靠性评估**：⭐⭐⭐⭐⭐（极高，多层冗余）

---

## 4. 推荐方案：方案 E（A+C 融合）

### 选择理由

| 维度 | 方案 A | 方案 B | 方案 C | 方案 D | **方案 E** |
|------|--------|--------|--------|--------|------------|
| 额外请求消耗 | 0 | 0 | ≈0 | 0 | **≈0** |
| 摘要质量 | 高 | 低 | 高 | 中 | **最高** |
| 可靠性 | 低 | 高 | 高 | 中 | **极高** |
| 实现复杂度 | 低 | 中 | 中 | 高 | **中高** |
| 改造风险 | 中 | 低 | 低 | 高 | **低** |

方案 E 的核心优势：
- **第一层 Rules 驱动**弥补了方案 C 对短会话的覆盖不足——Agent 在完成任务时主动保存，无论会话长短
- **第二层 preCompact**弥补了方案 A 的不可靠性——即使 Agent 忘记，长会话仍有阶段摘要
- **第三层 sessionEnd**提供最终兜底——即使前两层都失败，仍能从已有数据聚合
- 三层之间互为补充，单层失败不影响整体

---

## 5. 方案 E 详细设计

### 5.1 第一层：Rules 驱动 Agent 主动保存

在 SKILL.md 的 `[Session Save]` 行为说明中增加规则，同时在 `memory-rules.mdc` 中添加：

**新增规则内容**：

```
## 任务完成时的记忆保存（当前回合内执行）

当你完成用户请求的任务后，在同一回合内静默执行以下操作：

1. 判断本次会话是否有值得保存的内容（如果会话太短或无意义，跳过）
2. 调用 save_summary.py 保存会话摘要
3. 逐条调用 save_fact.py 保存关键事实
4. 所有操作静默执行，不在回复中提及
```

**关键设计点**：
- 这是"建议性规则"而非强制——Agent 可能忽略，但后续层会兜底
- 规则中明确"静默执行"，不影响用户体验
- 规则中明确"无意义会话跳过"，避免垃圾数据

### 5.2 第二层：preCompact 阶段摘要

修改 `flush_memory.py` 的提示词模板，增加阶段摘要要求：

```python
FLUSH_TEMPLATE = """[Memory Flush]

上下文即将压缩（当前使用率 {usage}%，消息数 {msg_count}）。请回顾当前对话，提取关键事实并保存。

## 提取规则
... (保持不变)

## 阶段摘要（新增）

请同时保存一条阶段摘要，概括当前对话阶段的主要内容：

```bash
{save_fact_cmd} --content "阶段摘要：[50-100字概括]" --type S --entities "session" --confidence 1.0 --session "{conv_id}"
```

## 注意
... (保持不变)
"""
```

同时修改 `save_fact.py` 支持 `--type S`：

```python
parser.add_argument("--type", default="W", choices=["W", "B", "O", "S"],
                    help="W=World, B=Biographical, O=Opinion, S=Summary")
```

### 5.3 第三层：sessionEnd 自动聚合

在 `sync_and_cleanup.py` 中新增 `auto_generate_summary()`：

```python
def auto_generate_summary(memory_dir: str, event: dict):
    """
    从本会话的 fact 和阶段摘要中自动聚合生成最终会话摘要。
    仅在 Agent 未主动保存摘要时执行（第一层失败的兜底）。
    """
    conv_id = event.get("conversation_id", "")
    if not conv_id:
        return

    # 第一层已保存则跳过
    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    last = read_last_entry(sessions_path)
    if last and last.get("session_id") == conv_id:
        log.info("摘要已存在（第一层已保存），跳过自动生成")
        return

    # 从 daily/*.jsonl 收集本会话的所有 fact 和阶段摘要
    daily_dir = os.path.join(memory_dir, "daily")
    session_facts = []
    session_summaries = []

    for f in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl")), reverse=True)[:3]:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                source = entry.get("source", {})
                if source.get("session") == conv_id:
                    if entry.get("memory_type") == "S":
                        session_summaries.append(entry.get("content", ""))
                    elif entry.get("type") == "fact":
                        session_facts.append(entry.get("content", ""))

    if not session_facts and not session_summaries:
        log.info("本会话无 fact/阶段摘要，跳过自动生成")
        return

    # 聚合：优先使用阶段摘要，其次用 fact 拼接
    topic_parts = [s.replace("阶段摘要：", "").strip() for s in session_summaries]
    topic = topic_parts[0] if topic_parts else (session_facts[0][:50] if session_facts else "未知主题")
    summary = " → ".join(topic_parts) if topic_parts else "; ".join(session_facts[:5])

    entry = {
        "id": f"sum-{ts_id()}",
        "session_id": conv_id,
        "topic": topic[:100],
        "summary": summary[:500],
        "decisions": [],
        "todos": [],
        "timestamp": iso_now(),
        "auto_generated": True,
    }

    with open(sessions_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info("自动生成摘要 id=%s topic='%s'", entry["id"], topic[:30])
```

### 5.4 兜底层：stop Hook 智能降级

修改 `prompt_session_save.py`，增加数据检测逻辑：

```python
def has_session_data(memory_dir: str, conv_id: str) -> bool:
    """检查本会话是否已有摘要或 fact（第一层或第二层已工作）"""
    # 检查是否已有摘要（第一层成功）
    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    last = read_last_entry(sessions_path)
    if last and last.get("session_id") == conv_id:
        return True

    # 检查是否有 fact（第二层成功）
    daily_dir = os.path.join(memory_dir, "daily")
    if not os.path.isdir(daily_dir):
        return False

    today_file = os.path.join(daily_dir, f"{today_str()}.jsonl")
    if not os.path.exists(today_file):
        return False

    with open(today_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                source = entry.get("source", {})
                if source.get("session") == conv_id and entry.get("type") == "fact":
                    return True
            except json.JSONDecodeError:
                continue
    return False


def main():
    # ... 现有逻辑 ...

    if has_session_data(memory_dir, conv_id):
        log.info("会话已有数据（第一/二层已工作），跳过 followup_message")
        print(json.dumps({}))
        return

    # 仅在前两层都无数据时才注入（最终兜底）
    prompt = SAVE_TEMPLATE.format(...)
    print(json.dumps({"followup_message": prompt}))
```

### 5.5 去重机制

由于多层可能产生重复数据，需要在以下位置增加去重：

**save_summary.py 去重**：保存前检查是否已有相同 session_id 的摘要

```python
# 在写入前检查
sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
last = read_last_entry(sessions_path)
if last and last.get("session_id") == args.session:
    log.info("摘要已存在 session_id=%s，跳过重复保存", args.session)
    print(json.dumps({"status": "skipped", "reason": "duplicate"}))
    return
```

**auto_generate_summary 去重**：已在 5.3 中包含（检查 last session_id）

### 5.6 SKILL.md 更新

更新 SKILL.md 中的行为说明，增加第一层规则：

```markdown
### 任务完成时（当前回合内）

完成用户任务后，在同一回合内静默执行：

1. 判断本次会话是否有值得保存的内容
2. 如有，调用 save_summary.py 保存摘要 + save_fact.py 保存事实
3. 静默执行，不在回复中提及
4. 如果会话太短或无意义，跳过
```

---

## 6. 预期效果

### 场景分析

| 会话类型 | 第一层 Rules | 第二层 preCompact | 第三层 sessionEnd | 兜底 stop | 额外请求 |
|----------|-------------|-------------------|-------------------|-----------|---------|
| 长会话（>阈值） | ✅ Agent 主动保存 | ✅ 阶段摘要（冗余） | ✅ 跳过（已有） | ❌ 跳过 | **0** |
| 中等会话 | ✅ Agent 主动保存 | ⚠️ 可能触发 | ✅ 跳过（已有） | ❌ 跳过 | **0** |
| 短会话（Agent 遵从规则） | ✅ Agent 主动保存 | ❌ 未触发 | ✅ 跳过（已有） | ❌ 跳过 | **0** |
| 短会话（Agent 忽略规则） | ❌ 未执行 | ❌ 未触发 | ❌ 无数据 | ✅ 兜底注入 | **1** |
| 极短会话（无意义） | ❌ 跳过 | ❌ | ❌ | ❌ 跳过 | **0** |

### 节省量化与"极少触发"推导

**基于实际数据的分析**（来自本项目 `memory-data/daily/` 统计）：

当前系统共记录 8 个会话，其中：
- 6 个会话有 fact + summary（75%）→ 这些会话中 preCompact 或 stop Hook 已成功工作
- 2 个会话无任何 fact/summary（25%）→ 这些是"需要兜底"的会话

**分析这 2 个无数据会话的特征**：
- `77c2de02...`：仅有 `session_end` 事件，无 `session_start`，说明是异常关闭或极短会话
- `e16f1243...`：有 `session_start` + `session_end`（reason=user_close），被系统标记为"未保存摘要"警告，说明用户手动关闭了会话

**结论**：这 25% 的"无数据会话"属于以下两类：
1. **用户主动关闭**（user_close）：用户在 Agent 完成任务前就关闭了会话，此时 stop Hook 不会触发（status 不是 completed/aborted）
2. **异常/极短会话**：会话几乎没有有意义的内容

**在方案 E 中，stop Hook 兜底触发需要同时满足**：
1. status 为 completed 或 aborted（排除了 user_close）
2. 第一层 Rules 未生效（Agent 忽略了主动保存规则）
3. 第二层 preCompact 未触发（短会话）
4. 会话有足够内容值得保存（排除极短会话）

**推导**：
- 当前 75% 的会话已有数据 → 第二/三层即可覆盖
- 剩余 25% 中，大部分是 user_close 或极短会话 → stop Hook 本身就不会触发
- 真正需要兜底的场景：**短但有意义的会话 + Agent 忽略 Rules + 未触发 preCompact + status=completed**
- 加入第一层 Rules 后，即使 Agent 遵从率仅 70%，也能覆盖大部分短会话

**保守估计**：stop Hook 兜底触发率 < 10%（约每 10 个会话触发不到 1 次）

> 注意："极少触发"是基于三层防线叠加后的推导，而非单层保障。任何单层的覆盖率都不足以支撑这个结论。

### 与纯方案 C 的对比

| 指标 | 方案 C | 方案 E（A+C 融合） |
|------|--------|-------------------|
| 长会话覆盖率 | 100% | 100% |
| 短会话覆盖率 | 0%（需兜底） | ~70%（Rules 驱动） |
| 总体零消耗率 | ~70% | ~94% |
| 摘要质量 | 高（preCompact 时） | 最高（Agent 主动 + preCompact 冗余） |

---

## 7. 实施步骤

1. **Phase 1**：`save_fact.py` 增加 `--type S` 支持
2. **Phase 2**：`flush_memory.py` 模板增加阶段摘要要求
3. **Phase 3**：`sync_and_cleanup.py` 增加 `auto_generate_summary()`
4. **Phase 4**：`prompt_session_save.py` 增加 `has_session_data()` 智能判断
5. **Phase 5**：`save_summary.py` 增加去重检查
6. **Phase 6**：更新 SKILL.md + `memory-rules.mdc`，添加第一层 Rules 规则

### 修改文件清单

| 文件 | 修改内容 | 所属层 |
|------|---------|--------|
| `save_fact.py` | `--type` 增加 `S` 选项 | 第二层 |
| `flush_memory.py` | 模板增加阶段摘要要求 | 第二层 |
| `sync_and_cleanup.py` | 新增 `auto_generate_summary()` | 第三层 |
| `prompt_session_save.py` | 新增 `has_session_data()` 判断 | 兜底层 |
| `save_summary.py` | 新增 session_id 去重检查 | 去重 |
| `SKILL.md` | 新增任务完成时主动保存规则 | 第一层 |
| `memory-rules.mdc` | 新增任务完成时主动保存规则 | 第一层 |

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Agent 忽略第一层 Rules | 短会话可能需兜底 | 第二/三层 + stop Hook 兜底 |
| Agent 在 preCompact 时忽略阶段摘要 | 第三层聚合质量下降 | 第一层可能已保存；stop Hook 兜底 |
| 多层重复保存 | 数据冗余 | save_summary.py 去重 + auto_generate 去重 |
| 自动聚合摘要质量不如 LLM | 信息丢失 | 标记 `auto_generated: true`，后续可人工补充 |
| preCompact 提示词变长 | token 消耗增加 | 增量极小（约 50 token），远低于一次完整请求 |
| 第一层增加每次回复 token | 成本增加 | 约 200-300 token，远低于一次新回合（数千 token） |

---

## 9. 2026-02-21-01 设计评审补充（不足与修正建议）

### P0（高优先级）

1. **去重与“已保存”判断存在漏判风险（仅看最后一条）**
   - 当前设计在 5.3/5.4/5.5 中多处以 `read_last_entry()` 判断“本会话是否已保存”，当 `sessions.jsonl` 末尾被其他会话插入时会漏判，导致重复保存或误触发 stop 兜底。
   - **建议修正**：改为“按 `session_id` 全文件扫描（或建立会话索引）”，判断条件从“最后一条是否匹配”升级为“是否存在任意匹配记录”。

2. **`has_session_data()` 仅检查当日日志，跨天会话会误判为无数据**
   - 现设计只读取 `daily/{today}.jsonl`，会话跨零点时，前一天的 fact/阶段摘要无法被识别，可能触发不必要的 `followup_message`。
   - **建议修正**：检查最近 N 天 `daily/*.jsonl`（至少 2-3 天）并按 `source.session == conv_id` 过滤；或使用统一查询函数按会话 ID 拉取。

### P1（中优先级）

3. **`memory_type=S` 的下游影响未封装，可能污染“近期事实”和提炼结果**
   - 方案引入 `S` 类型后，现有加载/提炼链路会把其当普通 fact 处理，可能导致“阶段摘要”重复进入上下文，影响检索与压缩质量。
   - **建议修正**：
     - `load_memory` 默认过滤 `memory_type=S`（或单独分组展示，默认不注入）；
     - `distill_to_memory` 排除 `S`，避免将阶段摘要提炼进 `MEMORY.md`。

4. **“第一层任务完成后主动保存”的触发语义不够可执行**
   - 文档描述“任务完成后”触发，但未定义“一次会话内只执行一次”的判定机制；多轮对话可能多次保存摘要，造成重复和噪声。
   - **建议修正**：增加会话级幂等标记（如 `summary_saved_for_session=true`）或在规则中明确“每个 `conversation_id` 仅首个完成点保存一次”。

5. **节省率推导样本偏小且口径混合，缺少上线后可观测指标**
   - 当前“stop 兜底 < 10% / 零消耗率 ~94%”来自小样本推导，且混入 `user_close` 等 stop 不触发场景，作为目标值风险较高。
   - **建议修正**：补充验收口径和埋点（至少记录：第一层命中率、第二层命中率、stop 触发率、重复写入率、自动聚合占比），灰度一周后再固化目标值。

### P2（可优化）

6. **`auto_generate_summary()` 仅扫描最近 3 个 daily 文件，长会话可能丢失上下文**
   - 会话跨多天时，`[:3]` 截断可能遗漏早期阶段摘要或事实。
   - **建议修正**：改为“按 `conversation_id` 全量检索”后再做长度裁剪，而不是按文件数量裁剪。

---

## 10. 2026-02-21-01 方案 A-E 可行性评估（重点 E）

### 10.1 总览结论

| 方案 | 技术可行性 | 生产可行性 | 结论 |
|------|-----------|-----------|------|
| A（Rules 主动保存） | 高 | 中 | 能做，但强依赖 Agent 遵从，稳定性受模型行为影响 |
| B（sessionEnd 脚本聚合） | 高 | 中 | 能做，稳定但摘要质量偏低 |
| C（preCompact + sessionEnd） | 高 | 中高 | 能做，适合长会话；短会话覆盖仍依赖兜底 |
| D（afterAgentResponse 提取） | 中 | 低中 | 能做但实现复杂、误判成本高，不建议优先 |
| E（A+C 融合） | **高** | **高（修正后）** | **推荐，具备上线条件** |

### 10.2 分方案说明

1. **方案 A 可行性**
   - 当前已具备 Rules 和脚本能力，新增“任务完成后主动 `save_summary + save_fact`”即可落地。
   - 主要问题不是“能不能实现”，而是“能否稳定执行”。

2. **方案 B 可行性**
   - `sessionEnd` 是 fire-and-forget，脚本聚合容易落地，且不会增加请求次数。
   - 但无 LLM 语义理解，摘要质量上限明显受限，更适合作为兜底层。

3. **方案 C 可行性**
   - preCompact/stop/sessionEnd 三个 Hook 均已存在，实现路径清晰。
   - 需要补齐 `memory_type=S` 的下游隔离策略（避免污染加载与提炼）。

4. **方案 D 可行性**
   - `afterAgentResponse` 已可读取文本并做审计，理论上可扩展为提取写入。
   - 但规则引擎误判、维护成本和可解释性压力较高，ROI 不如 E。

5. **方案 E（重点）可行性**
   - **技术上可行**：现有基础设施已覆盖三层防线所需的 Hook 与存储链路。
   - **生产上可行（前提）**：需要先完成第 9 节的 P0/P1 修正，特别是：
     1) 由“最后一条判断”改为“按 `session_id` 存在性判断”；  
     2) `has_session_data` 支持跨天会话检索；  
     3) `S` 类型与加载/提炼链路隔离；  
     4) 定义“每个会话仅保存一次摘要”的幂等规则与指标埋点。
   - 在上述修正到位后，方案 E 可以作为主方案推进。

### 10.3 方案 E 的上线门槛（建议）

满足以下门槛再灰度：

1. 单元测试覆盖新增逻辑（去重、跨天、幂等、无数据兜底）
2. 埋点可观测（第一层命中率、stop 触发率、重复写入率）
3. 灰度 1 周后验证：stop 触发率明显下降且摘要质量无明显回退
