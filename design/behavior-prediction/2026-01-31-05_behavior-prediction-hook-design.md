# 行为预测 Hook 设计文档

> **日期**: 2026-01-31
> **目标**: 设计一个 hook 机制，在会话结束时自动记录行为数据，解决 Cursor 无原生 hook 支持的问题

## 一、问题背景

### 1.1 当前痛点

Cursor 没有提供工具调用的 hook/回调机制，导致：

1. **记录依赖 AI 主动执行**：AI 需要在每次工具调用后"主动"执行 `record_action.py`
2. **容易遗漏**：AI 专注于主要任务时，容易"忘记"执行记录
3. **效率低下**：每次记录都需要一个 Shell 调用，增加延迟

### 1.2 用户提出的方案

创建一个 `hook.py` 脚本：
- 在规则文件中指导 AI 在会话结束时调用
- 在 hook 中批量写入本次会话的所有动作

## 二、方案设计

### 2.1 核心思路

```
┌─────────────────────────────────────────────────────────────┐
│                     完整会话生命周期                          │
├─────────────────────────────────────────────────────────────┤
│  【会话开始】                                                 │
│  1. AI 调用 hook.py --init 加载用户行为模式                   │
│  2. AI 获得用户的常见行为序列、偏好、习惯                      │
│  3. AI 可以主动预测用户意图，提高效率                          │
│                                                              │
│  【会话过程】                                                 │
│  4. AI 执行工具调用（Write, StrReplace, Shell 等）           │
│  5. AI 在内存中累积动作信息（不立即写入）                     │
│  6. AI 根据已加载的模式，主动提供建议                          │
│                                                              │
│  【会话结束】                                                 │
│  7. AI 调用 hook.py --finalize 批量写入动作                   │
│  8. 更新行为模式，返回预测建议                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 双向 Hook 设计

| Hook 类型 | 触发时机 | 功能 |
|-----------|----------|------|
| **Init Hook** | 会话开始 | 加载行为模式，提供给 AI 参考 |
| **Finalize Hook** | 会话结束 | 批量写入动作，更新行为模式 |

### 2.3 Init Hook 设计（会话开始）

#### 2.3.1 调用方式

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

#### 2.3.2 输出格式

```json
{
  "status": "success",
  "user_profile": {
    "total_sessions": 50,
    "total_actions": 500,
    "active_days": 15,
    "first_seen": "2026-01-15",
    "last_seen": "2026-01-31"
  },
  "behavior_patterns": {
    "common_sequences": [
      {
        "sequence": ["create_file[design_doc]", "create_file[api]", "run_test"],
        "count": 12,
        "description": "设计文档 → API 实现 → 测试"
      },
      {
        "sequence": ["edit_file[api]", "run_test", "git_commit"],
        "count": 8,
        "description": "修改 API → 测试 → 提交"
      }
    ],
    "top_transitions": [
      {"from": "create_file[api]", "to": "run_test", "probability": 0.85},
      {"from": "edit_file", "to": "run_test", "probability": 0.72},
      {"from": "run_test", "to": "git_commit", "probability": 0.68}
    ],
    "time_patterns": {
      "most_active_hours": [10, 14, 16],
      "avg_session_duration_minutes": 25
    }
  },
  "preferences": {
    "preferred_task_flow": "design → implement → test → commit",
    "common_file_types": [".py", ".js", ".md"],
    "common_purposes": ["api", "design_doc", "test"]
  },
  "suggestions": [
    "你通常在创建 API 后运行测试",
    "你习惯在测试通过后提交代码",
    "你的平均会话时长约 25 分钟"
  ]
}
```

#### 2.3.3 AI 如何使用

AI 在会话开始时获取这些信息后，可以：

1. **主动预测**：当用户创建 API 文件后，主动询问"要运行测试吗？"
2. **智能建议**：根据用户习惯，提供更符合用户风格的建议
3. **效率提升**：减少用户需要明确指示的次数

### 2.4 Finalize Hook 设计（会话结束）

#### 2.4.1 输入格式

```json
{
  "session_id": "2026-01-31-001",
  "start_time": "2026-01-31T10:00:00Z",
  "end_time": "2026-01-31T10:30:00Z",
  "actions": [
    {
      "type": "create_file",
      "tool": "Write",
      "timestamp": "2026-01-31T10:05:00Z",
      "details": {"file_path": "design/xxx.md"},
      "context": {"file_purpose": "design_doc", "task_stage": "design"}
    },
    {
      "type": "edit_file",
      "tool": "StrReplace",
      "timestamp": "2026-01-31T10:10:00Z",
      "details": {"file_path": "src/api/xxx.js"},
      "context": {"file_purpose": "api", "task_stage": "implement"}
    }
  ]
}
```

#### 2.4.2 Finalize Hook 功能

```python
# hook.py 主要功能
def session_hook(session_data):
    """
    会话结束时的 hook 处理
    
    1. 批量记录动作到日志
    2. 更新转移矩阵
    3. 记录会话统计
    4. 返回预测建议（可选）
    """
    pass
