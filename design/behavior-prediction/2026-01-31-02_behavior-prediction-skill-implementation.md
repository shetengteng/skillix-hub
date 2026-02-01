# 用户行为预测 Skill 实施方案

## 1. 概述

本文档基于 `2026-01-31_behavior-prediction-skill-design.md` 设计文档，提供详细的实施方案。

### 1.1 核心设计决策回顾

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 动作记录方式 | Always Applied Rule（核心）+ 会话结束处理（可选）+ 下次会话检查（兜底） | 实时完整，不依赖会话结束 |
| 动作分类 | 大模型分类（核心）+ 规则兜底 | 语义理解更准确 |
| 动作类型 | 开放式、可扩展 | 适应各种场景 |
| 预测决策 | 大模型综合判断 | 充分利用大模型能力 |
| 数据加载 | 按需加载 + 增量更新 | 性能优化 |
| 兼容性 | 支持多种 AI 助手 | Cursor, Claude, Copilot, Codeium 等 |

### 1.2 实施范围

**MVP 阶段实现**：
- ✅ 基础动作记录（Always Applied Rule）
- ✅ 大模型动作分类
- ✅ 转移矩阵统计
- ✅ 简单预测建议
- ✅ 会话结束批量处理

**后续阶段**：
- ⏳ 用户反馈学习（根据用户对预测的响应调整模型）
- ⏳ 自动执行（高置信度时自动执行预测动作）
- ⏳ 与 Memory Skill 协同

## 2. 兼容性

本 Skill 支持多种 AI 助手：

| AI 助手 | 目录名称 | 支持状态 |
|---------|----------|----------|
| Cursor | `.cursor` | ✅ 完全支持 |
| Claude | `.claude` | ✅ 完全支持 |
| GitHub Copilot | `.copilot` | ✅ 完全支持 |
| Codeium | `.codeium` | ✅ 完全支持 |
| 通用 AI | `.ai` | ✅ 完全支持 |

系统会自动检测当前使用的 AI 助手，并使用对应的目录存储数据。

## 3. 目录结构

```
~/.cursor/skills/  # 或 ~/.claude/skills/, ~/.ai/skills/ 等
├── behavior-prediction/              # Skill 代码目录
│   ├── SKILL.md                      # Skill 入口文件
│   ├── scripts/
│   │   ├── record_action.py          # 记录单个动作
│   │   ├── get_statistics.py         # 获取统计数据
│   │   ├── finalize_session.py       # 会话结束处理（可选）
│   │   ├── check_last_session.py     # 下次会话开始时检查（兜底）
│   │   ├── predict_next.py           # 预测下一步（可选）
│   │   └── utils.py                  # 工具函数
│   └── default_config.json           # 默认配置
│
└── behavior-prediction-data/         # 用户数据目录
    ├── actions/                      # 动作记录
    │   └── YYYY-MM-DD.json           # 每日动作日志
    ├── patterns/
    │   ├── transition_matrix.json    # 转移概率矩阵
    │   └── types_registry.json       # 动作类型注册表
    ├── stats/
    │   └── sessions.json             # 会话统计
    └── config.json                   # 用户配置

# 项目级规则文件
<project>/.cursor/rules/
└── behavior-recording.mdc            # Always Applied Rule
```

## 3. 核心文件实现

### 3.1 SKILL.md

```markdown
# Behavior Prediction Skill

为 Cursor 提供用户行为预测能力。学习用户的行为模式，当用户执行动作 A 后，自动预测并建议下一个可能的动作 B。

## 功能概述

1. **行为记录**：自动记录用户在 AI 助手中执行的动作
2. **模式学习**：分析行为序列，发现 A → B 的关联模式
3. **智能预测**：当用户执行动作 A 时，预测并建议动作 B

## 使用方式

### 自动模式

启用 Always Applied Rule 后，系统会自动：
- 记录每次工具调用
- 在适当时机提供预测建议

### 手动命令

| 命令 | 描述 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `预测下一步` | 手动触发预测 |
| `清除行为记录` | 删除所有行为记录 |

## 预测建议

当完成一个动作后，如果系统有高置信度的预测，会显示建议：

```
✨ 基于你的习惯，你可能想要：
→ 运行测试 (置信度: 85%)

要执行吗？[Y/n]
```

## 配置

配置文件位于 `~/.cursor/skills/behavior-prediction-data/config.json`

```json
{
  "enabled": true,
  "prediction": {
    "enabled": true,
    "suggest_threshold": 0.5,
    "auto_execute_threshold": 0.95
  },
  "recording": {
    "enabled": true,
    "retention_days": 90
  }
}
```

## 脚本说明

### record_action.py

记录单个动作到今日日志，并更新转移矩阵。

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {...}
}'
```

