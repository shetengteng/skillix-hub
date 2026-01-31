# 行为预测 Skill V2 实现文档

## 1. 概述

本文档详细说明 Behavior Prediction Skill V2 的实现细节，包括脚本实现、数据结构、API 设计等。

**相关文档**：
- 设计文档：`2026-01-31-07_behavior-prediction-v2-design.md`

## 2. 文件结构

```
skills/behavior-prediction/
├── SKILL.md                      # Skill 入口文档
├── default_config.json           # 默认配置
├── rules/
│   └── behavior-prediction.mdc   # Always Applied Rule
├── scripts/
│   ├── hook.py                   # 统一入口（--init / --finalize）
│   ├── record_session.py         # 记录会话
│   ├── extract_patterns.py       # 提取行为模式
│   ├── update_profile.py         # 更新用户画像
│   ├── get_statistics.py         # 获取统计数据（兼容 V1）
│   ├── user_profile.py           # 用户画像管理
│   └── utils.py                  # 工具函数
└── tests/
    ├── __init__.py
    ├── run_all_tests.py
    ├── test_hook.py
    ├── test_record_session.py
    ├── test_extract_patterns.py
    └── test_user_profile.py
```

## 3. 数据目录结构

```
<project>/.cursor/skills/behavior-prediction-data/
├── sessions/                      # 会话记录
│   └── 2026-01/                   # 按月份组织
│       ├── sess_20260131_001.json
│       └── sess_20260131_002.json
│
├── patterns/                      # 行为模式
│   ├── workflow_patterns.json     # 工作流程模式
│   ├── preferences.json           # 偏好数据
│   ├── project_patterns.json      # 项目模式
│   ├── transition_matrix.json     # 转移矩阵（兼容 V1）
│   └── types_registry.json        # 动作类型注册表（兼容 V1）
│
├── profile/                       # 用户画像
│   └── user_profile.json          # 综合用户画像
│
├── actions/                       # 动作记录（兼容 V1）
│   └── 2026-01-31.json
│
└── config.json                    # 用户配置
```

## 4. 核心脚本实现

### 4.1 hook.py - 统一入口

**功能**：提供统一的 hook 入口，支持 `--init` 和 `--finalize` 两种模式。

**调用方式**：

```bash
# 会话开始时
python3 hook.py --init

# 会话结束时
python3 hook.py --finalize '{...session_data...}'

# 记录单个动作（兼容 V1）
python3 hook.py --record '{...action_data...}'
```

**实现逻辑**：

```python
#!/usr/bin/env python3
"""
Behavior Prediction Hook - 统一入口

支持的操作：
- --init: 会话开始时调用，加载用户画像和预测建议
- --finalize: 会话结束时调用，记录会话并更新模式
- --record: 记录单个动作（兼容 V1）
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 导入子模块
from utils import get_data_dir, ensure_dir
from user_profile import load_user_profile, get_ai_summary
from record_session import record_session
from extract_patterns import extract_and_update_patterns
from record_action import record_action  # V1 兼容


def handle_init() -> dict:
    """
    会话开始时的初始化
    
    返回：
    - 用户画像摘要
    - 行为模式
    - 预测建议
    """
    try:
        # 1. 加载用户画像
        profile = load_user_profile()
        
        # 2. 加载行为模式
        patterns = load_behavior_patterns()
        
        # 3. 生成 AI 可用的摘要
        ai_summary = get_ai_summary(profile, patterns)
        
        # 4. 生成建议
        suggestions = generate_suggestions(profile, patterns)
        
        return {
            "status": "success",
            "user_profile": profile,
            "behavior_patterns": patterns,
            "ai_summary": ai_summary,
            "suggestions": suggestions
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def handle_finalize(session_data: dict) -> dict:
    """
    会话结束时的处理
    
    参数：
    - session_data: 会话数据（摘要、操作、对话等）
    
    处理：
    1. 记录会话到 sessions/
    2. 提取并更新行为模式
    3. 更新用户画像（可选，定期执行）
    """
    try:
        # 1. 记录会话
        session_id = record_session(session_data)
        
        # 2. 提取并更新模式
        patterns_updated = extract_and_update_patterns(session_data)
        
        # 3. 返回结果
        return {
            "status": "success",
            "session_id": session_id,
            "patterns_updated": patterns_updated,
            "message": f"Session {session_id} recorded successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def handle_record(action_data: dict) -> dict:
    """
    记录单个动作（兼容 V1）
    """
    return record_action(action_data)


def main():
    parser = argparse.ArgumentParser(description='Behavior Prediction Hook')
    parser.add_argument('--init', action='store_true', help='Initialize session')
    parser.add_argument('--finalize', type=str, help='Finalize session with data')
    parser.add_argument('--record', type=str, help='Record single action (V1 compat)')
    
    args = parser.parse_args()
    
    if args.init:
        result = handle_init()
    elif args.finalize:
        session_data = json.loads(args.finalize)
        result = handle_finalize(session_data)
    elif args.record:
        action_data = json.loads(args.record)
        result = handle_record(action_data)
    else:
        result = {"status": "error", "message": "No action specified"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### 4.2 record_session.py - 记录会话

**功能**：将完整会话记录保存到本地。

**输入数据结构**：

```json
{
  "session_summary": {
    "topic": "用户认证功能开发",
    "goals": ["创建认证 API", "实现 JWT 验证"],
    "completed_tasks": ["创建 auth.py", "实现 JWT 验证", "添加测试"],
    "technologies_used": ["FastAPI", "PyJWT", "pytest"],
    "workflow_stages": ["implement", "test"],
    "tags": ["#auth", "#api", "#jwt"]
  },
  "operations": {
    "files": {
      "created": ["src/api/auth.py", "tests/test_auth.py"],
      "modified": ["src/main.py", "requirements.txt"],
      "deleted": []
    },
    "commands": [
      {"command": "pip install pyjwt", "type": "install_dep", "exit_code": 0},
      {"command": "pytest tests/", "type": "run_test", "exit_code": 0}
    ]
  },
  "conversation": {
    "user_messages": [
      "帮我创建一个用户认证 API",
      "添加 JWT token 验证",
      "写一下单元测试"
    ],
    "message_count": 3
  },
  "time": {
    "start": "2026-01-31T10:00:00Z",
    "end": "2026-01-31T10:45:00Z"
  }
}
```

**实现逻辑**：

```python
#!/usr/bin/env python3
"""
记录完整会话
"""