```

#### 2.4.3 输出格式

```json
{
  "status": "success",
  "recorded_count": 5,
  "session_stats": {
    "duration_minutes": 30,
    "actions_count": 5,
    "main_activities": ["design", "implement"]
  },
  "predictions": [
    {
      "next_action": "run_test",
      "probability": 0.85,
      "reason": "你通常在创建 API 后运行测试"
    }
  ]
}
```

### 2.5 规则文件设计

```markdown
---
description: 会话开始/结束时自动调用 hook
globs: ["**/*"]
alwaysApply: true
---

# Session Hook 规则

## 一、会话开始时

### 触发条件
- 每次新会话开始时（用户发送第一条消息）

### 调用命令
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

### 使用返回的信息
- 了解用户的行为模式和偏好
- 在适当时机主动提供建议
- 根据用户习惯调整交互方式

## 二、会话过程中

在执行工具调用时，**在内存中累积**动作信息，格式如下：

```json
{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {...},
  "context": {...}
}
```

**不需要立即执行记录脚本**，只需在内存中保存。

## 三、会话结束时

### 触发条件
- 用户说"谢谢"、"好的"、"结束"、"拜拜"
- 用户说"thanks"、"done"、"bye"
- 用户说"提交行为记录"

### 调用命令
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_id": "...",
  "start_time": "...",
  "end_time": "...",
  "actions": [...]
}'
```
```

## 三、需要增加和修改的内容

### 3.1 新增功能

| 功能 | 文件 | 说明 |
|------|------|------|
| **Init Hook** | `hook.py` | 添加 `--init` 参数支持，返回用户行为模式 |
| **行为模式提取** | `extract_patterns.py`（新增） | 从历史数据中提取行为模式 |
| **用户画像** | `user_profile.py`（新增） | 生成用户画像（统计信息） |

### 3.2 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `hook.py` | 添加 `--init` 和 `--finalize` 参数分支 |
| `session-hook.mdc` | 添加会话开始时的调用说明 |
| `utils.py` | 添加行为模式提取的辅助函数 |

### 3.3 新增数据结构

#### 3.3.1 行为模式文件（patterns/behavior_patterns.json）

```json
{
  "updated_at": "2026-01-31T10:00:00Z",
  "common_sequences": [
    {
      "sequence": ["create_file[design_doc]", "create_file[api]", "run_test"],
      "count": 12,
      "last_seen": "2026-01-31",
      "description": "设计文档 → API 实现 → 测试"
    }
  ],
  "context_transitions": {
    "create_file[api]": {
      "run_test": {"count": 20, "probability": 0.85},
      "edit_file[api]": {"count": 3, "probability": 0.12}
    }
  }
}
```

#### 3.3.2 用户画像文件（patterns/user_profile.json）

```json
{
  "updated_at": "2026-01-31T10:00:00Z",
  "stats": {
    "total_sessions": 50,
    "total_actions": 500,
    "active_days": 15,
    "first_seen": "2026-01-15",
    "last_seen": "2026-01-31"
  },
  "preferences": {
    "preferred_task_flow": ["design", "implement", "test", "commit"],
    "common_file_types": [".py", ".js", ".md"],
    "common_purposes": ["api", "design_doc", "test"]
  },
  "time_patterns": {
    "most_active_hours": [10, 14, 16],
    "avg_session_duration_minutes": 25
  }
}
```

### 3.4 实现优先级

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | Init Hook 基础功能 | 返回 top_transitions 和基本统计 |
| P1 | 行为序列提取 | 提取常见的 2-3 步序列 |
| P2 | 用户画像 | 生成完整的用户画像 |
| P3 | 时间模式分析 | 分析用户的时间偏好 |