### get_statistics.py

获取预测所需的统计数据。

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py '{
  "current_action": "动作类型"
}'
```

### finalize_session.py

会话结束时的批量处理。

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/finalize_session.py '{
  "actions_summary": [...],
  "start_time": "...",
  "end_time": "..."
}'
```

## 会话开始检查

每次新会话开始时，执行检查确保数据完整：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py
```

这个脚本会：
1. 检查上次会话是否正常结束
2. 如果转移矩阵需要更新，自动重新计算
3. 每天只执行一次，避免重复检查

## 隐私说明

- 所有数据存储在本地
- 不上传任何信息到服务器
- 用户可以随时删除数据
```

### 3.2 Always Applied Rule (behavior-recording.mdc)

```markdown
---
description: 自动记录用户行为，用于行为预测 Skill
globs: ["**/*"]
alwaysApply: true
---

# 行为记录规则

## 一、动作记录

在执行以下工具调用**完成后**，自动记录动作。

### 需要记录的工具

| 工具 | 记录条件 |
|------|----------|
| Write | 总是记录 |
| StrReplace | 总是记录 |
| Delete | 总是记录 |
| Shell | 命令执行完成后记录 |

### 动作分类

请根据工具调用的语义进行分类，**不限于以下类型**：

**常见类型参考**：
- 文件操作：create_file, edit_file, delete_file
- 代码相关：write_code, write_test, refactor, fix_bug
- 命令执行：run_test, run_build, run_server, install_dep
- Git 操作：git_add, git_commit, git_push, git_pull

**分类要求**：
1. 理解语义，不只看关键词
2. 结合用户消息理解意图
3. 可以创建新类型（如 train_model, deploy_app）
4. 输出置信度

### 记录执行

工具调用完成后，执行：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "分类结果",
  "tool": "工具名称",
  "timestamp": "当前ISO8601时间",
  "details": {
    "file_path": "文件路径（如适用）",
    "command": "命令内容（如适用）",
    "exit_code": "退出码（如适用）"
  },
  "classification": {
    "confidence": 0.95,
    "is_new_type": false,
    "reason": "分类理由"
  }
}'
```

### 记录示例

**示例 1：创建文件**

工具调用：Write("src/utils/helper.py", "...")

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "create_file",
  "tool": "Write",
  "timestamp": "2026-01-31T10:30:00Z",
  "details": {"file_path": "src/utils/helper.py"},
  "classification": {"confidence": 0.98, "is_new_type": false}
}'
```

**示例 2：运行测试**

工具调用：Shell("pytest tests/ -v")

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "run_test",
  "tool": "Shell",
  "timestamp": "2026-01-31T10:35:00Z",
  "details": {"command": "pytest tests/ -v", "exit_code": 0},
  "classification": {"confidence": 0.95, "is_new_type": false}
}'
```

**示例 3：新类型（机器学习训练）**

工具调用：Shell("python train.py --epochs 100")

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "train_model",
  "tool": "Shell",
  "timestamp": "2026-01-31T10:40:00Z",
  "details": {"command": "python train.py --epochs 100", "exit_code": 0},
  "classification": {
    "confidence": 0.85,
    "is_new_type": true,
    "description": "训练机器学习模型"
  }
}'
```

## 二、预测建议

### 触发时机

在以下情况下触发预测：
1. 完成一个"重要"动作后（create_file, edit_file, write_code 等）
2. 用户明确请求预测

### 预测流程

1. **获取统计数据**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py '{
  "current_action": "刚完成的动作类型"
}'
```

2. **分析并决策**：

根据返回的统计数据，综合判断：
- 历史概率
- 样本量
- 当前上下文
- 最近行为模式

3. **生成建议**（如果置信度 > 0.5）：

使用自然、友好的语言，根据置信度调整语气：
- > 0.9：肯定语气，如"我来帮你运行测试"
- 0.7-0.9：建议语气，如"要运行测试验证一下吗？"
- 0.5-0.7：询问语气，如"你可能想运行测试？"

## 三、会话结束处理（可选）

> **注意**：由于实时记录已经保证了数据完整性，会话结束处理是**可选的**。即使没有执行，数据也是完整的。

### 触发时机

**如果有机会执行**（用户等待 AI 响应后再离开）：
- 用户说"谢谢"、"好的"、"结束"、"拜拜"
- 用户说"thanks"、"done"、"bye"