import json
from datetime import datetime
from pathlib import Path
from utils import get_data_dir, ensure_dir, detect_project_info


def record_session(session_data: dict) -> str:
    """
    记录会话到本地
    
    返回：session_id
    """
    data_dir = get_data_dir()
    
    # 生成 session_id
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # 获取今日已有的会话数
    sessions_dir = data_dir / "sessions" / now.strftime("%Y-%m")
    ensure_dir(sessions_dir)
    
    existing_sessions = list(sessions_dir.glob(f"sess_{date_str}_*.json"))
    session_num = len(existing_sessions) + 1
    session_id = f"sess_{date_str}_{session_num:03d}"
    
    # 构建完整的会话记录
    session_record = {
        "session_id": session_id,
        "version": "2.0",
        "project": detect_project_info(),
        "time": {
            "start": session_data.get("time", {}).get("start", now.isoformat() + "Z"),
            "end": session_data.get("time", {}).get("end", now.isoformat() + "Z"),
            "recorded_at": now.isoformat() + "Z"
        },
        "conversation": session_data.get("conversation", {}),
        "operations": session_data.get("operations", {}),
        "summary": session_data.get("session_summary", {})
    }
    
    # 计算会话时长
    try:
        start = datetime.fromisoformat(session_record["time"]["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(session_record["time"]["end"].replace("Z", "+00:00"))
        session_record["time"]["duration_minutes"] = int((end - start).total_seconds() / 60)
    except:
        session_record["time"]["duration_minutes"] = 0
    
    # 保存会话记录
    session_file = sessions_dir / f"{session_id}.json"
    session_file.write_text(json.dumps(session_record, ensure_ascii=False, indent=2))
    
    # 更新会话索引
    update_session_index(session_id, session_record)
    
    return session_id


def update_session_index(session_id: str, session_record: dict):
    """
    更新会话索引，便于快速查询
    """
    data_dir = get_data_dir()
    index_file = data_dir / "index" / "sessions_index.json"
    ensure_dir(index_file.parent)
    
    # 读取或创建索引
    if index_file.exists():
        index = json.loads(index_file.read_text())
    else:
        index = {"sessions": [], "total_count": 0}
    
    # 添加新会话的索引信息
    index_entry = {
        "session_id": session_id,
        "date": session_record["time"]["recorded_at"][:10],
        "topic": session_record.get("summary", {}).get("topic", ""),
        "tags": session_record.get("summary", {}).get("tags", []),
        "workflow_stages": session_record.get("summary", {}).get("workflow_stages", []),
        "duration_minutes": session_record["time"].get("duration_minutes", 0)
    }
    
    index["sessions"].append(index_entry)
    index["total_count"] = len(index["sessions"])
    index["updated_at"] = datetime.now().isoformat() + "Z"
    
    # 只保留最近 500 条索引
    if len(index["sessions"]) > 500:
        index["sessions"] = index["sessions"][-500:]
    
    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2))
```

### 4.3 extract_patterns.py - 提取行为模式

**功能**：从会话记录中提取行为模式，更新模式数据。

**实现逻辑**：

```python
#!/usr/bin/env python3
"""
从会话记录中提取行为模式
"""

import json
from datetime import datetime
from pathlib import Path
from collections import Counter
from utils import get_data_dir, ensure_dir


def extract_and_update_patterns(session_data: dict) -> bool:
    """
    从新会话中提取模式并更新
    
    返回：是否有更新
    """
    updated = False
    
    # 1. 更新工作流程模式
    if update_workflow_patterns(session_data):
        updated = True
    
    # 2. 更新偏好数据
    if update_preferences(session_data):
        updated = True
    
    # 3. 更新项目模式
    if update_project_patterns(session_data):
        updated = True
    
    return updated