## 四、可行性分析

### 4.1 优势

| 优势 | 说明 |
|------|------|
| **减少 Shell 调用** | 从每次工具调用后记录，变为会话结束时一次性记录 |
| **数据完整性** | 批量写入，减少遗漏风险 |
| **性能提升** | 减少 I/O 操作，提高响应速度 |
| **简单实现** | 不需要额外的 MCP Server 或扩展 |

### 4.2 劣势与风险

| 风险 | 说明 | 缓解措施 |
|------|------|----------|
| **AI 忘记调用** | AI 可能在会话结束时忘记调用 hook | 在规则中强调，使用明确的触发词 |
| **会话中断** | 用户直接关闭窗口，数据丢失 | 可选：每 N 个动作自动保存一次 |
| **内存累积** | 长会话可能累积大量数据 | 设置上限，超过时自动 flush |
| **时间戳不准** | AI 可能忘记记录时间戳 | 在 hook 中自动补充缺失的时间戳 |

### 4.3 可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **技术可行性** | ⭐⭐⭐⭐⭐ | 完全可行，只需 Python 脚本 |
| **实现复杂度** | ⭐⭐⭐⭐⭐ | 低，复用现有代码 |
| **可靠性** | ⭐⭐⭐⭐ | 依赖 AI 调用，有一定风险 |
| **性能** | ⭐⭐⭐⭐⭐ | 显著提升，减少 Shell 调用 |
| **用户体验** | ⭐⭐⭐⭐ | 无感知，自动执行 |

**总体评估**：**可行**，推荐实施。

## 五、实现方案

### 5.1 文件结构

```
skills/behavior-prediction/
├── scripts/
│   ├── hook.py              # 会话 hook 脚本（支持 --init 和 --finalize）
│   ├── extract_patterns.py  # 新增：行为模式提取
│   ├── user_profile.py      # 新增：用户画像生成
│   ├── record_action.py     # 保留：单个动作记录（兼容）
│   ├── batch_record_actions.py  # 保留：批量记录
│   ├── get_statistics.py    # 保留：获取统计
│   └── utils.py             # 更新：添加模式提取辅助函数
├── rules/
│   └── session-hook.mdc     # 会话 hook 规则
└── ...

# 数据目录（自动创建，位于项目或全局 AI 助手目录下）
# 项目级：<project>/.cursor/skills/behavior-prediction-data/
# 全局级：~/.cursor/skills/behavior-prediction-data/

<ai_dir>/skills/behavior-prediction-data/
├── actions/                 # 每日动作日志
│   └── 2026-01-31.json
├── sessions/                # 会话统计
│   └── 2026-01-31.json
└── patterns/                # 行为模式
    ├── transition_matrix.json
    ├── types_registry.json
    ├── behavior_patterns.json  # 新增
    └── user_profile.json       # 新增
```

### 5.2 Hook 脚本实现（更新版）

