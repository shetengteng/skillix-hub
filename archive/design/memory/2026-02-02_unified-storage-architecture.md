# 统一存储架构设计：Memory 作为核心存储层

> **版本**: v1.0
> **日期**: 2026-02-02
> **状态**: 设计中

## 一、问题背景

### 1.1 当前架构

目前三个 Skill 各自独立存储数据：

```
~/.cursor/skills/
├── memory-data/                    # Memory Skill 数据
│   ├── daily/                      # 每日记忆
│   ├── index/keywords.json         # 关键词索引
│   ├── temp/                       # 临时记忆
│   └── config.json
│
├── behavior-prediction-data/       # Behavior Prediction 数据
│   ├── sessions/                   # 会话记录
│   ├── patterns/                   # 行为模式
│   ├── profile/                    # 用户画像
│   └── index/
│
└── continuous-learning-data/       # Continuous Learning 数据（计划）
    ├── observations/               # 观察记录
    ├── instincts/                  # 本能文件
    ├── evolved/                    # 演化技能
    └── profile/
```

### 1.2 存在的问题

| 问题 | 影响 |
|------|------|
| **数据冗余** | 三个 Skill 都存储会话信息，格式不同但内容重叠 |
| **索引分散** | 每个 Skill 维护自己的索引，无法跨 Skill 检索 |
| **维护成本高** | 三套存储逻辑，三套清理策略，三套导入导出 |
| **数据不一致** | 同一会话在不同 Skill 中可能有不同的记录 |

### 1.3 核心洞察

分析三个 Skill 的数据本质：

| Skill | 存储内容 | 本质 |
|-------|---------|------|
| **Memory** | 对话记忆、决策、偏好 | **原始事实** |
| **Behavior Prediction** | 会话记录、工作流程、用户画像 | **模式分析** |
| **Continuous Learning** | 观察记录、本能、技能 | **知识提取** |

**关键发现**：Memory 存储的是"原始事实"，而 Behavior Prediction 和 Continuous Learning 都是基于这些事实进行"分析和提取"。

## 二、设计目标

### 2.1 核心原则

1. **Memory 作为唯一存储层**：所有原始数据都存储在 Memory 中
2. **其他 Skill 作为分析层**：从 Memory 读取数据，生成分析结果
3. **分析结果可选存储**：分析结果可以缓存，但不是必须的

### 2.2 预期收益

| 收益 | 说明 |
|------|------|
| **单一数据源** | 消除数据冗余和不一致 |
| **统一索引** | 一次索引，多处使用 |
| **简化维护** | 一套存储逻辑，一套清理策略 |
| **更好的检索** | 跨 Skill 的语义检索成为可能 |

## 三、改造方案

### 方案 A：完全统一（推荐）

#### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Memory Skill                            │
│                    (统一存储层)                               │
├─────────────────────────────────────────────────────────────┤
│  memory-data/                                                │
│  ├── daily/                    # 每日记忆（原有）             │
│  │   └── 2026-02-02.md                                       │
│  ├── sessions/                 # 会话原始数据（新增）         │
│  │   └── 2026-02/                                            │
│  │       └── sess_20260202_001.json                          │
│  ├── index/                    # 统一索引（扩展）             │
│  │   ├── keywords.json         # 关键词索引                  │
│  │   ├── sessions.json         # 会话索引                    │
│  │   └── tags.json             # 标签索引                    │
│  ├── temp/                     # 临时数据                    │
│  └── config.json                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 读取
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Behavior Prediction Skill                       │
│                    (分析层)                                   │
├─────────────────────────────────────────────────────────────┤
│  behavior-prediction-cache/    # 可选缓存                    │
│  ├── patterns/                 # 分析出的模式                │
│  │   ├── workflow_patterns.json                              │
│  │   └── transition_matrix.json                              │
│  └── profile/                  # 用户画像                    │
│      └── user_profile.json                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 读取
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Continuous Learning Skill                       │
│                    (知识层)                                   │
├─────────────────────────────────────────────────────────────┤
│  continuous-learning-cache/    # 可选缓存                    │
│  ├── instincts/                # 本能文件                    │
│  └── evolved/                  # 演化技能                    │
└─────────────────────────────────────────────────────────────┘
```

#### 数据流

```
会话开始
    │
    ▼