def update_workflow_patterns(session_data: dict) -> bool:
    """
    更新工作流程模式
    """
    data_dir = get_data_dir()
    patterns_file = data_dir / "patterns" / "workflow_patterns.json"
    ensure_dir(patterns_file.parent)
    
    # 读取或创建模式数据
    if patterns_file.exists():
        patterns = json.loads(patterns_file.read_text())
    else:
        patterns = {
            "version": "2.0",
            "patterns": [],
            "stage_transitions": {},
            "total_sessions": 0
        }
    
    # 获取本次会话的工作流程阶段
    summary = session_data.get("session_summary", {})
    stages = summary.get("workflow_stages", [])
    
    if not stages:
        return False
    
    # 更新阶段转移统计
    for i in range(len(stages) - 1):
        from_stage = stages[i]
        to_stage = stages[i + 1]
        
        if from_stage not in patterns["stage_transitions"]:
            patterns["stage_transitions"][from_stage] = {}
        
        if to_stage not in patterns["stage_transitions"][from_stage]:
            patterns["stage_transitions"][from_stage][to_stage] = {"count": 0}
        
        patterns["stage_transitions"][from_stage][to_stage]["count"] += 1
    
    # 重新计算转移概率
    for from_stage, transitions in patterns["stage_transitions"].items():
        total = sum(t["count"] for t in transitions.values())
        for to_stage, data in transitions.items():
            data["probability"] = round(data["count"] / total, 3) if total > 0 else 0
    
    # 更新会话计数
    patterns["total_sessions"] += 1
    patterns["updated_at"] = datetime.now().isoformat() + "Z"
    
    # 识别常见模式序列
    patterns["patterns"] = identify_common_sequences(patterns["stage_transitions"])
    
    # 保存
    patterns_file.write_text(json.dumps(patterns, ensure_ascii=False, indent=2))
    
    return True


def identify_common_sequences(transitions: dict) -> list:
    """
    从转移数据中识别常见的工作流程序列
    """
    sequences = []
    
    # 找出高频转移
    high_freq_transitions = []
    for from_stage, to_stages in transitions.items():
        for to_stage, data in to_stages.items():
            if data["count"] >= 3:  # 至少出现 3 次
                high_freq_transitions.append({
                    "from": from_stage,
                    "to": to_stage,
                    "count": data["count"],
                    "probability": data["probability"]
                })
    
    # 按频率排序
    high_freq_transitions.sort(key=lambda x: x["count"], reverse=True)
    
    # 构建序列模式
    for trans in high_freq_transitions[:10]:  # 取前 10 个
        sequences.append({
            "sequence": [trans["from"], trans["to"]],
            "count": trans["count"],
            "probability": trans["probability"],
            "description": f"{trans['from']} → {trans['to']}"
        })
    
    return sequences


def update_preferences(session_data: dict) -> bool:
    """
    更新用户偏好数据
    """
    data_dir = get_data_dir()
    prefs_file = data_dir / "patterns" / "preferences.json"
    ensure_dir(prefs_file.parent)
    
    # 读取或创建偏好数据
    if prefs_file.exists():
        prefs = json.loads(prefs_file.read_text())
    else:
        prefs = {
            "version": "2.0",
            "tech_stack": {
                "languages": {},
                "frameworks": {},
                "tools": {}
            },
            "workflow": {
                "stages_frequency": {}
            },
            "total_sessions": 0
        }
    
    summary = session_data.get("session_summary", {})
    
    # 更新技术栈统计
    technologies = summary.get("technologies_used", [])
    for tech in technologies:
        tech_lower = tech.lower()
        
        # 简单分类（可以更智能）
        if tech_lower in ["python", "javascript", "typescript", "java", "go", "rust"]:
            category = "languages"
        elif tech_lower in ["fastapi", "flask", "django", "vue", "react", "express"]:
            category = "frameworks"
        else:
            category = "tools"
        
        if tech_lower not in prefs["tech_stack"][category]:
            prefs["tech_stack"][category][tech_lower] = {"count": 0}
        
        prefs["tech_stack"][category][tech_lower]["count"] += 1
    
    # 更新工作流程阶段频率
    stages = summary.get("workflow_stages", [])
    for stage in stages:
        if stage not in prefs["workflow"]["stages_frequency"]:
            prefs["workflow"]["stages_frequency"][stage] = 0
        prefs["workflow"]["stages_frequency"][stage] += 1
    
    # 更新计数
    prefs["total_sessions"] += 1
    prefs["updated_at"] = datetime.now().isoformat() + "Z"
    
    # 计算偏好分数
    calculate_preference_scores(prefs)
    
    # 保存
    prefs_file.write_text(json.dumps(prefs, ensure_ascii=False, indent=2))
    
    return True


def calculate_preference_scores(prefs: dict):
    """
    计算各项的偏好分数（0-1）
    """
    total_sessions = prefs["total_sessions"]
    if total_sessions == 0:
        return
    
    # 计算技术栈偏好分数
    for category in ["languages", "frameworks", "tools"]:
        items = prefs["tech_stack"][category]
        if not items:
            continue
        
        max_count = max(item["count"] for item in items.values())
        for item in items.values():
            item["preference"] = round(item["count"] / max_count, 2) if max_count > 0 else 0