### 处理内容

会话结束处理只做"锦上添花"的工作：
1. 记录会话统计
2. 验证数据一致性

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/finalize_session.py '{
  "actions_summary": [
    {"type": "create_file", "tool": "Write", "file": "..."},
    {"type": "edit_file", "tool": "StrReplace", "file": "..."},
    {"type": "run_test", "tool": "Shell", "command": "..."}
  ],
  "start_time": "会话开始时间",
  "end_time": "当前时间"
}'
```

### 重要说明

**即使会话结束处理没有执行，数据也是完整的**，因为：
- 每次工具调用后都会立即记录（Always Applied Rule）
- 转移矩阵是实时更新的
- 下次会话开始时会自动检查和修复

## 四、注意事项

1. **记录失败不阻塞**：如果脚本执行失败，继续正常流程
2. **静默执行**：记录过程不向用户显示
3. **频率控制**：相同动作 5 秒内不重复记录
4. **本地存储**：所有数据存储在本地，用户完全控制
```

### 3.3 Python 脚本实现

#### 3.3.1 utils.py

```python
#!/usr/bin/env python3
"""工具函数"""

import json
from datetime import datetime
from pathlib import Path

# 数据目录
DATA_DIR = Path.home() / ".cursor" / "skills" / "behavior-prediction-data"
SKILL_DIR = Path.home() / ".cursor" / "skills" / "behavior-prediction"


def ensure_data_dirs():
    """确保数据目录存在"""
    (DATA_DIR / "actions").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "patterns").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "stats").mkdir(parents=True, exist_ok=True)


def load_json(file_path: Path, default: dict = None) -> dict:
    """加载 JSON 文件"""
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default or {}
    return default or {}


def save_json(file_path: Path, data: dict):
    """保存 JSON 文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_today() -> str:
    """获取今天的日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().isoformat() + "Z"


def load_config() -> dict:
    """加载用户配置"""
    config_file = DATA_DIR / "config.json"
    default_config = load_json(SKILL_DIR / "default_config.json", {
        "enabled": True,
        "prediction": {
            "enabled": True,
            "suggest_threshold": 0.5,
            "auto_execute_threshold": 0.95
        },
        "recording": {
            "enabled": True,
            "retention_days": 90
        }
    })
    
    user_config = load_json(config_file, {})
    
    # 合并配置
    return {**default_config, **user_config}


def load_transition_matrix() -> dict:
    """加载转移矩阵"""
    matrix_file = DATA_DIR / "patterns" / "transition_matrix.json"
    return load_json(matrix_file, {
        "version": "1.0",
        "matrix": {},
        "total_transitions": 0
    })


def save_transition_matrix(matrix: dict):
    """保存转移矩阵"""
    matrix["updated_at"] = get_timestamp()
    matrix_file = DATA_DIR / "patterns" / "transition_matrix.json"
    save_json(matrix_file, matrix)


def load_types_registry() -> dict:
    """加载动作类型注册表"""
    registry_file = DATA_DIR / "patterns" / "types_registry.json"
    return load_json(registry_file, {
        "version": "1.0",
        "types": {}
    })


def save_types_registry(registry: dict):
    """保存动作类型注册表"""
    registry["updated_at"] = get_timestamp()
    registry_file = DATA_DIR / "patterns" / "types_registry.json"
    save_json(registry_file, registry)


def register_action_type(action_type: str, description: str = "", is_new: bool = False):
    """注册动作类型"""
    registry = load_types_registry()
    
    if action_type not in registry["types"]:
        registry["types"][action_type] = {
            "description": description,
            "source": "auto_generated" if is_new else "predefined",
            "first_seen": get_today(),
            "count": 0
        }
    
    registry["types"][action_type]["count"] = registry["types"][action_type].get("count", 0) + 1
    registry["types"][action_type]["last_seen"] = get_today()
    
    save_types_registry(registry)
```

#### 3.3.2 record_action.py