```python
#!/usr/bin/env python3
"""
Session Hook - 会话生命周期 hook 处理

功能：
1. --init: 会话开始时加载用户行为模式
2. --finalize: 会话结束时批量记录动作

用法：
  python3 hook.py --init
  python3 hook.py --finalize '{"actions": [...]}'
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from batch_record_actions import batch_record_actions
from get_statistics import get_statistics, get_all_statistics
from extract_patterns import extract_behavior_patterns
from user_profile import get_user_profile


def init_hook() -> dict:
    """
    会话开始时的 hook 处理
    
    Returns:
        {
            "status": "success",
            "user_profile": {...},
            "behavior_patterns": {...},
            "suggestions": [...]
        }
    """
    try:
        # 1. 获取用户画像
        user_profile = get_user_profile()
        
        # 2. 获取行为模式
        behavior_patterns = extract_behavior_patterns()
        
        # 3. 生成建议
        suggestions = generate_suggestions(user_profile, behavior_patterns)
        
        return {
            "status": "success",
            "user_profile": user_profile,
            "behavior_patterns": behavior_patterns,
            "suggestions": suggestions
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def finalize_hook(session_data: dict) -> dict:
    """
    会话结束时的 hook 处理
    
    Args:
        session_data: {"actions": [...], "start_time": "...", "end_time": "..."}
    
    Returns:
        {"status": "success", "recorded_count": N, ...}
    """
    # ... 现有的 session_hook 逻辑 ...
    pass


def generate_suggestions(user_profile: dict, behavior_patterns: dict) -> list:
    """根据用户画像和行为模式生成建议"""
    suggestions = []
    
    # 基于常见序列生成建议
    common_sequences = behavior_patterns.get("common_sequences", [])
    if common_sequences:
        top_seq = common_sequences[0]
        suggestions.append(f"你常见的工作流程：{top_seq.get('description', '')}")
    
    # 基于 top transitions 生成建议
    top_transitions = behavior_patterns.get("top_transitions", [])
    for t in top_transitions[:2]:
        from_action = t.get("from", "")
        to_action = t.get("to", "")
        prob = int(t.get("probability", 0) * 100)
        if prob >= 70:
            suggestions.append(f"你通常在 {from_action} 后执行 {to_action} ({prob}%)")
    
    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Session Hook")
    parser.add_argument("--init", action="store_true", help="会话开始时调用")
    parser.add_argument("--finalize", type=str, help="会话结束时调用，传入 JSON 数据")
    
    args = parser.parse_args()
    
    if args.init:
        result = init_hook()
    elif args.finalize:
        session_data = json.loads(args.finalize)
        result = finalize_hook(session_data)
    else:
        result = {"status": "error", "message": "请使用 --init 或 --finalize"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### 5.3 行为模式提取脚本（新增）

```python
#!/usr/bin/env python3
"""
extract_patterns.py - 从历史数据中提取行为模式
"""

import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, load_json, save_json, get_today


def extract_behavior_patterns() -> dict:
    """
    从历史数据中提取行为模式
    
    Returns:
        {
            "common_sequences": [...],
            "top_transitions": [...],
            "context_transitions": {...}
        }
    """
    # 1. 加载转移矩阵
    matrix_file = DATA_DIR / "patterns" / "transition_matrix.json"
    matrix = load_json(matrix_file, {"matrix": {}})
    
    # 2. 提取 top transitions（带上下文）
    top_transitions = extract_top_transitions(matrix)
    
    # 3. 提取常见序列（2-3 步）
    common_sequences = extract_common_sequences(matrix)
    
    # 4. 提取上下文转移
    context_transitions = extract_context_transitions(matrix)
    
    return {
        "common_sequences": common_sequences,
        "top_transitions": top_transitions,
        "context_transitions": context_transitions
    }


def extract_top_transitions(matrix: dict, limit: int = 10) -> list:
    """提取概率最高的转移"""
    transitions = []
    
    for from_action, to_actions in matrix.get("matrix", {}).items():
        for to_action, data in to_actions.items():
            # 优先使用带上下文的转移
            by_context = data.get("by_context", {})
            if by_context:
                for ctx_key, ctx_data in by_context.items():
                    transitions.append({
                        "from": f"{from_action}[{ctx_key.split('→')[0]}]",
                        "to": to_action,
                        "probability": ctx_data.get("probability", 0),
                        "count": ctx_data.get("count", 0),
                        "context_key": ctx_key
                    })
            else:
                transitions.append({
                    "from": from_action,
                    "to": to_action,
                    "probability": data.get("probability", 0),
                    "count": data.get("count", 0)
                })
    
    # 按概率排序，取 top N
    transitions.sort(key=lambda x: (x["probability"], x["count"]), reverse=True)
    return transitions[:limit]


def extract_common_sequences(matrix: dict, min_count: int = 3) -> list:
    """提取常见的 2-3 步序列"""
    sequences = []
    
    # 从转移矩阵中提取 2 步序列
    for from_action, to_actions in matrix.get("matrix", {}).items():
        for to_action, data in to_actions.items():
            count = data.get("count", 0)
            if count >= min_count:
                sequences.append({
                    "sequence": [from_action, to_action],
                    "count": count,
                    "description": f"{from_action} → {to_action}"
                })
    
    # 按次数排序
    sequences.sort(key=lambda x: x["count"], reverse=True)
    return sequences[:10]


def extract_context_transitions(matrix: dict) -> dict:
    """提取带上下文的转移统计"""
    context_transitions = {}
    
    for from_action, to_actions in matrix.get("matrix", {}).items():
        for to_action, data in to_actions.items():
            by_context = data.get("by_context", {})
            for ctx_key, ctx_data in by_context.items():
                from_ctx = ctx_key.split("→")[0]
                key = f"{from_action}[{from_ctx}]"
                
                if key not in context_transitions:
                    context_transitions[key] = {}
                
                context_transitions[key][to_action] = {
                    "count": ctx_data.get("count", 0),
                    "probability": ctx_data.get("probability", 0)
                }
    
    return context_transitions