def update_project_patterns(session_data: dict) -> bool:
    """
    更新项目模式
    """
    data_dir = get_data_dir()
    project_file = data_dir / "patterns" / "project_patterns.json"
    ensure_dir(project_file.parent)
    
    # 读取或创建项目模式数据
    if project_file.exists():
        project_patterns = json.loads(project_file.read_text())
    else:
        project_patterns = {
            "version": "2.0",
            "patterns": {},
            "total_sessions": 0
        }
    
    # 获取项目类型（从 session_data 或推断）
    summary = session_data.get("session_summary", {})
    tags = summary.get("tags", [])
    technologies = summary.get("technologies_used", [])
    
    # 简单推断项目类型
    project_type = infer_project_type(tags, technologies)
    
    if project_type:
        if project_type not in project_patterns["patterns"]:
            project_patterns["patterns"][project_type] = {
                "count": 0,
                "common_stages": {},
                "common_tech": {}
            }
        
        pattern = project_patterns["patterns"][project_type]
        pattern["count"] += 1
        
        # 统计常见阶段
        for stage in summary.get("workflow_stages", []):
            if stage not in pattern["common_stages"]:
                pattern["common_stages"][stage] = 0
            pattern["common_stages"][stage] += 1
        
        # 统计常见技术
        for tech in technologies:
            tech_lower = tech.lower()
            if tech_lower not in pattern["common_tech"]:
                pattern["common_tech"][tech_lower] = 0
            pattern["common_tech"][tech_lower] += 1
    
    project_patterns["total_sessions"] += 1
    project_patterns["updated_at"] = datetime.now().isoformat() + "Z"
    
    # 保存
    project_file.write_text(json.dumps(project_patterns, ensure_ascii=False, indent=2))
    
    return True


def infer_project_type(tags: list, technologies: list) -> str:
    """
    根据标签和技术推断项目类型
    """
    tags_lower = [t.lower() for t in tags]
    tech_lower = [t.lower() for t in technologies]
    
    # API/后端项目
    if any(t in tags_lower for t in ["#api", "#backend", "#server"]):
        return "backend_api"
    if any(t in tech_lower for t in ["fastapi", "flask", "django", "express"]):
        return "backend_api"
    
    # 前端项目
    if any(t in tags_lower for t in ["#frontend", "#ui", "#web"]):
        return "frontend"
    if any(t in tech_lower for t in ["vue", "react", "angular"]):
        return "frontend"
    
    # 全栈项目
    if any(t in tags_lower for t in ["#fullstack"]):
        return "fullstack"
    
    # 工具/脚本
    if any(t in tags_lower for t in ["#script", "#tool", "#cli"]):
        return "tool_script"
    
    # 默认
    return "general"
```

### 4.4 user_profile.py - 用户画像管理

**功能**：管理用户画像的加载、更新和查询。

**实现逻辑**：

```python
#!/usr/bin/env python3
"""
用户画像管理
"""

import json
from datetime import datetime
from pathlib import Path
from utils import get_data_dir, ensure_dir


def load_user_profile() -> dict:
    """
    加载用户画像
    """
    data_dir = get_data_dir()
    profile_file = data_dir / "profile" / "user_profile.json"
    
    if profile_file.exists():
        return json.loads(profile_file.read_text())
    
    # 返回默认画像
    return get_default_profile()


def get_default_profile() -> dict:
    """
    获取默认用户画像
    """
    return {
        "version": "2.0",
        "updated_at": datetime.now().isoformat() + "Z",
        "stats": {
            "total_sessions": 0,
            "total_actions": 0,
            "active_days": 0,
            "first_seen": None,
            "last_seen": None
        },
        "preferences": {
            "common_file_types": [],
            "common_purposes": [],
            "preferred_task_flow": []
        },
        "time_patterns": {
            "most_active_hours": [],
            "avg_session_duration_minutes": 0
        }
    }


def update_user_profile() -> dict:
    """
    根据历史数据更新用户画像
    
    这个函数会分析所有会话记录，生成综合的用户画像
    """
    data_dir = get_data_dir()
    
    # 加载所有会话索引
    index_file = data_dir / "index" / "sessions_index.json"
    if not index_file.exists():
        return get_default_profile()
    
    index = json.loads(index_file.read_text())
    sessions = index.get("sessions", [])
    
    if not sessions:
        return get_default_profile()
    
    # 统计基本信息
    total_sessions = len(sessions)
    dates = set(s["date"] for s in sessions)
    active_days = len(dates)
    
    # 统计时间模式
    hours = []
    durations = []
    for session in sessions:
        # 提取小时（如果有）
        if "date" in session:
            # 假设有更详细的时间信息
            pass
        if "duration_minutes" in session:
            durations.append(session["duration_minutes"])
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # 统计工作流程偏好
    all_stages = []
    all_tags = []
    for session in sessions:
        all_stages.extend(session.get("workflow_stages", []))
        all_tags.extend(session.get("tags", []))
    
    # 计算频率
    from collections import Counter
    stage_counts = Counter(all_stages)
    tag_counts = Counter(all_tags)
    
    # 构建用户画像
    profile = {
        "version": "2.0",
        "updated_at": datetime.now().isoformat() + "Z",
        "stats": {
            "total_sessions": total_sessions,
            "active_days": active_days,
            "first_seen": min(dates) if dates else None,
            "last_seen": max(dates) if dates else None
        },
        "preferences": {
            "common_stages": [stage for stage, _ in stage_counts.most_common(5)],
            "common_tags": [tag for tag, _ in tag_counts.most_common(10)]
        },
        "time_patterns": {
            "avg_session_duration_minutes": round(avg_duration, 1)
        }
    }
    
    # 保存用户画像
    profile_file = data_dir / "profile" / "user_profile.json"
    ensure_dir(profile_file.parent)
    profile_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    
    return profile