```python
#!/usr/bin/env python3
"""记录单个动作"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, ensure_data_dirs, load_json, save_json,
    get_today, get_timestamp, load_transition_matrix,
    save_transition_matrix, register_action_type
)


def record_action(action_data: dict) -> dict:
    """
    记录一个动作到今日日志，并更新转移矩阵
    
    Args:
        action_data: {
            "type": "动作类型",
            "tool": "工具名称",
            "timestamp": "ISO8601时间",
            "details": {...},
            "classification": {
                "confidence": 0.95,
                "is_new_type": false,
                "description": "类型描述（新类型时）"
            }
        }
    
    Returns:
        {"status": "success|skipped|error", ...}
    """
    try:
        ensure_data_dirs()
        
        # 获取动作类型
        action_type = action_data.get("type", "unknown")
        
        # 今日日志文件
        today = get_today()
        log_file = DATA_DIR / "actions" / f"{today}.json"
        
        # 读取或创建日志
        log_data = load_json(log_file, {"date": today, "actions": []})
        
        # 频率控制：5秒内相同动作不重复记录
        if log_data["actions"]:
            last_action = log_data["actions"][-1]
            if last_action.get("type") == action_type:
                try:
                    last_time = datetime.fromisoformat(
                        last_action.get("timestamp", "").replace("Z", "+00:00")
                    )
                    now = datetime.now().astimezone()
                    if (now - last_time).total_seconds() < 5:
                        return {"status": "skipped", "reason": "duplicate within 5s"}
                except (ValueError, TypeError):
                    pass
        
        # 生成动作 ID
        action_id = f"{today}-{len(log_data['actions']) + 1:03d}"
        
        # 构建动作记录
        action_record = {
            "id": action_id,
            "type": action_type,
            "tool": action_data.get("tool", "unknown"),
            "timestamp": action_data.get("timestamp", get_timestamp()),
            "details": action_data.get("details", {}),
        }
        
        # 如果有分类信息，添加到记录
        if "classification" in action_data:
            action_record["classification"] = action_data["classification"]
        
        # 追加到日志
        log_data["actions"].append(action_record)
        save_json(log_file, log_data)
        
        # 注册动作类型（如果是新类型）
        classification = action_data.get("classification", {})
        if classification.get("is_new_type"):
            register_action_type(
                action_type,
                description=classification.get("description", ""),
                is_new=True
            )
        else:
            register_action_type(action_type)
        
        # 更新转移矩阵（如果有前一个动作）
        if len(log_data["actions"]) >= 2:
            prev_action = log_data["actions"][-2]["type"]
            update_transition(prev_action, action_type)
        
        return {
            "status": "success",
            "action_id": action_id,
            "type": action_type
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_transition(from_action: str, to_action: str):
    """更新转移矩阵"""
    matrix = load_transition_matrix()
    
    # 初始化
    if from_action not in matrix["matrix"]:
        matrix["matrix"][from_action] = {}
    
    if to_action not in matrix["matrix"][from_action]:
        matrix["matrix"][from_action][to_action] = {"count": 0}
    
    # 更新计数
    matrix["matrix"][from_action][to_action]["count"] += 1
    matrix["total_transitions"] += 1
    
    # 重新计算该行的概率
    total = sum(t["count"] for t in matrix["matrix"][from_action].values())
    for action, data in matrix["matrix"][from_action].items():
        data["probability"] = round(data["count"] / total, 3)
    
    save_transition_matrix(matrix)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing action data"}))
        sys.exit(1)
    
    try:
        action_data = json.loads(sys.argv[1])
        result = record_action(action_data)
        print(json.dumps(result, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
```

#### 3.3.3 get_statistics.py

```python
#!/usr/bin/env python3
"""获取预测所需的统计数据"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, load_json, get_today,
    load_transition_matrix, load_config
)


def get_statistics(current_action: str) -> dict:
    """
    获取预测所需的统计数据
    
    Args:
        current_action: 当前动作类型
    
    Returns:
        {
            "current_action": "动作类型",
            "transitions": {...},
            "recent_sequence": [...],
            "context": {...},
            "config": {...}
        }
    """
    try:
        # 加载转移矩阵
        matrix = load_transition_matrix()
        
        # 获取当前动作的转移统计
        transitions = matrix.get("matrix", {}).get(current_action, {})
        
        # 获取最近的动作序列
        recent_sequence = get_recent_actions(limit=10)
        
        # 收集上下文信息
        context = collect_context()
        
        # 加载配置
        config = load_config()
        
        return {
            "status": "success",
            "current_action": current_action,
            "transitions": transitions,
            "total_samples": sum(t.get("count", 0) for t in transitions.values()),
            "recent_sequence": recent_sequence,
            "context": context,
            "prediction_config": config.get("prediction", {})
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_recent_actions(limit: int = 10) -> list:
    """获取最近的动作序列"""
    today = get_today()
    log_file = DATA_DIR / "actions" / f"{today}.json"
    
    log_data = load_json(log_file, {"actions": []})
    actions = log_data.get("actions", [])
    
    # 返回最近的动作类型
    recent = [a.get("type", "unknown") for a in actions[-limit:]]
    return recent


def collect_context() -> dict:
    """收集当前上下文信息"""
    context = {
        "date": get_today(),
        "has_data": True
    }
    
    # 可以扩展更多上下文信息
    # 如：当前项目类型、最近修改的文件类型等
    
    return context


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing input data"}))
        sys.exit(1)
    
    try:
        input_data = json.loads(sys.argv[1])
        current_action = input_data.get("current_action", "")
        
        if not current_action:
            print(json.dumps({"status": "error", "message": "Missing current_action"}))
            sys.exit(1)
        
        result = get_statistics(current_action)
        print(json.dumps(result, ensure_ascii=False))
    
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
```

