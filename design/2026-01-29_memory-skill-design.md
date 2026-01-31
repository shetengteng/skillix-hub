# Memory Skill 设计文档

## 1. 概述

**Skill 名称**: memory  
**描述**: 为 Cursor 提供长期记忆能力，自动记录每日对话内容，并在新会话开始时根据用户问题检索相关历史上下文。

### 1.1 问题背景

Cursor 目前存在以下限制：
- 每次会话独立，无法记住历史对话
- 用户需要重复解释项目背景、偏好设置
- 无法积累学习用户的工作习惯和代码风格
- 跨会话的任务连续性差

### 1.2 解决方案

创建一个 Memory Skill，实现：
- 自动记录每日对话摘要
- 智能检索历史上下文
- 支持项目级和全局级记忆
- 用户可控的记忆管理

### 1.3 核心原则

- **零外部依赖**：不使用 sentence-transformers 等外部库
- **利用大模型能力**：让 Cursor 内置的大模型进行语义理解
- **代码数据分离**：Skill 代码可更新，用户数据永不覆盖
- **本地存储**：数据存储在本地，不上传到任何服务器

## 2. 核心功能

### 2.1 记忆记录（Memory Recording）

- **智能保存**: 大模型判断对话是否值得保存
- **用户控制**: 用户可以说"这次不保存"来跳过记录
- **每日文件**: 按日期组织，每天一个 Markdown 文件
- **结构化存储**: 包含时间戳、主题、关键信息、标签等

### 2.2 记忆检索（Memory Retrieval）

- **智能触发**: 大模型判断是否需要检索历史记忆
- **关键词 + 大模型**: 关键词快速筛选，大模型精准匹配
- **时间衰减**: 近期记忆权重更高
- **上下文注入**: 将相关记忆作为上下文提供给 AI

### 2.3 记忆管理（Memory Management）

- **查看记忆**: 用户可以查看历史记忆
- **删除记忆**: 用户可以删除特定记忆
- **搜索记忆**: 用户可以主动搜索历史记忆

## 3. 存储架构

### 3.1 目录结构（代码与数据分离）

**项目级记忆（优先）**：
```
<project>/.cursor/skills/
├── memory/                      # Skill 代码（可安全更新）
│   ├── SKILL.md                 # Skill 入口文件
│   ├── scripts/
│   │   ├── save_memory.py       # 保存记忆脚本
│   │   ├── search_memory.py     # 搜索记忆脚本
│   │   └── utils.py             # 工具函数
│   └── default_config.json      # 默认配置模板
│
└── memory-data/                 # 用户数据（永不覆盖）
    ├── daily/                   # 每日对话记录
    │   └── 2026-01-29.md
    ├── index/
    │   └── keywords.json        # 关键词索引
    └── config.json              # 用户自定义配置
```

**全局级记忆（备选）**：
```
~/.cursor/skills/
├── memory/                      # 全局 Skill 代码
└── memory-data/                 # 全局用户数据
```

### 3.2 搜索策略：本地优先，全局备选

Memory Skill 采用**项目级优先、全局级备选**的搜索策略：

```
1. 首先搜索项目级记忆 (<project>/.cursor/skills/memory-data/)
2. 如果项目级没有找到相关记忆，再搜索全局级记忆 (~/.cursor/skills/memory-data/)
3. 合并结果，项目级记忆权重更高
```

**搜索优先级**：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | 项目级记忆 | 当前项目的历史对话，最相关 |
| 2 | 全局级记忆 | 跨项目的通用记忆，如用户偏好 |

**保存策略**：

| 记忆类型 | 保存位置 | 示例 |
|----------|----------|------|
| 项目相关 | 项目级 | API 设计、项目配置、代码风格 |
| 通用偏好 | 全局级 | 编程语言偏好、工具选择 |

**配置选项**：

```json
{
  "storage": {
    "location": "project-first",  // "project-only", "global-only", "project-first"
    "retention_days": -1
  }
}
```

| 选项 | 说明 |
|------|------|
| `project-first` | 默认，项目级优先，全局级备选 |
| `project-only` | 只使用项目级记忆 |
| `global-only` | 只使用全局级记忆 |

### 3.3 更新策略