def get_ai_summary(profile: dict, patterns: dict) -> dict:
    """
    生成 AI 可用的摘要信息
    
    这个摘要会在会话开始时返回给 AI，帮助 AI 了解用户
    """
    stats = profile.get("stats", {})
    prefs = profile.get("preferences", {})
    
    summary = {
        "summary": {
            "description": f"这是一个活跃了 {stats.get('active_days', 0)} 天的用户，"
                          f"共进行了 {stats.get('total_sessions', 0)} 次会话"
        },
        "predictions": {
            "rules": []
        }
    }
    
    # 添加预测规则
    if patterns:
        stage_transitions = patterns.get("stage_transitions", {})
        for from_stage, transitions in stage_transitions.items():
            for to_stage, data in transitions.items():
                if data.get("probability", 0) >= 0.5:
                    summary["predictions"]["rules"].append({
                        "when": f"用户完成 {from_stage} 阶段后",
                        "then": f"{int(data['probability'] * 100)}% 概率会进入 {to_stage} 阶段",
                        "action": f"可以主动询问是否需要 {to_stage}"
                    })
    
    return summary


def load_behavior_patterns() -> dict:
    """
    加载行为模式数据
    """
    data_dir = get_data_dir()
    patterns_file = data_dir / "patterns" / "workflow_patterns.json"
    
    if patterns_file.exists():
        return json.loads(patterns_file.read_text())
    
    return {
        "version": "2.0",
        "patterns": [],
        "stage_transitions": {},
        "total_sessions": 0
    }


def generate_suggestions(profile: dict, patterns: dict) -> list:
    """
    根据用户画像和行为模式生成建议
    """
    suggestions = []
    
    # 基于常见工作流程的建议
    common_sequences = patterns.get("patterns", [])
    for seq in common_sequences[:3]:
        suggestions.append(f"你常见的工作流程：{seq.get('description', '')}")
    
    # 基于偏好的建议
    prefs = profile.get("preferences", {})
    common_stages = prefs.get("common_stages", [])
    if common_stages:
        suggestions.append(f"你最常进行的工作阶段：{', '.join(common_stages[:3])}")
    
    return suggestions
```

### 4.5 utils.py - 工具函数

**功能**：提供通用的工具函数。

```python
#!/usr/bin/env python3
"""
工具函数
"""

import json
import os
from pathlib import Path
from datetime import datetime


# AI 助手目录优先级
AI_DIRS = [".cursor", ".claude", ".copilot", ".codeium", ".ai"]


def detect_ai_dir() -> str:
    """
    检测当前使用的 AI 助手目录
    """
    cwd = Path.cwd()
    
    # 检查项目级目录
    for ai_dir in AI_DIRS:
        if (cwd / ai_dir).exists():
            return ai_dir
    
    # 检查全局级目录
    home = Path.home()
    for ai_dir in AI_DIRS:
        if (home / ai_dir).exists():
            return ai_dir
    
    # 默认使用 .cursor
    return ".cursor"


def get_data_dir() -> Path:
    """
    获取数据存储目录
    
    优先级：
    1. 项目级：<project>/.cursor/skills/behavior-prediction-data/
    2. 全局级：~/.cursor/skills/behavior-prediction-data/
    """
    ai_dir = detect_ai_dir()
    cwd = Path.cwd()
    
    # 项目级目录
    project_data_dir = cwd / ai_dir / "skills" / "behavior-prediction-data"
    if project_data_dir.exists():
        return project_data_dir
    
    # 全局级目录
    global_data_dir = Path.home() / ai_dir / "skills" / "behavior-prediction-data"
    
    # 如果都不存在，创建全局级目录
    if not global_data_dir.exists():
        global_data_dir.mkdir(parents=True, exist_ok=True)
    
    return global_data_dir


def ensure_dir(path: Path):
    """
    确保目录存在
    """
    if path.is_file():
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)


def detect_project_info() -> dict:
    """
    检测当前项目信息
    """
    cwd = Path.cwd()
    
    project_info = {
        "path": str(cwd),
        "name": cwd.name,
        "type": "unknown",
        "tech_stack": []
    }
    
    # 检测技术栈
    if (cwd / "package.json").exists():
        project_info["tech_stack"].append("javascript")
        # 读取 package.json 获取更多信息
        try:
            pkg = json.loads((cwd / "package.json").read_text())
            deps = list(pkg.get("dependencies", {}).keys())
            if "vue" in deps:
                project_info["tech_stack"].append("vue")
                project_info["type"] = "frontend"
            if "react" in deps:
                project_info["tech_stack"].append("react")
                project_info["type"] = "frontend"
            if "express" in deps:
                project_info["tech_stack"].append("express")
                project_info["type"] = "backend_api"
        except:
            pass
    
    if (cwd / "requirements.txt").exists() or (cwd / "pyproject.toml").exists():
        project_info["tech_stack"].append("python")
        project_info["type"] = "backend_api"
    
    if (cwd / "go.mod").exists():
        project_info["tech_stack"].append("go")
        project_info["type"] = "backend_api"
    
    if (cwd / "Cargo.toml").exists():
        project_info["tech_stack"].append("rust")
    
    return project_info


def get_recent_sessions(limit: int = 10) -> list:
    """
    获取最近的会话记录
    """
    data_dir = get_data_dir()
    index_file = data_dir / "index" / "sessions_index.json"
    
    if not index_file.exists():
        return []
    
    index = json.loads(index_file.read_text())
    sessions = index.get("sessions", [])
    
    return sessions[-limit:]
```

## 5. Always Applied Rule

### 5.1 规则文件

**文件位置**：`rules/behavior-prediction.mdc`

```markdown
---
description: 行为预测 V2 - 会话生命周期管理
globs: ["**/*"]
alwaysApply: true
---