┌─────────────────┐
│  Memory --init  │  ← 创建 pending session
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  会话进行中     │  ← Memory 实时保存重要信息
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│              Memory --finalize                   │
│  1. 保存完整会话数据到 sessions/                 │
│  2. 更新 daily/ 记忆文件                         │
│  3. 更新统一索引                                 │
└────────┬────────────────────────────────────────┘
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ▼                                          ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│  Behavior Prediction    │          │  Continuous Learning    │
│  从 Memory 读取会话数据  │          │  从 Memory 读取会话数据  │
│  分析行为模式            │          │  检测可学习模式          │
│  更新用户画像            │          │  生成/更新本能           │
└─────────────────────────┘          └─────────────────────────┘
```

#### Memory 数据格式扩展

**sessions/sess_xxx.json**（新增）：

```json
{
  "session_id": "sess_20260202_001",
  "version": "3.0",
  "project": {
    "path": "/path/to/project",
    "name": "project-name"
  },
  "time": {
    "start": "2026-02-02T10:00:00Z",
    "end": "2026-02-02T11:30:00Z",
    "duration_minutes": 90
  },
  "conversation": {
    "messages": [
      {
        "role": "user",
        "content": "帮我创建一个 API",
        "timestamp": "2026-02-02T10:00:00Z"
      },
      {
        "role": "assistant",
        "content": "好的，我来创建...",
        "timestamp": "2026-02-02T10:00:05Z"
      }
    ],
    "message_count": 20
  },
  "operations": {
    "files": {
      "created": ["src/api.py"],
      "modified": ["src/main.py"],
      "deleted": []
    },
    "commands": [
      {"command": "pytest", "exit_code": 0}
    ],
    "tools_used": ["Write", "Shell", "Read"]
  },
  "summary": {
    "topic": "API 开发",
    "goals": ["创建 REST API"],
    "completed_tasks": ["创建 api.py"],
    "technologies_used": ["Python", "FastAPI"],
    "workflow_stages": ["implement", "test"],
    "tags": ["#api", "#backend"]
  },
  "memories": [
    {
      "id": "mem_001",
      "type": "decision",
      "content": "决定使用 FastAPI",
      "importance": "high"
    }
  ]
}
```

#### Behavior Prediction 改造

**改造前**：
```python
# hook.py --init
def init():
    # 从自己的 sessions/ 目录读取历史数据
    sessions = load_sessions_from_local()
    patterns = analyze_patterns(sessions)
    return patterns
```

**改造后**：
```python
# hook.py --init
def init():
    # 从 Memory 读取历史会话数据
    from memory.scripts.utils import get_sessions
    sessions = get_sessions(days=90)
    patterns = analyze_patterns(sessions)
    return patterns

# hook.py --finalize
def finalize(session_data):
    # 不再自己存储，而是通知 Memory 存储
    from memory.scripts.hook import finalize as memory_finalize
    memory_finalize(session_data)
    
    # 然后基于新数据更新分析结果
    update_patterns(session_data)
```

#### Continuous Learning 改造

**改造前**：
```python
# observe.py --init
def init():
    # 从自己的 observations/ 目录读取
    observations = load_observations()
    return analyze(observations)
```

**改造后**：
```python
# observe.py --init
def init():
    # 从 Memory 读取历史会话
    from memory.scripts.utils import get_sessions
    sessions = get_sessions(days=90)
    
    # 分析会话中的可学习模式
    patterns = detect_patterns(sessions)
    return patterns