```

### 5.4 用户画像脚本（新增）

```python
#!/usr/bin/env python3
"""
user_profile.py - 生成用户画像
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, load_json, save_json, get_today


def get_user_profile() -> dict:
    """
    生成用户画像
    
    Returns:
        {
            "stats": {...},
            "preferences": {...},
            "time_patterns": {...}
        }
    """
    # 1. 统计基本信息
    stats = calculate_stats()
    
    # 2. 分析偏好
    preferences = analyze_preferences()
    
    # 3. 分析时间模式
    time_patterns = analyze_time_patterns()
    
    return {
        "stats": stats,
        "preferences": preferences,
        "time_patterns": time_patterns
    }


def calculate_stats() -> dict:
    """计算基本统计"""
    actions_dir = DATA_DIR / "actions"
    sessions_dir = DATA_DIR / "sessions"
    
    total_actions = 0
    total_sessions = 0
    active_days = set()
    first_seen = None
    last_seen = None
    
    # 遍历动作日志
    if actions_dir.exists():
        for log_file in actions_dir.glob("*.json"):
            date = log_file.stem
            active_days.add(date)
            
            data = load_json(log_file, {"actions": []})
            total_actions += len(data.get("actions", []))
            
            if first_seen is None or date < first_seen:
                first_seen = date
            if last_seen is None or date > last_seen:
                last_seen = date
    
    # 遍历会话统计
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("*.json"):
            data = load_json(session_file, {"sessions": []})
            total_sessions += len(data.get("sessions", []))
    
    return {
        "total_sessions": total_sessions,
        "total_actions": total_actions,
        "active_days": len(active_days),
        "first_seen": first_seen,
        "last_seen": last_seen
    }


def analyze_preferences() -> dict:
    """分析用户偏好"""
    file_types = defaultdict(int)
    file_purposes = defaultdict(int)
    task_stages = defaultdict(int)
    
    actions_dir = DATA_DIR / "actions"
    if actions_dir.exists():
        for log_file in actions_dir.glob("*.json"):
            data = load_json(log_file, {"actions": []})
            for action in data.get("actions", []):
                context = action.get("context", {})
                
                if "file_type" in context:
                    file_types[context["file_type"]] += 1
                if "file_purpose" in context:
                    file_purposes[context["file_purpose"]] += 1
                if "task_stage" in context:
                    task_stages[context["task_stage"]] += 1
    
    return {
        "common_file_types": sorted(file_types.keys(), key=lambda x: file_types[x], reverse=True)[:5],
        "common_purposes": sorted(file_purposes.keys(), key=lambda x: file_purposes[x], reverse=True)[:5],
        "preferred_task_flow": sorted(task_stages.keys(), key=lambda x: task_stages[x], reverse=True)
    }


def analyze_time_patterns() -> dict:
    """分析时间模式"""
    hour_counts = defaultdict(int)
    session_durations = []
    
    # 分析动作时间
    actions_dir = DATA_DIR / "actions"
    if actions_dir.exists():
        for log_file in actions_dir.glob("*.json"):
            data = load_json(log_file, {"actions": []})
            for action in data.get("actions", []):
                timestamp = action.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        hour_counts[dt.hour] += 1
                    except:
                        pass
    
    # 分析会话时长
    sessions_dir = DATA_DIR / "sessions"
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("*.json"):
            data = load_json(session_file, {"sessions": []})
            for session in data.get("sessions", []):
                duration = session.get("duration_minutes", 0)
                if duration > 0:
                    session_durations.append(duration)
    
    # 计算最活跃的小时
    most_active_hours = sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:3]
    
    # 计算平均会话时长
    avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
    
    return {
        "most_active_hours": most_active_hours,
        "avg_session_duration_minutes": round(avg_duration, 1)
    }
```

### 5.5 规则文件实现（更新版）

```markdown
---
description: 会话结束时自动调用 hook 记录行为（替代实时记录）
globs: ["**/*"]
alwaysApply: true
---

# Session Hook 规则

> **版本**: v1.0.0
> **说明**: 在会话结束时批量记录行为，替代每次工具调用后的实时记录

## 一、会话过程中

### 1.1 累积动作信息

在执行工具调用（Write, StrReplace, Delete, Shell）时，**在内存中累积**动作信息：

```json
{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {
    "file_path": "文件路径（如适用）",
    "command": "命令（如适用）"
  },
  "context": {
    "file_type": ".py",
    "file_category": "source_code",
    "file_purpose": "api",
    "task_stage": "implement"
  }
}
```

### 1.2 动作分类

请根据工具调用的语义进行分类：

- 文件操作：create_file, edit_file, delete_file
- 代码相关：write_code, write_test, refactor, fix_bug
- 命令执行：run_test, run_build, run_server, install_dep
- Git 操作：git_add, git_commit, git_push

### 1.3 上下文推断

根据文件路径/命令内容推断上下文：

| 路径/命令 | file_purpose | task_stage |
|-----------|--------------|------------|
| design/*.md | design_doc | design |
| tests/*.py | test | test |
| src/api/*.js | api | implement |
| pytest, jest | - | test |

## 二、会话结束时

### 2.1 触发条件

当检测到以下信号时，调用 hook：

- 用户说"谢谢"、"好的"、"结束"、"拜拜"
- 用户说"thanks"、"done"、"bye"
- 用户说"提交行为记录"
- 用户明确表示任务完成

### 2.2 调用命令

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py '{
  "session_id": "2026-01-31-001",
  "start_time": "会话开始时间",
  "end_time": "当前时间",
  "actions": [
    {"type": "...", "tool": "...", ...},
    ...
  ]
}'
```

### 2.3 处理结果

Hook 返回后，可以向用户展示预测建议：

```
✅ 已记录 5 个动作

基于你的习惯，下次你可能想要：
→ 运行测试 (85%)
```

## 三、注意事项

1. **不要忘记调用 hook**：会话结束时必须调用
2. **时间戳**：尽量记录准确的时间戳
3. **上下文**：尽量提供上下文信息，提高预测精度
4. **静默执行**：hook 调用过程不需要向用户展示
```

## 六、与现有方案的对比

| 维度 | 实时记录（当前） | Session Hook（新） |
|------|------------------|-------------------|
| Shell 调用次数 | 每个动作 1 次 | 每个会话 1 次 |
| 数据完整性 | 可能遗漏 | 批量写入，更完整 |
| 性能 | 较慢 | 更快 |
| 实现复杂度 | 简单 | 简单 |
| 依赖 AI 调用 | 每次都依赖 | 只在结束时依赖 |

## 七、实施计划

### Phase 1：更新 hook.py（已完成部分）

1. ✅ 实现 `finalize_hook()` 函数
2. ⬜ 添加 `--init` 参数支持
3. ⬜ 实现 `init_hook()` 函数

### Phase 2：新增脚本

1. ⬜ 创建 `extract_patterns.py`
2. ⬜ 创建 `user_profile.py`
3. ⬜ 更新 `utils.py` 添加辅助函数

### Phase 3：更新规则文件

1. ⬜ 更新 `session-hook.mdc`
2. ⬜ 添加会话开始时的调用说明
3. ⬜ 添加 AI 如何使用行为模式的指导

### Phase 4：测试验证

1. ⬜ 编写 `test_extract_patterns.py`
2. ⬜ 编写 `test_user_profile.py`
3. ⬜ 更新 `test_hook.py` 添加 init 测试
4. ⬜ 手动测试完整会话流程

## 八、总结

双向 Hook 方案是一个**可行且推荐**的解决方案：

### 8.1 核心价值

| 功能 | 价值 |
|------|------|
| **Init Hook** | 让 AI 了解用户习惯，主动提供建议，提高效率 |
| **Finalize Hook** | 批量记录，减少 Shell 调用，保证数据完整 |

### 8.2 预期效果

1. **会话开始**：AI 知道用户的常见工作流程，可以主动预测
2. **会话过程**：AI 根据用户习惯，在适当时机提供建议
3. **会话结束**：自动记录行为，持续学习用户模式

### 8.3 实施建议

**立即实施**：
1. 更新 `hook.py` 支持 `--init`
2. 创建 `extract_patterns.py` 和 `user_profile.py`
3. 更新规则文件

**预期工作量**：约 2-3 小时