# 行为预测规则

> **版本**: v2.0
> **说明**: 统一管理会话全生命周期的行为记录和预测

## 一、会话开始时

### 1.1 触发条件

**每次新会话开始时**（用户发送第一条消息），调用 init hook。

### 1.2 调用命令

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

### 1.3 返回的信息

Hook 返回用户的行为模式和偏好：

```json
{
  "status": "success",
  "ai_summary": {
    "summary": {
      "description": "这是一个活跃了 15 天的用户，主要从事 API 开发、测试相关工作"
    },
    "predictions": {
      "rules": [
        {
          "when": "用户完成 implement 阶段后",
          "then": "85% 概率会进入 test 阶段",
          "action": "主动询问：要运行测试验证一下吗？"
        }
      ]
    }
  },
  "suggestions": [
    "你常见的工作流程：implement → test → commit",
    "你最常使用的技术：Python, FastAPI"
  ]
}
```

### 1.4 如何使用

获取用户行为模式后，AI 应该：
1. **了解用户习惯**：根据 `ai_summary` 了解用户的工作风格
2. **主动预测**：当用户完成某个阶段后，参考 `predictions.rules` 主动提供建议
3. **调整交互**：根据用户偏好调整交互方式

## 二、会话过程中

### 2.1 V2 模式（推荐）

V2 模式下，会话过程中**不需要**实时记录每个动作。所有记录在会话结束时统一处理。

AI 只需要：
1. 正常处理用户请求
2. 在适当时机根据行为模式提供建议
3. 记住本次会话执行了哪些操作（用于会话结束时的摘要）

### 2.2 V1 兼容模式（可选）

如果需要实时记录动作（兼容 V1），可以在执行工具调用后调用：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --record '{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {...}
}'
```

## 三、会话结束时

### 3.1 触发条件

当检测到以下信号时，调用 finalize hook：

**中文信号**：
- "谢谢"、"好的"、"结束"、"拜拜"、"再见"
- "完成了"、"可以了"、"就这样"

**英文信号**：
- "thanks"、"done"、"bye"
- "that's all"、"finished"

### 3.2 执行步骤

1. **回顾会话**：回顾本次会话的所有对话和操作
2. **生成摘要**：生成结构化的会话摘要
3. **调用 Hook**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "会话主题",
    "goals": ["目标1", "目标2"],
    "completed_tasks": ["任务1", "任务2"],
    "technologies_used": ["tech1", "tech2"],
    "workflow_stages": ["implement", "test"],
    "tags": ["#tag1", "#tag2"]
  },
  "operations": {
    "files": {
      "created": ["file1.py"],
      "modified": ["file2.py"],
      "deleted": []
    },
    "commands": [
      {"command": "pytest", "type": "run_test", "exit_code": 0}
    ]
  },
  "conversation": {
    "user_messages": ["消息1", "消息2"],
    "message_count": 2
  },
  "time": {
    "start": "会话开始时间",
    "end": "当前时间"
  }
}'
```

### 3.3 会话摘要生成指南

生成会话摘要时，请提取以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| topic | 会话主题（一句话） | "用户认证功能开发" |
| goals | 用户的目标 | ["创建认证 API", "实现 JWT"] |
| completed_tasks | 完成的具体任务 | ["创建 auth.py", "添加测试"] |
| technologies_used | 使用的技术/工具 | ["FastAPI", "PyJWT", "pytest"] |
| workflow_stages | 工作流程阶段 | ["implement", "test"] |
| tags | 标签 | ["#auth", "#api"] |

**工作流程阶段定义**：

| 阶段 | 说明 |
|------|------|
| design | 设计、规划、讨论方案 |
| implement | 编写代码、创建文件 |
| test | 编写测试、运行测试 |
| debug | 调试、修复问题 |
| refactor | 重构、优化代码 |
| document | 编写文档 |
| deploy | 部署、发布 |
| review | 代码审查 |
| commit | 提交代码 |

## 四、完整示例

### 4.1 会话流程

```
1. 会话开始
   → python3 hook.py --init
   → AI 获取用户行为模式

2. 用户：帮我创建一个用户认证 API
   → AI 执行 Write("src/api/auth.py", "...")
   → AI 继续处理...

3. 用户：添加 JWT token 验证
   → AI 执行 StrReplace(...)
   → AI 根据行为模式，主动询问"要运行测试吗？"

4. 用户：好的，运行测试
   → AI 执行 Shell("pytest tests/")

5. 用户：谢谢！
   → AI 生成会话摘要
   → python3 hook.py --finalize '{...}'
   → 会话结束
```

## 五、注意事项

1. **会话开始时调用 --init**：加载用户行为模式
2. **会话结束时调用 --finalize**：记录会话并更新模式
3. **主动预测**：根据行为模式，在适当时机主动提供建议
4. **静默执行**：hook 调用过程不需要向用户详细展示
5. **失败不阻塞**：如果 hook 调用失败，不影响正常对话
```

## 6. 配置文件

### 6.1 default_config.json

```json
{
  "version": "2.0",
  "enabled": true,
  "recording": {
    "enabled": true,
    "mode": "session",
    "retention_days": 90
  },
  "patterns": {
    "extraction_enabled": true,
    "min_sessions_for_pattern": 3
  },
  "profile": {
    "auto_update": true,
    "update_frequency": "weekly"
  },
  "prediction": {
    "enabled": true,
    "suggest_threshold": 0.5,
    "max_suggestions": 3
  },
  "v1_compat": {
    "enabled": true,
    "record_actions": false
  }
}
```

### 6.2 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | 总开关 |
| `recording.mode` | `"session"` | 记录模式：session（会话级）或 action（动作级，V1） |
| `recording.retention_days` | `90` | 会话记录保留天数 |
| `patterns.min_sessions_for_pattern` | `3` | 最少会话数才识别模式 |
| `profile.auto_update` | `true` | 是否自动更新用户画像 |
| `prediction.suggest_threshold` | `0.5` | 显示建议的最低置信度 |
| `v1_compat.enabled` | `true` | 是否启用 V1 兼容模式 |

## 7. SKILL.md 更新

```markdown
# Behavior Prediction Skill