| 文件类型 | 位置 | 更新时处理 |
|----------|------|-----------|
| SKILL.md | memory/ | ✅ 覆盖 |
| scripts/*.py | memory/ | ✅ 覆盖 |
| daily/*.md | memory-data/ | ❌ 保留 |
| index/*.json | memory-data/ | ❌ 保留 |
| config.json | memory-data/ | ⚠️ 合并 |

### 3.4 每日记忆文件格式

```markdown
# 2026-01-29 对话记忆

## Session 1 - 10:30:45

### 主题
Memory Skill 设计讨论

### 关键信息
- 用户希望创建长期记忆功能
- 检索方式：关键词 + 大模型二次筛选

### 标签
#skill #memory #design

---
```

### 3.5 关键词索引格式

```json
{
  "version": "1.0",
  "updated_at": "2026-01-29T10:30:45Z",
  "entries": [
    {
      "id": "2026-01-29-001",
      "date": "2026-01-29",
      "session": 1,
      "keywords": ["memory", "skill", "design"],
      "summary": "Memory Skill 设计讨论",
      "tags": ["#skill", "#design"],
      "line_range": [3, 35]
    }
  ]
}
```

## 4. 检索方案

### 4.1 推荐方案：关键词 + 大模型二次筛选

> **核心洞察**: 既然 Skill 是在 Cursor 中运行，大模型本身就有强大的语义理解能力，完全不需要额外的 embedding 模型。

**流程**:
1. **第一步（快速筛选）**: 用关键词索引快速找出候选记忆（Top 10-20）
2. **第二步（精准匹配）**: 让大模型从候选中选出最相关的（Top 3-5）

**优点**:
- 零额外依赖，Skill 保持轻量
- 大模型语义理解能力远超 sentence-transformers
- 维护成本为零
- 实现简单，只需写好 Skill 指令

### 4.2 记忆权重机制（重点）

记忆的最终权重由多个因素综合计算：

```
最终权重 = 关键词匹配分 × 时间衰减系数 × 来源权重
```

#### 4.2.1 关键词匹配分

基于用户查询和记忆关键词的匹配程度：

```python
def keyword_score(query_keywords: set, memory_keywords: set) -> float:
    """计算关键词匹配分"""
    matched = query_keywords & memory_keywords
    if not matched:
        return 0
    # 匹配关键词数量 / 查询关键词数量
    return len(matched) / len(query_keywords)
```

| 匹配情况 | 分数 | 示例 |
|----------|------|------|
| 完全匹配 | 1.0 | 查询 ["API", "重构"]，记忆 ["API", "重构", "FastAPI"] |
| 部分匹配 | 0.5 | 查询 ["API", "重构"]，记忆 ["API", "设计"] |
| 无匹配 | 0 | 查询 ["API", "重构"]，记忆 ["数据库", "优化"] |

#### 4.2.2 时间衰减系数

近期记忆权重更高，使用指数衰减：

```python
def time_decay(days_ago: int, decay_rate: float = 0.95) -> float:
    """时间衰减系数: decay_rate^days_ago"""
    return decay_rate ** days_ago
```

| 天数 | 衰减系数 (rate=0.95) | 说明 |
|------|---------------------|------|
| 0 (今天) | 1.00 | 无衰减 |
| 1 | 0.95 | 衰减 5% |
| 7 | 0.70 | 衰减 30% |
| 30 | 0.21 | 衰减 79% |
| 90 | 0.01 | 几乎忽略 |

**配置调整**：
- `time_decay_rate = 0.95`：默认，每天衰减 5%
- `time_decay_rate = 0.99`：慢衰减，适合长期项目
- `time_decay_rate = 0.90`：快衰减，适合快速迭代项目

#### 4.2.3 来源权重

项目级记忆比全局级记忆更相关：

| 来源 | 默认权重 | 说明 |
|------|---------|------|
| 项目级记忆 | 1.0 | 当前项目的历史对话 |
| 全局级记忆 | 0.7 | 跨项目的通用记忆 |

#### 4.2.4 权重配置

所有权重参数都可以在配置文件中自定义：

```json
{
  "retrieval": {
    "time_decay_rate": 0.95,
    "source_weight": {
      "project": 1.0,
      "global": 0.7
    }
  }
}
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `time_decay_rate` | `0.95` | 时间衰减率，每天衰减 5% |
| `source_weight.project` | `1.0` | 项目级记忆权重 |
| `source_weight.global` | `0.7` | 全局级记忆权重 |

**调整建议**：
- 长期项目：`time_decay_rate = 0.99`（慢衰减）
- 快速迭代：`time_decay_rate = 0.90`（快衰减）
- 更重视全局记忆：`source_weight.global = 0.9`

#### 4.2.5 综合计算示例

```python
def calculate_final_score(
    query_keywords: set,
    memory: dict,
    is_project_level: bool
) -> float:
    """计算记忆的最终权重"""
    # 1. 关键词匹配分
    kw_score = keyword_score(query_keywords, set(memory["keywords"]))
    
    # 2. 时间衰减
    days_ago = (datetime.now() - datetime.strptime(memory["date"], "%Y-%m-%d")).days
    decay = time_decay(days_ago, decay_rate=0.95)
    
    # 3. 来源权重
    source_weight = 1.0 if is_project_level else 0.7
    
    # 最终权重
    return kw_score * decay * source_weight
```

**示例计算**：

| 记忆 | 关键词分 | 天数 | 衰减 | 来源 | 来源权重 | 最终分 |
|------|---------|------|------|------|---------|--------|
| A | 1.0 | 1 | 0.95 | 项目 | 1.0 | 0.95 |
| B | 0.5 | 0 | 1.00 | 项目 | 1.0 | 0.50 |
| C | 1.0 | 7 | 0.70 | 全局 | 0.7 | 0.49 |
| D | 0.8 | 30 | 0.21 | 项目 | 1.0 | 0.17 |

排序结果：A > B > C > D

### 4.3 为什么不用 sentence-transformers

| 对比维度 | sentence-transformers | 大模型方案 |
|----------|----------------------|-----------|
| 安装简易度 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 依赖管理 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 语义理解 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 维护成本 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 适合 Skill | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**唯一考虑 sentence-transformers 的场景**：
- 需要完全离线使用
- 记忆量极大（>10000条），需要毫秒级检索

## 5. 智能触发条件（核心入口）

> **核心思想**：意图识别是 Memory Skill 的入口，决定了整个 Skill 的行为。充分利用大模型的理解能力进行意图识别，而不是依赖简单的关键词匹配。

### 5.1 意图识别框架

#### 5.1.1 意图分类体系

| 意图类别 | 子类型 | 触发检索 | 触发保存 | 示例 |
|----------|--------|---------|---------|------|
| **延续性意图** | 时间延续 | ✅ | - | "继续昨天的工作" |
| | 话题延续 | ✅ | - | "上次说到哪了" |
| | 任务延续 | ✅ | - | "接着做那个功能" |
| **偏好相关** | 编码偏好 | ✅ | ✅ | "帮我写个函数" |
| | 工具偏好 | ✅ | ✅ | "我想用什么框架" |
| | 风格偏好 | ✅ | ✅ | "按我的习惯来" |
| **项目相关** | 项目配置 | ✅ | ✅ | "这个项目的 API" |
| | 架构决策 | ✅ | ✅ | "我们的技术栈" |
| | 代码约定 | ✅ | ✅ | "命名规范是什么" |
| **独立问题** | 通用知识 | ❌ | ❌ | "Python 怎么读文件" |
| | 语法查询 | ❌ | ❌ | "async/await 用法" |
| **新话题** | 明确切换 | ❌ | - | "换个话题" |
| | 无关问题 | ❌ | ❌ | "今天天气怎么样" |

#### 5.1.2 意图识别信号词

```python
# 高优先级：强信号词（高置信度触发）
STRONG_SIGNALS = {
    "continuation": [
        # 中文
        "继续", "接着", "上次", "之前", "昨天", "刚才",
        "我们讨论过", "你记得", "还记得", "提到过", "说过",
        # 英文
        "continue", "last time", "yesterday", "before", 
        "remember", "we discussed", "you mentioned", "as I said"
    ],
    "preference": [
        "我喜欢", "我习惯", "我通常", "按照我的风格",
        "我偏好", "我一般", "我的习惯是",
        "I prefer", "I usually", "my style"
    ],
    "project": [
        "这个项目", "我们的", "当前项目", "这里的",
        "项目里", "代码库", "我们的代码",
        "this project", "our codebase", "in our"
    ]
}

# 中优先级：弱信号词（需要结合上下文判断）
WEAK_SIGNALS = {
    "task": [
        "帮我写", "帮我实现", "生成一个", "创建一个",
        "写一个", "实现一下", "做一个",
        "help me", "create", "implement", "write"
    ],
    "query": [
        "怎么", "如何", "什么是", "为什么",
        "how to", "what is", "why"
    ]
}

# 排除信号：明确不需要记忆的场景
EXCLUDE_SIGNALS = [
    "换个话题", "新问题", "另外", "顺便问一下",
    "change topic", "new question", "by the way"
]
```

#### 5.1.3 意图识别算法

```python
def identify_intent(user_query: str, context: dict = None) -> dict:
    """
    识别用户意图
    
    Returns:
        {
            "intent_type": str,      # 意图类型
            "confidence": float,     # 置信度 0-1
            "should_retrieve": bool, # 是否需要检索
            "should_save": bool,     # 是否值得保存
            "signals_found": list,   # 匹配的信号词
            "reason": str            # 判断理由
        }
    """
    query_lower = user_query.lower()
    signals_found = []
    
    # 1. 检查排除信号（最高优先级）
    for signal in EXCLUDE_SIGNALS:
        if signal in query_lower:
            return {
                "intent_type": "new_topic",
                "confidence": 0.9,
                "should_retrieve": False,
                "should_save": False,
                "signals_found": [signal],
                "reason": f"检测到新话题信号: {signal}"
            }
    
    # 2. 检查强信号词
    for category, signals in STRONG_SIGNALS.items():
        for signal in signals:
            if signal in query_lower:
                signals_found.append(signal)
                return {
                    "intent_type": category,
                    "confidence": 0.9,
                    "should_retrieve": True,
                    "should_save": category in ["preference", "project"],
                    "signals_found": signals_found,
                    "reason": f"检测到{category}类强信号: {signal}"
                }
    
    # 3. 检查弱信号词（需要结合上下文）
    for category, signals in WEAK_SIGNALS.items():
        for signal in signals:
            if signal in query_lower:
                signals_found.append(signal)
    
    if signals_found:
        # 弱信号需要结合上下文判断
        is_new_session = context.get("is_new_session", True) if context else True
        return {
            "intent_type": "task",
            "confidence": 0.6,
            "should_retrieve": is_new_session,  # 新会话时检索
            "should_save": True,  # 任务类通常值得保存
            "signals_found": signals_found,
            "reason": f"检测到任务类弱信号，新会话={is_new_session}"
        }
    
    # 4. 无明显信号，使用大模型判断
    return {
        "intent_type": "unknown",
        "confidence": 0.5,
        "should_retrieve": context.get("is_new_session", True) if context else True,
        "should_save": False,
        "signals_found": [],
        "reason": "无明显信号，建议大模型进一步判断"
    }
```

### 5.2 检索触发决策树

```
用户输入问题
    ↓
┌─────────────────────────────────────┐
│ 1. 检查排除信号                      │
│    - "换个话题"、"新问题" → 不检索    │
└─────────────────────────────────────┘
    ↓ 无排除信号
┌─────────────────────────────────────┐
│ 2. 检查强信号词                      │
│    - 延续性信号 → 检索               │
│    - 偏好信号 → 检索                 │
│    - 项目信号 → 检索                 │
└─────────────────────────────────────┘
    ↓ 无强信号
┌─────────────────────────────────────┐
│ 3. 检查弱信号词                      │
│    - 任务类信号 + 新会话 → 检索      │
│    - 任务类信号 + 旧会话 → 不检索    │
└─────────────────────────────────────┘
    ↓ 无弱信号
┌─────────────────────────────────────┐
│ 4. 大模型兜底判断                    │
│    - 新会话 → 尝试检索               │
│    - 旧会话 → 不检索                 │
└─────────────────────────────────────┘
```

### 5.3 增强版 Skill 检索指令

```markdown
## Memory Skill - 智能检索触发

### 第一步：意图识别

分析用户问题，识别意图类型：

**用户问题**: {user_query}

**意图分类**：
1. **延续性意图**（必须检索）
   - 信号词：继续、上次、之前、昨天、我们讨论过、你记得
   - 示例："继续昨天的工作"、"上次说到哪了"

2. **偏好相关**（应该检索）
   - 信号词：我喜欢、我习惯、按照我的风格
   - 示例："帮我写个函数"（需要了解用户编码偏好）

3. **项目相关**（应该检索）
   - 信号词：这个项目、我们的、当前、项目里
   - 示例："这个项目的 API 怎么调用"

4. **独立问题**（不需要检索）
   - 特征：通用知识、语法查询、与项目无关
   - 示例："Python 怎么读文件"、"async/await 用法"

5. **新话题**（不需要检索）
   - 信号词：换个话题、新问题、另外
   - 示例："换个话题，我想问..."

### 第二步：执行决策

根据意图类型决定是否检索：

| 意图类型 | 决策 | 动作 |
|----------|------|------|
| 延续性意图 | ✅ 检索 | 执行 search_memory.py |
| 偏好相关 | ✅ 检索 | 执行 search_memory.py |
| 项目相关 | ✅ 检索 | 执行 search_memory.py |
| 独立问题 | ❌ 不检索 | 直接回答 |
| 新话题 | ❌ 不检索 | 直接回答 |

### 第三步：输出格式

```json
{
  "intent_type": "continuation|preference|project|independent|new_topic",
  "confidence": 0.9,
  "should_retrieve": true,
  "reason": "检测到延续性信号词：继续",
  "action": "执行 search_memory.py '继续 API 重构'"
}
```

如果 should_retrieve = true，执行检索后继续回答问题。
如果 should_retrieve = false，直接回答用户问题。
```

### 5.4 保存触发（价值判断）

| 对话类型 | 是否保存 | 原因 |
|----------|---------|------|
| 重要决策 | ✅ | "我们决定使用 FastAPI" |
| 偏好表达 | ✅ | "我喜欢用 TypeScript" |
| 项目配置 | ✅ | "API 前缀是 /api/v2" |
| 简单问答 | ❌ | "Python 怎么读文件" |
| 调试过程 | ❌ | 临时的错误排查 |
| 闲聊 | ❌ | 与项目无关的对话 |

**Skill 指令**：

```markdown
## 智能保存判断

对话结束时，请判断是否值得保存为记忆。

**值得保存**：重要决策、用户偏好、项目配置、待办计划、复杂方案
**不值得保存**：通用问答、临时调试、闲聊、重复内容

**输出判断结果**：
- 如果值得保存：提取关键信息，执行 save_memory.py
- 如果不值得保存：跳过保存
```

## 6. 工作流程

### 6.1 检索流程

```
用户输入问题 → 大模型判断是否需要检索 → 运行 search_memory.py 
→ 大模型从候选中选择最相关的 → 注入上下文 → 回答问题
```

### 6.2 保存流程

```
对话结束 → 大模型判断是否值得保存 → 提取主题/关键信息/标签 
→ 运行 save_memory.py → 更新索引
```

## 7. 配置选项

### 7.1 配置文件位置

用户配置文件位于 `.cursor/skills/memory-data/config.json`，首次使用时会从默认配置复制。

### 7.2 配置参数说明

```json
{
  "version": "1.0",
  "enabled": true,
  "auto_save": true,
  "auto_retrieve": true,
  "storage": {
    "retention_days": -1
  },
  "retrieval": {
    "max_candidates": 10,
    "max_results": 3,
    "search_scope_days": 30,
    "time_decay_rate": 0.95
  }
}
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | **总开关**，设置为 `false` 完全禁用 Memory Skill |
| `auto_save` | `true` | 是否自动保存对话记忆，设置为 `false` 则只能手动保存 |
| `auto_retrieve` | `true` | 是否自动检索历史记忆，设置为 `false` 则只能手动搜索 |
| `storage.retention_days` | `-1` | 记忆保留天数。`-1` 表示永久保留，设置正整数如 `90` 表示保留 90 天后自动清理 |
| `retrieval.max_candidates` | `10` | 关键词筛选返回的最大候选数量 |
| `retrieval.max_results` | `3` | 最终返回给用户的最相关记忆数量 |
| `retrieval.search_scope_days` | `30` | 检索范围限制，只搜索最近 N 天的记忆。设置 `-1` 表示搜索全部 |
| `retrieval.time_decay_rate` | `0.95` | 时间衰减率，每天衰减 5%（0.95），值越小衰减越快 |

### 7.3 配置示例

**完全禁用 Memory Skill**：
```json
{
  "enabled": false
}
```

**只启用手动保存，禁用自动保存**：
```json
{
  "auto_save": false,
  "auto_retrieve": true
}
```

**只启用手动搜索，禁用自动检索**：
```json
{
  "auto_save": true,
  "auto_retrieve": false
}
```

**永久保留所有记忆（默认）**：
```json
{
  "storage": { "retention_days": -1 }
}
```

**保留最近 90 天的记忆**：
```json
{
  "storage": { "retention_days": 90 }
}
```

**扩大检索范围到 60 天**：
```json
{
  "retrieval": { "search_scope_days": 60 }
}
```

**搜索全部历史记忆**：
```json
{
  "retrieval": { "search_scope_days": -1 }
}
```

## 8. 用户交互命令

| 命令 | 描述 |
|------|------|
| `记住这个` / `save this` | 手动保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |
| `查看今日记忆` | 查看今天的记忆 |
| `删除记忆: xxx` | 删除特定记忆 |

## 9. 潜在问题与解决方案

### 9.1 隐私与安全

> 由于数据完全存储在本地，不上传到任何服务器，隐私问题优先级较低。

**当前策略**: 暂不实现敏感信息过滤，用户对本地数据有完全控制权。

### 9.2 存储空间管理

**解决方案**:
- 设置保留天数（默认 90 天）
- 自动清理过期记忆

### 9.3 性能考虑

**解决方案**:
- 关键词快速筛选，减少大模型处理量
- 限制检索范围（默认最近 30 天）
- 时间衰减，优先返回近期记忆

### 9.4 并发与一致性

**解决方案**:
- 追加写入而非覆盖
- 每次操作更新索引

## 10. 示例场景

### 场景 1: 自动上下文注入

```
[用户]: 继续昨天的 API 重构工作

[Memory Skill]:
检索到相关记忆: 2026-01-28 - API 重构讨论，决定使用 FastAPI

[AI 响应]:
基于昨天的讨论，我们决定使用 FastAPI 替换 Flask。接下来需要...
```

### 场景 2: 偏好记忆

```
[历史记忆]: 用户偏好使用 TypeScript，喜欢函数式编程风格

[用户]: 帮我写一个数据处理函数

[AI 响应]: (自动使用 TypeScript + 函数式风格)
```

## 11. 技术选型：Node.js vs Python

### 11.1 对比评估

| 维度 | Python | Node.js | 胜出 |
|------|--------|---------|------|
| **Cursor 兼容性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Python |
| **用户环境普及度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Python |
| **脚本简洁性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Python |
| **JSON 处理** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Node.js |
| **文件操作** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 平手 |
| **异步能力** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Node.js |
| **依赖管理** | ⭐⭐⭐⭐ | ⭐⭐⭐ | Python |
| **跨平台** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 平手 |

### 11.2 详细分析

**Python 优势**：
1. **Cursor 原生支持**：Cursor 内置 Python 解释器，无需额外安装
2. **开发者普及度高**：大多数开发者电脑已安装 Python
3. **脚本简洁**：Python 语法简洁，适合写小型脚本
4. **标准库强大**：`json`、`pathlib`、`datetime` 等无需额外依赖

**Node.js 优势**：
1. **JSON 原生支持**：JavaScript 天然处理 JSON
2. **异步 I/O**：适合文件读写操作
3. **前端开发者友好**：前端开发者更熟悉

**Python 劣势**：
1. 版本碎片化（Python 2 vs 3）
2. 虚拟环境管理复杂

**Node.js 劣势**：
1. 需要单独安装 Node.js 运行时
2. `package.json` 依赖管理对简单脚本过重
3. 回调/Promise 语法对简单脚本略显复杂

### 11.3 推荐：Python

**理由**：

1. **零安装成本**：Cursor 已内置 Python，用户无需额外配置
2. **简单脚本更适合**：Memory Skill 的脚本都是简单的文件读写和 JSON 处理，Python 更简洁
3. **无依赖**：只使用 Python 标准库，无需 `pip install`
4. **Skill 生态一致性**：大多数 Cursor Skill 使用 Python

**代码对比**：

```python
# Python - 简洁
import json
from pathlib import Path

data = json.loads(Path("config.json").read_text())
```

```javascript
// Node.js - 相对繁琐
const fs = require('fs');
const path = require('path');

const data = JSON.parse(fs.readFileSync('config.json', 'utf8'));
```

### 11.4 备选方案

如果未来需要更复杂的功能（如实时监听、WebSocket），可以考虑：
- 核心脚本保持 Python
- 特定功能模块使用 Node.js

## 12. 自动触发优化

### 12.1 问题背景

#### 12.1.1 现象

用户在新会话中询问"上次我的 git 排名咋样"，Memory Skill 没有自动触发检索，导致 AI 无法获取历史记忆上下文。

#### 12.1.2 根本原因分析

1. **Skill 描述缺失**
   - 在 `<available_skills>` 中，Memory Skill 的描述为空
   - 其他 Skill 都有明确的触发描述，但 Memory Skill 没有
   ```xml
   <!-- 当前状态 - 无描述 -->
   <agent_skill fullPath="/Users/TerrellShe/.cursor/skills/memory/SKILL.md" />
   
   <!-- 对比：其他 Skill 有描述 -->
   <agent_skill fullPath="...qc-assistant/SKILL.md">辅助用户完成 QC 文档...</agent_skill>
   ```

2. **被动式设计**
   - SKILL.md 是指导性文档，描述了"何时应该检索"和"如何检索"
   - 但没有任何自动化机制强制执行意图识别
   - AI 需要主动阅读 SKILL.md 并按指示执行，这不是默认行为

3. **意图识别时机问题**
   - 意图识别应该在**对话开始时**立即执行
   - 但当前设计没有强制这一行为

### 12.2 解决方案

#### 方案 A：添加 Skill 触发描述（推荐）

修改 SKILL.md 的开头，添加标准的触发描述格式：

```markdown
# Memory Skill

为 Cursor 提供长期记忆能力，自动记录对话并在新会话时检索相关历史。当用户问题包含延续性词汇（上次、之前、昨天、继续、你记得）、偏好相关词汇（我喜欢、我习惯、按照我的风格）、或项目相关词汇（这个项目、我们的）时自动触发检索。
```

**优点**：
- 简单直接，只需修改一行
- 符合 Cursor Skill 的标准格式
- 让 AI 知道何时应该读取这个 Skill

**缺点**：
- 依赖 AI 主动识别触发词并读取 Skill
- 可能存在漏检

#### 方案 B：创建 Always Applied Rule（推荐配合方案 A）

创建 `.cursor/rules/memory-auto-retrieve.mdc`（或对应 AI 助手的规则文件）：

```markdown
# Memory Skill 自动记忆规则

## 一、检索触发（对话开始时）

**每次对话开始时**，检查用户的第一条消息是否包含以下信号词：

### 强信号词（必须触发检索）
- 延续性：继续、上次、之前、昨天、我们讨论过、你记得、continue、last time、yesterday
- 偏好：我喜欢、我习惯、按照我的风格、I prefer、my style
- 项目：这个项目、我们的、当前、项目里、this project、our codebase

### 排除信号词（不触发检索）
- 换个话题、新问题、另外、顺便问一下、change topic、new question

### 检索执行

如果检测到强信号词且无排除信号词：

1. 立即执行记忆检索：
   ```bash
   python3 <skills_dir>/memory/scripts/search_memory.py "用户问题关键词"
   ```

2. 将检索结果作为上下文注入回答

## 二、保存触发（对话结束时）

**对话结束时**，判断本次对话是否值得保存为记忆。

### 值得保存的内容
- **重要决策**：技术选型、架构决定（如"我们决定使用 FastAPI"）
- **用户偏好**：编码风格、工具选择（如"我喜欢用 TypeScript"）
- **项目配置**：API 设计、命名规范（如"API 前缀是 /api/v2"）
- **待办计划**：下一步任务、TODO 事项
- **复杂方案**：详细的实现方案、设计讨论

### 不值得保存的内容
- **通用问答**：Python 怎么读文件、async/await 用法
- **临时调试**：错误排查、临时修复
- **闲聊内容**：与项目无关的对话
- **重复内容**：已经保存过的相同信息

### 保存执行

如果判断值得保存：

1. 提取关键信息：
   - **主题**：对话的核心主题（一句话）
   - **关键信息**：重要的决策、偏好、配置等（列表形式）
   - **标签**：相关标签，以 # 开头

2. 执行保存：
   ```bash
   python3 <skills_dir>/memory/scripts/save_memory.py '{"topic": "主题", "key_info": ["要点1", "要点2"], "tags": ["#tag1", "#tag2"]}'
   ```

## 三、用户控制

用户可以通过以下命令控制记忆行为：

| 命令 | 效果 |
|------|------|
| `记住这个` / `save this` | 强制保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |

## 四、注意事项

- 检索失败不应阻塞正常对话
- 检索结果为空时正常继续对话
- 保存失败时提示用户但不影响对话
- 尊重用户的保存/不保存指令
```

**优点**：
- 作为 Always Applied Rule，每次对话都会被加载
- 强制执行意图识别（检索和保存）
- 不依赖 AI 主动读取 Skill
- 同时处理检索和保存两个方向

**缺点**：
- 增加了规则文件
- 需要 AI 正确解析和执行规则

### 12.3 推荐实施方案

**实施方案 A + B**：

1. 修改 SKILL.md 添加触发描述
2. 创建 Always Applied Rule

### 12.4 具体实施步骤

#### 步骤 1：修改 SKILL.md

在 `/Users/TerrellShe/.cursor/skills/memory/SKILL.md` 的第一行描述后添加触发说明。

#### 步骤 2：创建规则文件

通过 Memory Skill 提供的脚本自动创建规则文件：

```bash
# 在项目目录启用自动记忆
python3 <skills_dir>/memory/scripts/setup_auto_retrieve.py '{"action": "enable"}'

# 或在全局目录启用（对所有项目生效）
python3 <skills_dir>/memory/scripts/setup_auto_retrieve.py '{"action": "enable", "location": "global"}'
```

脚本会根据当前使用的 AI 助手类型（Cursor、Claude 等）自动创建对应格式的规则文件。

#### 步骤 3：验证

1. 开启新会话
2. 输入包含强信号词的问题（如"上次我们讨论了什么"）
3. 确认 Memory Skill 被触发并执行检索

### 12.5 预期效果

优化后，当用户在新会话中使用延续性词汇时：

```
[用户]: 上次我的 git 排名咋样

[AI 内部流程]:
1. 检测到强信号词"上次"
2. 自动执行 search_memory.py "git 排名"
3. 获取检索结果
4. 将结果作为上下文回答用户

[AI 响应]:
根据记忆记录，你在 metadata-server 项目的 Git 排名是第一名...
```

### 12.6 后续优化建议

1. **添加检索日志**：记录每次检索的触发原因和结果，便于调试
2. **优化关键词提取**：使用更智能的关键词提取算法
3. **支持多语言信号词**：扩展信号词列表支持更多语言
4. **添加置信度阈值**：低置信度时询问用户确认

## 13. 总结

Memory Skill 通过以下方式解决 Cursor 无长期记忆的问题：

1. **智能记录**: 大模型判断对话价值，自动保存有意义的内容
2. **智能检索**: 关键词快速筛选 + 大模型精准匹配
3. **用户可控**: 支持跳过保存、删除记忆、配置选项
4. **零依赖**: 不需要额外的 embedding 模型，充分利用大模型能力
5. **本地存储**: 数据安全，用户完全控制
6. **自动触发**: 通过 Skill 描述和 Always Applied Rule 实现自动意图识别和检索

这个 Skill 将显著提升 Cursor 的使用体验，让 AI 助手真正"记住"用户的偏好、项目背景和历史决策。