```

#### 优点

1. **彻底消除冗余**：所有原始数据只存一份
2. **统一的数据格式**：便于维护和扩展
3. **简化的清理策略**：只需配置 Memory 的 retention
4. **更好的跨 Skill 协作**：共享同一数据源

#### 缺点

1. **改造工作量大**：需要重写两个 Skill 的存储逻辑
2. **依赖关系**：Behavior Prediction 和 Continuous Learning 依赖 Memory
3. **Memory 成为单点**：如果 Memory 出问题，影响其他 Skill

---

### 方案 B：共享索引层

#### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Shared Index Layer                        │
│                      (共享索引层)                             │
├─────────────────────────────────────────────────────────────┤
│  shared-index/                                               │
│  ├── sessions.json             # 会话索引                    │
│  ├── keywords.json             # 关键词索引                  │
│  ├── tags.json                 # 标签索引                    │
│  └── cross_references.json     # 跨 Skill 引用               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     Memory      │  │    Behavior     │  │   Continuous    │
│   memory-data/  │  │   Prediction    │  │    Learning     │
│   (原有结构)    │  │   bp-data/      │  │   cl-data/      │
│                 │  │   (原有结构)    │  │   (原有结构)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 工作方式

1. 每个 Skill 保持自己的数据存储
2. 引入共享索引层，记录所有数据的元信息
3. 跨 Skill 检索通过共享索引实现

#### 优点

1. **改造工作量小**：只需添加索引同步逻辑
2. **向后兼容**：现有数据结构不变
3. **渐进式迁移**：可以逐步过渡到方案 A

#### 缺点

1. **数据仍然冗余**：只解决了检索问题
2. **索引同步复杂**：需要保证索引一致性
3. **维护成本仍高**：三套存储逻辑仍需维护

---

### 方案 C：Memory 作为存储代理

#### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Skill                              │
│                  (存储代理层)                                 │
├─────────────────────────────────────────────────────────────┤
│  memory-data/                                                │
│  ├── daily/                    # Memory 自己的数据           │
│  ├── index/                    # 统一索引                    │
│  ├── stores/                   # 代理存储（新增）            │
│  │   ├── behavior-prediction/  # BP 的数据                   │
│  │   │   ├── sessions/                                       │
│  │   │   └── patterns/                                       │
│  │   └── continuous-learning/  # CL 的数据                   │
│  │       ├── observations/                                   │
│  │       └── instincts/                                      │
│  └── config.json                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 工作方式

1. Memory 提供统一的存储 API
2. 其他 Skill 通过 Memory API 存取数据
3. Memory 负责统一的索引和清理

#### API 设计

```python
# memory/scripts/store_api.py

def save(namespace: str, key: str, data: dict) -> bool:
    """
    保存数据到指定命名空间
    
    Args:
        namespace: 命名空间，如 "behavior-prediction"
        key: 数据键，如 "sessions/2026-02/sess_001"
        data: 要保存的数据
    """
    pass

def load(namespace: str, key: str) -> dict:
    """从指定命名空间加载数据"""
    pass

def query(namespace: str, filters: dict) -> list:
    """查询指定命名空间的数据"""
    pass

def delete(namespace: str, key: str) -> bool:
    """删除指定数据"""
    pass