#### 3.3.4 finalize_session.py

```python
#!/usr/bin/env python3
"""会话结束时的批量处理"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, ensure_data_dirs, load_json, save_json,
    get_today, get_timestamp, load_transition_matrix,
    save_transition_matrix
)


def finalize_session(session_data: dict) -> dict:
    """
    会话结束时的处理
    
    Args:
        session_data: {
            "actions_summary": [...],
            "start_time": "...",
            "end_time": "..."
        }
    
    Returns:
        {"status": "success|error", ...}
    """
    try:
        ensure_data_dirs()
        
        actions_summary = session_data.get("actions_summary", [])
        
        if not actions_summary:
            return {"status": "success", "message": "No actions to process"}
        
        # 1. 补充遗漏的动作记录
        supplemented = supplement_missing_actions(actions_summary)
        
        # 2. 更新转移矩阵（基于完整序列）
        update_transitions_from_sequence(actions_summary)
        
        # 3. 记录会话统计
        record_session_stats(session_data, len(actions_summary))
        
        return {
            "status": "success",
            "actions_count": len(actions_summary),
            "supplemented": supplemented,
            "message": f"Session finalized with {len(actions_summary)} actions"
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def supplement_missing_actions(actions_summary: list) -> int:
    """补充遗漏的动作记录"""
    today = get_today()
    log_file = DATA_DIR / "actions" / f"{today}.json"
    
    existing = load_json(log_file, {"date": today, "actions": []})
    existing_types = set()
    
    # 收集已记录的动作类型（简化检查）
    for action in existing.get("actions", []):
        existing_types.add(action.get("type", ""))
    
    supplemented = 0
    
    for action in actions_summary:
        action_type = action.get("type", "")
        
        # 简单检查：如果类型完全不在已记录中，补充记录
        # 实际可以更精细（检查时间戳、文件路径等）
        if action_type and action_type not in existing_types:
            action_record = {
                "id": f"{today}-{len(existing['actions']) + 1:03d}",
                "type": action_type,
                "tool": action.get("tool", "unknown"),
                "timestamp": get_timestamp(),
                "details": action.get("details", {}),
                "source": "session_finalize"
            }
            existing["actions"].append(action_record)
            existing_types.add(action_type)
            supplemented += 1
    
    if supplemented > 0:
        save_json(log_file, existing)
    
    return supplemented


def update_transitions_from_sequence(actions: list):
    """根据动作序列更新转移矩阵"""
    if len(actions) < 2:
        return
    
    matrix = load_transition_matrix()
    
    # 遍历序列，更新转移
    for i in range(len(actions) - 1):
        from_action = actions[i].get("type", "unknown")
        to_action = actions[i + 1].get("type", "unknown")
        
        if from_action == "unknown" or to_action == "unknown":
            continue
        
        if from_action not in matrix["matrix"]:
            matrix["matrix"][from_action] = {}
        
        if to_action not in matrix["matrix"][from_action]:
            matrix["matrix"][from_action][to_action] = {"count": 0}
        
        # 会话结束时的更新权重较低（0.5），避免与实时记录重复计数
        matrix["matrix"][from_action][to_action]["count"] += 0.5
        matrix["total_transitions"] += 0.5
    
    # 重新计算所有概率
    for from_action in matrix["matrix"]:
        total = sum(t["count"] for t in matrix["matrix"][from_action].values())
        if total > 0:
            for action, data in matrix["matrix"][from_action].items():
                data["probability"] = round(data["count"] / total, 3)
    
    save_transition_matrix(matrix)


def record_session_stats(session_data: dict, actions_count: int):
    """记录会话统计信息"""
    stats_file = DATA_DIR / "stats" / "sessions.json"
    
    stats = load_json(stats_file, {"sessions": [], "total_sessions": 0})
    
    session_record = {
        "date": get_today(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "actions_count": actions_count,
        "action_types": list(set(
            a.get("type", "unknown") 
            for a in session_data.get("actions_summary", [])
        ))
    }
    
    stats["sessions"].append(session_record)
    stats["total_sessions"] += 1
    
    # 只保留最近 100 条会话记录
    if len(stats["sessions"]) > 100:
        stats["sessions"] = stats["sessions"][-100:]
    
    save_json(stats_file, stats)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing session data"}))
        sys.exit(1)
    
    try:
        session_data = json.loads(sys.argv[1])
        result = finalize_session(session_data)
        print(json.dumps(result, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
```