为 AI 助手提供用户行为预测能力。通过记录和分析用户的会话内容，学习用户的工作流程、偏好和习惯，提供智能预测和个性化交互。

## 版本

- **V2.0**：会话级记录，多维度行为模式
- **V1.x**：动作级记录，转移概率预测（兼容）

## 安装后提示

> **重要**：安装完成后，请将以下内容展示给用户。

```
✅ Behavior Prediction Skill V2 安装成功！

这个 Skill 会：
• 记录你的会话内容（会话结束时）
• 学习你的工作流程和偏好
• 在适当时机提供智能建议

无需额外配置，开始使用即可！

其他命令：
• 查看我的行为模式
• 更新用户画像
• 查看行为统计
```

---

## 功能概述

### V2 新功能

1. **会话级记录**：会话结束时记录完整会话内容
2. **多维度模式**：工作流程模式 + 偏好模式 + 项目模式
3. **用户画像**：综合分析生成用户画像
4. **交互优化**：根据用户偏好调整交互方式

### 核心能力

| 能力 | 说明 |
|------|------|
| **行为记录** | 记录会话内容、操作、对话 |
| **模式学习** | 提取工作流程、偏好、项目模式 |
| **智能预测** | 基于模式预测下一步操作 |
| **个性化** | 根据用户画像优化交互 |

## 使用方式

### 自动模式（推荐）

启用 Always Applied Rule 后，系统会自动：
- 会话开始时加载用户画像
- 会话结束时记录并更新模式
- 在适当时机提供预测建议

### 手动命令

| 命令 | 描述 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `查看用户画像` | 显示用户画像信息 |
| `更新用户画像` | 手动触发画像更新 |
| `查看行为统计` | 显示统计数据概览 |

## 脚本说明

### hook.py

统一的 hook 入口，支持多种操作模式。

```bash
# 会话开始时
python3 <skill_dir>/scripts/hook.py --init

# 会话结束时
python3 <skill_dir>/scripts/hook.py --finalize '{...session_data...}'

# 记录单个动作（V1 兼容）
python3 <skill_dir>/scripts/hook.py --record '{...action_data...}'
```

### record_session.py

记录完整会话到本地。

```bash
python3 <skill_dir>/scripts/record_session.py '{
  "session_summary": {...},
  "operations": {...},
  "conversation": {...},
  "time": {...}
}'
```

### extract_patterns.py

从会话记录中提取行为模式。

```bash
python3 <skill_dir>/scripts/extract_patterns.py
```

### update_profile.py

更新用户画像。

```bash
python3 <skill_dir>/scripts/update_profile.py
```

## 数据存储

```
behavior-prediction-data/
├── sessions/                # 会话记录（按月份）
│   └── 2026-01/
│       └── sess_xxx.json
├── patterns/                # 行为模式
│   ├── workflow_patterns.json
│   ├── preferences.json
│   └── project_patterns.json
├── profile/                 # 用户画像
│   └── user_profile.json
├── index/                   # 索引
│   └── sessions_index.json
└── config.json              # 配置
```

## 配置选项

```json
{
  "enabled": true,
  "recording": {
    "mode": "session",
    "retention_days": 90
  },
  "prediction": {
    "enabled": true,
    "suggest_threshold": 0.5
  }
}
```

## 隐私说明