```

#### 优点

1. **统一存储位置**：所有数据在 memory-data/ 下
2. **统一清理策略**：Memory 统一管理数据生命周期
3. **保持独立性**：每个 Skill 仍有自己的数据结构

#### 缺点

1. **API 设计复杂**：需要设计通用的存储 API
2. **性能开销**：多一层代理
3. **不彻底**：数据结构仍然分散

---

## 四、方案对比

| 维度 | 方案 A（完全统一） | 方案 B（共享索引） | 方案 C（存储代理） |
|------|------------------|------------------|------------------|
| **数据冗余** | ✅ 完全消除 | ❌ 仍存在 | ⚠️ 部分消除 |
| **改造工作量** | ❌ 大 | ✅ 小 | ⚠️ 中等 |
| **维护成本** | ✅ 低 | ❌ 高 | ⚠️ 中等 |
| **跨 Skill 协作** | ✅ 天然支持 | ⚠️ 需要索引 | ⚠️ 需要 API |
| **向后兼容** | ❌ 不兼容 | ✅ 兼容 | ⚠️ 部分兼容 |
| **长期可维护性** | ✅ 高 | ❌ 低 | ⚠️ 中等 |

## 五、推荐方案

### 推荐：方案 A（完全统一）

理由：
1. **从根本上解决问题**：消除数据冗余，简化架构
2. **长期收益大**：虽然改造工作量大，但一劳永逸
3. **符合设计原则**：Memory 作为"记忆"的本质就是存储事实

### 实施建议

由于不考虑兼容性和数据迁移，可以直接重写：

1. **Phase 1**：扩展 Memory 数据格式，支持会话存储
2. **Phase 2**：改造 Behavior Prediction，从 Memory 读取数据
3. **Phase 3**：改造 Continuous Learning，从 Memory 读取数据
4. **Phase 4**：删除旧的数据目录

## 六、详细改造计划

### 6.1 Memory Skill 改造

#### 新增功能

1. **会话存储**：支持存储完整会话数据
2. **扩展索引**：支持按会话、标签、时间范围检索
3. **数据导出 API**：供其他 Skill 调用

#### 新增脚本

```
memory/scripts/
├── session_store.py      # 会话存储管理
├── unified_index.py      # 统一索引管理
└── export_api.py         # 数据导出 API
```

#### 配置扩展

```json
{
  "version": "3.0",
  "session_storage": {
    "enabled": true,
    "include_messages": true,
    "include_operations": true
  },
  "unified_index": {
    "enabled": true,
    "index_sessions": true,
    "index_tags": true
  }
}
```

### 6.2 Behavior Prediction 改造

#### 删除的功能

1. 删除 `sessions/` 目录及相关存储逻辑
2. 删除 `record_session.py`（改为调用 Memory）

#### 保留的功能

1. 保留 `patterns/` 目录（分析结果缓存）
2. 保留 `profile/` 目录（用户画像）
3. 保留所有分析逻辑

#### 改造的脚本

```python
# hook.py
def finalize(session_data):
    # 改为调用 Memory 存储
    from memory.scripts.session_store import save_session
    save_session(session_data)
    
    # 然后更新分析结果
    update_patterns(session_data)

def init():
    # 从 Memory 读取历史数据
    from memory.scripts.export_api import get_recent_sessions
    sessions = get_recent_sessions(days=90)
    return analyze(sessions)
```

### 6.3 Continuous Learning 改造

#### 删除的功能

1. 删除 `observations/` 目录（改为从 Memory 读取）

#### 保留的功能

1. 保留 `instincts/` 目录（本能文件）
2. 保留 `evolved/` 目录（演化技能）
3. 保留所有分析和演化逻辑

#### 改造的脚本

```python
# observe.py
def init():
    # 从 Memory 读取历史会话
    from memory.scripts.export_api import get_recent_sessions
    sessions = get_recent_sessions(days=90)
    
    # 分析可学习模式
    return detect_patterns(sessions)

def finalize(session_data):
    # 不再单独存储观察记录
    # 直接从 session_data 中提取模式
    patterns = detect_patterns([session_data])
    update_instincts(patterns)
```

## 七、新架构数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                           会话开始                                   │
└────────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Memory --init                                    │
│  1. 自动 finalize 上一个会话                                         │
│  2. 创建 pending session                                             │
│  3. 返回最近记忆供上下文                                             │
└────────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ├─────────────────────────────────────┐
                                 │                                     │
                                 ▼                                     ▼
┌─────────────────────────────────────────┐  ┌─────────────────────────────────────┐
│     Behavior Prediction --init          │  │    Continuous Learning --init       │
│  从 Memory 读取历史会话                  │  │  从 Memory 读取历史会话              │
│  分析行为模式                            │  │  加载已有本能                        │
│  返回预测建议                            │  │  返回学习状态                        │
└─────────────────────────────────────────┘  └─────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         会话进行中                                   │
│  Memory: 实时保存重要信息到 temp/                                    │
│  BP: 记录动作（可选）                                                │
│  CL: 检测可学习模式（可选）                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Memory --finalize                                │
│  1. 汇总临时记忆                                                     │
│  2. 保存完整会话数据到 sessions/                                     │
│  3. 更新 daily/ 记忆文件                                             │
│  4. 更新统一索引                                                     │
│  5. 通知其他 Skill（可选）                                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ├─────────────────────────────────────┐
                                 │                                     │
                                 ▼                                     ▼
┌─────────────────────────────────────────┐  ┌─────────────────────────────────────┐
│   Behavior Prediction --on_session_end  │  │  Continuous Learning --on_session_end│
│  从 Memory 读取刚保存的会话              │  │  从 Memory 读取刚保存的会话          │
│  更新行为模式                            │  │  检测新模式                          │
│  更新用户画像                            │  │  更新本能                            │
└─────────────────────────────────────────┘  └─────────────────────────────────────┘
```