#### 3.3.5 check_last_session.py（下次会话开始时检查）

```python
#!/usr/bin/env python3
"""检查上次会话是否正常结束，如果没有则补充处理"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, load_json, save_json, get_today,
    load_transition_matrix, save_transition_matrix
)


def check_last_session() -> dict:
    """
    检查上次会话是否正常结束
    
    Returns:
        {"status": "success", "action": "none|processed", ...}
    """
    try:
        stats_file = DATA_DIR / "stats" / "sessions.json"
        stats = load_json(stats_file, {"sessions": [], "last_check": None})
        
        today = get_today()
        last_check = stats.get("last_check")
        
        # 如果今天已经检查过，跳过
        if last_check == today:
            return {"status": "success", "action": "none", "reason": "Already checked today"}
        
        # 更新检查时间
        stats["last_check"] = today
        save_json(stats_file, stats)
        
        # 检查是否需要重新计算转移矩阵
        # （如果昨天的数据没有被正确处理）
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_log = DATA_DIR / "actions" / f"{yesterday}.json"
        
        if yesterday_log.exists():
            # 验证转移矩阵是否包含昨天的数据
            matrix = load_transition_matrix()
            matrix_updated = matrix.get("updated_at", "")
            
            # 如果矩阵最后更新时间早于昨天，重新计算
            if matrix_updated < yesterday:
                recalculate_transition_matrix()
                return {
                    "status": "success",
                    "action": "processed",
                    "reason": "Recalculated transition matrix"
                }
        
        return {"status": "success", "action": "none", "reason": "No action needed"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def recalculate_transition_matrix():
    """重新计算转移矩阵（基于所有日志）"""
    actions_dir = DATA_DIR / "actions"
    
    if not actions_dir.exists():
        return
    
    # 收集所有转移
    all_transitions = {}
    total = 0
    
    # 遍历所有日志文件
    for log_file in sorted(actions_dir.glob("*.json")):
        log_data = load_json(log_file, {"actions": []})
        actions = log_data.get("actions", [])
        
        # 遍历动作序列
        for i in range(len(actions) - 1):
            from_action = actions[i].get("type", "unknown")
            to_action = actions[i + 1].get("type", "unknown")
            
            if from_action == "unknown" or to_action == "unknown":
                continue
            
            if from_action not in all_transitions:
                all_transitions[from_action] = {}
            
            if to_action not in all_transitions[from_action]:
                all_transitions[from_action][to_action] = {"count": 0}
            
            all_transitions[from_action][to_action]["count"] += 1
            total += 1
    
    # 计算概率
    for from_action in all_transitions:
        row_total = sum(t["count"] for t in all_transitions[from_action].values())
        if row_total > 0:
            for to_action, data in all_transitions[from_action].items():
                data["probability"] = round(data["count"] / row_total, 3)
    
    # 保存
    matrix = {
        "version": "1.0",
        "matrix": all_transitions,
        "total_transitions": total,
        "updated_at": datetime.now().isoformat() + "Z",
        "recalculated": True
    }
    save_transition_matrix(matrix)


if __name__ == "__main__":
    result = check_last_session()
    print(json.dumps(result, ensure_ascii=False))
```

### 3.4 默认配置 (default_config.json)

```json
{
  "version": "1.0",
  "enabled": true,
  "prediction": {
    "enabled": true,
    "suggest_threshold": 0.5,
    "auto_execute_threshold": 0.95,
    "max_suggestions": 3
  },
  "recording": {
    "enabled": true,
    "retention_days": 90
  },
  "learning": {
    "enabled": true,
    "min_samples_for_prediction": 3
  }
}
```

## 4. 安装与部署

### 4.1 安装步骤