- 所有数据存储在本地
- 不上传任何信息到服务器
- 用户可以随时删除数据
- 会话内容仅用于模式学习
```

## 8. 测试用例

### 8.1 test_hook.py

```python
#!/usr/bin/env python3
"""
测试 hook.py
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# 设置测试环境
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestHookInit(unittest.TestCase):
    """测试 --init 功能"""
    
    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / ".cursor" / "skills" / "behavior-prediction-data"
        self.data_dir.mkdir(parents=True)
    
    def tearDown(self):
        """清理测试目录"""
        shutil.rmtree(self.test_dir)
    
    @patch('utils.get_data_dir')
    def test_init_empty_data(self, mock_get_data_dir):
        """测试无数据时的初始化"""
        mock_get_data_dir.return_value = self.data_dir
        
        from hook import handle_init
        result = handle_init()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("user_profile", result)
        self.assertIn("suggestions", result)
    
    @patch('utils.get_data_dir')
    def test_init_with_profile(self, mock_get_data_dir):
        """测试有用户画像时的初始化"""
        mock_get_data_dir.return_value = self.data_dir
        
        # 创建测试用户画像
        profile_dir = self.data_dir / "profile"
        profile_dir.mkdir(parents=True)
        profile_file = profile_dir / "user_profile.json"
        profile_file.write_text(json.dumps({
            "version": "2.0",
            "stats": {"total_sessions": 10, "active_days": 5}
        }))
        
        from hook import handle_init
        result = handle_init()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["user_profile"]["stats"]["total_sessions"], 10)


class TestHookFinalize(unittest.TestCase):
    """测试 --finalize 功能"""
    
    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / ".cursor" / "skills" / "behavior-prediction-data"
        self.data_dir.mkdir(parents=True)
    
    def tearDown(self):
        """清理测试目录"""
        shutil.rmtree(self.test_dir)
    
    @patch('utils.get_data_dir')
    def test_finalize_session(self, mock_get_data_dir):
        """测试会话结束处理"""
        mock_get_data_dir.return_value = self.data_dir
        
        session_data = {
            "session_summary": {
                "topic": "测试会话",
                "goals": ["测试目标"],
                "completed_tasks": ["任务1"],
                "technologies_used": ["python"],
                "workflow_stages": ["implement", "test"],
                "tags": ["#test"]
            },
            "operations": {
                "files": {"created": ["test.py"], "modified": [], "deleted": []},
                "commands": []
            },
            "conversation": {
                "user_messages": ["测试消息"],
                "message_count": 1
            },
            "time": {
                "start": "2026-01-31T10:00:00Z",
                "end": "2026-01-31T10:30:00Z"
            }
        }
        
        from hook import handle_finalize
        result = handle_finalize(session_data)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("session_id", result)
        self.assertTrue(result["patterns_updated"])


if __name__ == "__main__":
    unittest.main()
```

### 8.2 test_record_session.py

```python
#!/usr/bin/env python3
"""
测试 record_session.py
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestRecordSession(unittest.TestCase):
    """测试会话记录功能"""
    
    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / ".cursor" / "skills" / "behavior-prediction-data"
        self.data_dir.mkdir(parents=True)
    
    def tearDown(self):
        """清理测试目录"""
        shutil.rmtree(self.test_dir)
    
    @patch('utils.get_data_dir')
    @patch('utils.detect_project_info')
    def test_record_session_basic(self, mock_project, mock_data_dir):
        """测试基本会话记录"""
        mock_data_dir.return_value = self.data_dir
        mock_project.return_value = {"path": "/test", "name": "test", "type": "unknown", "tech_stack": []}
        
        from record_session import record_session
        
        session_data = {
            "session_summary": {
                "topic": "测试会话",
                "workflow_stages": ["implement"]
            },
            "time": {
                "start": "2026-01-31T10:00:00Z",
                "end": "2026-01-31T10:30:00Z"
            }
        }
        
        session_id = record_session(session_data)
        
        self.assertIsNotNone(session_id)
        self.assertTrue(session_id.startswith("sess_"))
        
        # 验证文件已创建
        sessions_dir = self.data_dir / "sessions"
        session_files = list(sessions_dir.rglob("*.json"))
        self.assertEqual(len(session_files), 1)
    
    @patch('utils.get_data_dir')
    @patch('utils.detect_project_info')
    def test_record_multiple_sessions(self, mock_project, mock_data_dir):
        """测试多个会话记录"""
        mock_data_dir.return_value = self.data_dir
        mock_project.return_value = {"path": "/test", "name": "test", "type": "unknown", "tech_stack": []}
        
        from record_session import record_session
        
        # 记录多个会话
        for i in range(3):
            session_data = {
                "session_summary": {"topic": f"会话 {i}"},
                "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
            }
            record_session(session_data)
        
        # 验证索引
        index_file = self.data_dir / "index" / "sessions_index.json"
        self.assertTrue(index_file.exists())
        
        index = json.loads(index_file.read_text())
        self.assertEqual(index["total_count"], 3)


if __name__ == "__main__":
    unittest.main()
```

## 9. 迁移指南

### 9.1 从 V1 迁移到 V2

V2 与 V1 可以共存，不需要强制迁移。

**共存模式**：
- V1 的动作记录继续保留在 `actions/` 目录
- V2 的会话记录保存在 `sessions/` 目录
- 两套数据互不影响

**完全迁移**（可选）：
1. 停用 V1 的实时动作记录
2. 删除 `actions/` 目录（可选）
3. 使用 V2 的会话级记录

### 9.2 配置迁移

```json
// V1 配置
{
  "recording": {
    "enabled": true
  }
}

// V2 配置
{
  "recording": {
    "enabled": true,
    "mode": "session"  // 新增：session 或 action
  },
  "v1_compat": {
    "enabled": true,    // 是否兼容 V1
    "record_actions": false  // 是否继续记录动作
  }
}
```

## 10. 总结

### 10.1 实现要点

1. **统一入口**：`hook.py` 提供 `--init` 和 `--finalize` 两种模式
2. **会话级记录**：会话结束时记录完整会话内容
3. **多维度模式**：工作流程 + 偏好 + 项目模式
4. **V1 兼容**：保留 `--record` 支持动作级记录

### 10.2 文件清单

| 文件 | 功能 |
|------|------|
| `hook.py` | 统一入口 |
| `record_session.py` | 记录会话 |
| `extract_patterns.py` | 提取模式 |
| `user_profile.py` | 用户画像 |
| `utils.py` | 工具函数 |
| `behavior-prediction.mdc` | Always Applied Rule |

### 10.3 下一步

1. 实现所有脚本
2. 编写完整测试
3. 更新 SKILL.md
4. 测试验证

---

*文档版本: 2.0*  
*创建日期: 2026-01-31*