## 八、总结

### 核心改变

1. **Memory 成为唯一的原始数据存储层**
2. **Behavior Prediction 和 Continuous Learning 变为纯分析层**
3. **统一的会话数据格式**
4. **统一的索引和检索**

### 预期效果

| 指标 | 改造前 | 改造后 |
|------|--------|--------|
| 数据目录数 | 3 | 1 |
| 索引文件数 | 3+ | 1 |
| 存储逻辑套数 | 3 | 1 |
| 清理策略套数 | 3 | 1 |
| 跨 Skill 检索 | 不支持 | 支持 |

### 下一步

1. 确认采用方案 A
2. 设计 Memory 的会话存储格式
3. 设计 Memory 的导出 API
4. 开始实施改造

---

## 九、方案 A（完全统一）设计审阅与改进建议（2026-02-02-01）

以下建议以 Cursor 的真实运行方式为核心前提：**进程随时中断、规则触发不可控、多个 Skill 可能并发触发脚本、Python import 路径不稳定（不同安装位置/项目级 vs 全局）**。

同时结合你补充的背景：这是开发阶段的重构，可视为“新项目”，**不需要考虑历史数据迁移成本**；但仍建议保留最小的 schema 演进与可回退开关（面向未来迭代与故障自救），避免把“开发期便利”变成“后续维护负担”。

### 9.1 关键缺口与风险点（按优先级）

1. **依赖耦合与循环依赖风险**
   - 文档中“改造后 Behavior Prediction 的 `finalize()` 直接 `from memory.scripts.hook import finalize`”属于强 import 依赖；在 Cursor 的多安装形态下（全局/项目级），容易出现 import 失败或加载到“另一个位置的 memory”。
   - 如果未来 Memory 也想“通知其他 Skill”，就会出现潜在循环依赖（Memory ↔ BP/CL）。

2. **并发写入与一致性没有设计**
   - 方案 A 中 `memory-data/` 将承担：pending session、temp、finalize、索引更新。Cursor 环境下可能出现多个脚本同时运行（规则触发/用户多次操作/多终端），若无文件锁或原子写策略，会导致 `pending_session.json`、`index/*.json` 竞争写、索引损坏或丢数据。

3. **“原始事实”与“派生结果”的边界仍不清**
   - 你定义 Memory 存“原始事实”，但 `sessions/sess_xxx.json` 同时包含 `summary`、`workflow_stages` 等派生信息；这些字段未来很可能由 BP/CL 生成，容易造成“谁负责写、谁负责改、谁是权威”的不一致。

4. **Schema 演进/兼容策略缺失**
   - `version: "3.0"` 只写在示例里，但没有说明：字段新增/删除/重命名时，BP/CL 如何兼容；索引结构如何升级；旧会话文件是否需要回填/迁移。

5. **索引策略过于笼统，可能成为性能瓶颈**
   - 统一索引是对的，但没有约束“索引更新粒度、重建策略、增量更新、检索范围（按项目/时间）”。在长期使用后，`sessions.json/keywords.json/tags.json` 若做成“大 JSON”，读写和 merge 会越来越慢，且冲突概率更高。

6. **隐私/敏感信息处理未定义**
   - `conversation.messages[].content` 会保存大量原文，可能含密钥、token、内部链接等。Cursor 场景经常会把配置/日志粘贴进对话；若无脱敏/排除策略，Memory 会把敏感信息长期落盘。

7. **“不考虑兼容性/迁移”仍需最低限度的“安全退路”**
   - 即使你不做历史迁移，也需要定义：出现问题如何回滚（例如临时恢复旧数据目录）、如何禁用统一化、如何重新生成索引。

### 9.2 对方案 A 的结构性改进（尽量不引入额外抽象层）