```bash
# 1. 创建 Skill 目录
mkdir -p ~/.cursor/skills/behavior-prediction/scripts
mkdir -p ~/.cursor/skills/behavior-prediction-data

# 2. 复制 Skill 文件
# 将上述文件复制到对应目录

# 3. 设置脚本可执行权限
chmod +x ~/.cursor/skills/behavior-prediction/scripts/*.py

# 4. 创建项目级 Rule（在项目目录中）
mkdir -p .cursor/rules
# 将 behavior-recording.mdc 复制到 .cursor/rules/
```

### 4.2 验证安装

```bash
# 测试脚本是否可执行
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"type": "test", "tool": "Shell"}'

# 应该输出类似：
# {"status": "success", "action_id": "2026-01-31-001", "type": "test"}
```

## 5. 使用流程

### 5.1 自动记录流程

```
1. 用户与 AI 对话
2. AI 执行工具调用（如 Write、Shell）
3. [Always Applied Rule 触发]
4. AI 分类动作类型
5. AI 调用 record_action.py 记录
6. 继续正常对话
```

### 5.2 预测建议流程

```
1. AI 完成一个"重要"动作
2. AI 调用 get_statistics.py 获取统计
3. AI 分析统计数据，判断是否建议
4. 如果置信度 > 0.5，显示建议
5. 用户选择接受或忽略
```

### 5.3 会话结束处理（重要）

> **问题**：在 Cursor 中，用户说"谢谢"等结束语后，对话可能直接结束，AI 没有机会执行会话结束处理。

#### 5.3.1 问题分析

| 场景 | AI 能否执行结束处理 |
|------|-------------------|
| 用户说"谢谢"后等待 AI 响应 | ✅ 可以 |
| 用户说"谢谢"后直接关闭 | ❌ 不可以 |
| 用户直接关闭窗口 | ❌ 不可以 |
| 用户长时间不操作 | ❌ 不可以 |

#### 5.3.2 解决方案

**方案 A：实时记录为主，会话结束为辅（推荐）**

核心思想：**不依赖会话结束处理**，实时记录已经足够完整。

```
┌─────────────────────────────────────────────────────────────┐
│ Always Applied Rule（主要）                                  │
│ - 每次工具调用后立即记录                                      │
│ - 立即更新转移矩阵                                           │
│ - 数据实时完整                                               │
└─────────────────────────────────────────────────────────────┘
                           +
┌─────────────────────────────────────────────────────────────┐
│ 会话结束处理（补充，可选）                                     │
│ - 如果 AI 有机会执行，则补充处理                              │
│ - 如果没有机会，数据也是完整的                                │
└─────────────────────────────────────────────────────────────┘
```

**实施要点**：
1. 确保 `record_action.py` 每次都更新转移矩阵
2. 会话结束处理只做"锦上添花"的工作
3. 即使没有会话结束处理，数据也是完整的

**方案 B：定时任务补充处理**

使用系统定时任务（如 cron）定期处理未完成的会话。

```bash
# crontab -e
# 每小时运行一次，处理未完成的会话
0 * * * * python3 ~/.cursor/skills/behavior-prediction/scripts/cleanup_sessions.py
```

**cleanup_sessions.py**：
```python
#!/usr/bin/env python3
"""定期清理和处理未完成的会话"""

def cleanup_sessions():
    """
    1. 检查今日日志，确保转移矩阵是最新的
    2. 清理过期数据
    """
    # 重新计算转移矩阵（基于所有日志）
    recalculate_transition_matrix()
    
    # 清理过期数据
    cleanup_old_data(retention_days=90)
```

**方案 C：下次会话开始时补充处理**

在新会话开始时，检查上次会话是否正常结束，如果没有则补充处理。

```markdown
## 会话开始检查（添加到 SKILL.md）

### 会话开始时

检查上次会话是否正常结束：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py
```

如果上次会话未正常结束，脚本会自动补充处理。
```

#### 5.3.3 推荐组合方案

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 实时记录（核心，必须）                                     │
│    - Always Applied Rule                                     │
│    - 每次工具调用后立即记录和更新                             │
└─────────────────────────────────────────────────────────────┘
                           +
┌─────────────────────────────────────────────────────────────┐
│ 2. 会话结束处理（可选，如果有机会执行）                        │
│    - 检测结束信号时执行                                       │
│    - 补充遗漏，更新统计                                       │
└─────────────────────────────────────────────────────────────┘
                           +
┌─────────────────────────────────────────────────────────────┐
│ 3. 下次会话开始时检查（兜底）                                  │
│    - 检查上次会话是否正常结束                                 │
│    - 如果没有，补充处理                                       │
└─────────────────────────────────────────────────────────────┘
```

#### 5.3.4 修改后的会话结束处理

```markdown
## 会话结束处理（修改版）

### 触发时机

**主动触发**（如果有机会）：
- 用户说"谢谢"、"好的"、"结束"等
- 用户说"thanks"、"done"、"bye"等

**被动触发**（兜底）：
- 下次会话开始时，检查上次会话

### 处理内容

由于实时记录已经保证了数据完整性，会话结束处理只做：
1. 记录会话统计（可选）
2. 验证数据一致性（可选）

### 注意

**即使会话结束处理没有执行，数据也是完整的**，因为：
- 每次工具调用后都会立即记录
- 转移矩阵是实时更新的
```

## 6. 测试计划

### 6.1 单元测试

| 测试项 | 描述 |
|--------|------|
| record_action | 测试动作记录功能 |
| get_statistics | 测试统计数据获取 |
| finalize_session | 测试会话结束处理 |
| 转移矩阵更新 | 测试概率计算正确性 |
| 频率控制 | 测试 5 秒去重 |

### 6.2 集成测试

| 测试场景 | 描述 |
|----------|------|
| 完整会话 | 模拟一个完整的开发会话 |
| 预测准确性 | 验证预测建议的合理性 |
| 新类型注册 | 测试新动作类型的自动注册 |

## 7. 后续迭代

### 7.1 Phase 2：用户反馈学习

**功能描述**：根据用户对预测建议的响应（接受/拒绝/忽略）来调整预测模型。

**工作原理**：

```
预测建议 → 用户响应 → 记录反馈 → 调整模型
```

**响应类型与权重调整**：

| 用户响应 | 权重调整 | 说明 |
|----------|----------|------|
| 接受 (Y) | +20% | 用户同意，提高这个预测的权重 |
| 拒绝 (n) | -20% | 用户不同意，降低权重；如果用户执行了其他动作，提高那个动作的权重 |
| 忽略 | -5% | 用户没有响应，轻微降低权重 |

**实现要点**：
- 新增 `record_feedback.py` 脚本
- 在预测建议后等待用户响应
- 记录反馈到 `feedback/user_feedback.json`
- 调整转移矩阵中的权重

**为什么放在后续阶段**：
- MVP 先验证基础功能是否有价值
- 需要先有足够的预测数据
- 实现复杂度较高

### 7.2 Phase 3：自动执行

**功能描述**：当预测置信度非常高时，系统自动执行预测的动作，而不需要用户确认。

**工作原理**：

```
┌─────────────────────────────────────────────────────────────┐
│ 置信度 > 0.95 → 自动执行，告知用户                           │
│ 置信度 0.7-0.95 → 询问用户确认                               │
│ 置信度 0.5-0.7 → 显示建议，不强调                            │
│ 置信度 < 0.5 → 不显示建议                                    │
└─────────────────────────────────────────────────────────────┘
```

**示例**：

```
用户修改了 tests/test_user.py（测试文件）
预测：run_test，置信度 0.98

系统自动执行：pytest tests/test_user.py

AI 响应：
"测试文件已修改，我已经帮你运行测试了。结果如下：
✅ 3 tests passed"
```

**配置选项**：

```json
{
  "prediction": {
    "auto_execute_threshold": 0.95,
    "auto_execute_enabled": true,
    "never_auto_execute": ["git_push", "delete_file", "deploy"]
  }
}
```

**安全控制**：
- 高阈值（0.95），只有非常确定时才自动执行
- 用户可以关闭自动执行
- 某些危险操作永远不自动执行

**为什么放在后续阶段**：
- 风险较高，需要先验证预测准确性
- 用户需要先信任系统的预测
- MVP 先验证基础功能

### 7.3 Phase 4：与 Memory Skill 协同

**功能描述**：结合 Memory Skill 的历史记忆，提升预测准确性和建议个性化。

**协同方式**：

```
┌─────────────────────────────────────────────────────────────┐
│ Memory Skill: 检索相关历史记忆                               │
│ → "用户之前说过喜欢 TDD 开发方式"                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Behavior Prediction Skill: 预测下一步                        │
│ → 结合 Memory（用户喜欢 TDD）+ 行为统计 → 提高 run_test 置信度│
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 输出建议: "按照你的 TDD 习惯，要先运行测试吗？"               │
└─────────────────────────────────────────────────────────────┘
```

**实现要点**：
- 在预测前调用 Memory Skill 检索相关记忆
- 将记忆作为上下文因素影响置信度
- 生成个性化的建议文案

---

*文档版本: 1.0*  
*创建日期: 2026-01-31*