1. **将“写入 Memory”的交互改为“命令契约”，避免 Python 直接 import**
   - 建议 BP/CL 与 Memory 的交互优先走子进程调用（`python3 <memory_dir>/scripts/...`）+ 约定 JSON 输入输出；这与当前三个 skill 的使用方式一致，也更贴合 Cursor 的规则触发。
   - 这样可以把依赖从“代码级 import”降级为“CLI 协议”，同时天然避免循环依赖。

2. **明确三类数据的“权威写入者”**
   - 建议把 `sessions/sess_xxx.json` 拆成最小权威面：
     - **raw/conversation**：原始 messages（可配置是否保存原文）
     - **raw/operations**：文件与命令的事实记录
     - **facts/memories**：Memory 自己提取并确认要保存的“事实条目”（decision/preference/config/plan）
   - `summary/workflow_stages/technologies_used` 这类字段建议定义为“可选派生”，来源可标注：`derived_by: "memory|behavior-prediction|continuous-learning"`，或直接只放到各自 cache 中，避免 Memory 里出现多方写同一字段的情况。

3. **引入最小的文件锁 + 原子写规范（不需要引入第三方依赖）**
   - 至少定义两条写入纪律：
     - **原子写**：写到临时文件后 `rename` 覆盖（避免半写入）
     - **锁粒度**：对 `pending_session.json`、`index/*.json`、单个 session 文件分别加锁（避免全局大锁）
   - 这些规则写进文档即可，后续实现仍可用标准库完成。

4. **索引建议从“大 JSON”转向“可增量更新的分片”**
   - 保持现有目录不大改的前提下，建议：
     - `index/sessions/2026-02.json`（按月分片）
     - `index/keywords/<kw_prefix>.json` 或者 `index/keywords_shards/*.json`
     - `index/tags/<tag>.json`（每 tag 一份或按 hash 分片）
   - 好处：增量写更小、并发冲突更少、读取按需范围更明确。

5. **项目隔离与多安装位置的“定位规则”需要落到契约**
   - 你在 Memory v2.0 已有 `storage.location: project-first` 的概念；方案 A 建议补充明确：
     - session 记录必须带 `project.path` 与一个稳定的 `project_id`（如 path hash）
     - 索引检索默认按当前项目过滤，跨项目检索需要显式参数
     - 当项目级与全局同时存在时，读取优先级、合并策略、冲突策略要固定（否则“读到不同地方的数据”会非常隐蔽）

6. **敏感信息的最小保护措施（Cursor 场景强烈建议）**
   - 建议至少加两个开关：
     - `session_storage.include_messages`（已在文档出现）默认可考虑为 `false` 或支持“仅保存 user 摘要/仅保存 decision 相关片段”
     - `redaction.enabled` + `redaction.patterns`（简单正则/关键字），对 `token/secret/key/password` 等做掩码
   - 这不改变总体架构，但显著降低落盘风险。

### 9.3 方案 A 的落地顺序调整（仍保持 Phase 思路）

你目前的 Phase 更偏“先扩结构再改两端”。在 Cursor 场景我建议把“稳定契约”前置，减少回滚成本：

1. **Phase 0（先定义契约）**：确定 Memory 的 CLI 输入输出 JSON（init/save/finalize/export），以及 session schema 的“权威字段集合”
2. **Phase 1（只让 Memory 产出 session 原始事实）**：先把 `sessions/` 写起来并保证锁/原子写
3. **Phase 2（BP/CL 只读 Memory）**：先改成只读导出接口（不写 Memory），验证分析逻辑正确
4. **Phase 3（可选回写派生结果）**：若确实需要缓存，写到各自 cache；若要写回 Memory，必须遵循“derived_*”命名空间与锁规则
5. **Phase 4（删除旧目录）**：保留“可手动恢复”的说明与开关，不做自动删除（避免误删）

### 9.4 建议你在文档里补充的“必须写清楚的契约清单”

- **写入者职责**：哪些字段 Memory 写、哪些字段 BP/CL 写（或只能写 cache）
- **并发策略**：锁文件位置、锁粒度、原子写方式、失败回滚方式
- **schema versioning**：向前/向后兼容原则、字段弃用策略
- **存储定位**：project-first / global 的优先级与合并规则
- **隐私策略**：是否保存原文、脱敏规则、保留期与清理
