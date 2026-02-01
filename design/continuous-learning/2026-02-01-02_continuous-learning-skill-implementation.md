# Continuous Learning Skill 实施文档

## 1. 概述

本文档描述 Continuous Learning Skill 的具体实施方案，包括目录结构、脚本实现、规则文件配置等。

---

## 2. 目录结构

### 2.1 最终目录结构

```
~/.cursor/skills/
├── continuous-learning/                    # Skill 代码目录
│   ├── SKILL.md                           # Skill 入口文件
│   ├── rules/
│   │   └── continuous-learning.mdc        # 规则文件模板
│   ├── scripts/
│   │   ├── observe.py                     # 观察脚本
│   │   ├── analyze.py                     # 分析脚本
│   │   ├── instinct.py                    # 本能管理脚本
│   │   ├── setup_rule.py                  # 规则安装脚本
│   │   └── utils.py                       # 工具函数
│   ├── default_config.json                # 默认配置
│   └── tests/
│       ├── __init__.py
│       ├── run_all_tests.py
│       ├── test_observe.py
│       ├── test_analyze.py
│       ├── test_instinct.py
│       └── test_utils.py
│
└── continuous-learning-data/              # 用户数据目录
    ├── observations/                      # 观察记录
    │   └── 2026-02/
    │       └── obs_20260201_001.jsonl
    ├── instincts/                         # 本能文件
    │   └── prefer-functional.yaml
    ├── evolved/                           # 演化生成的技能
    │   ├── skills/
    │   │   └── testing-workflow/
    │   │       └── SKILL.md
    │   ├── commands/
    │   └── skills-index.json
    ├── profile/
    │   └── learning_profile.json
    └── config.json
```

---

## 3. 脚本实现

### 3.1 utils.py - 工具函数

```python
#!/usr/bin/env python3
"""
工具函数模块
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# ─────────────────────────────────────────────
# 路径管理
# ─────────────────────────────────────────────

def get_skill_dir() -> Path:
    """获取 Skill 代码目录"""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """获取用户数据目录"""
    # 优先使用全局目录
    global_dir = Path.home() / ".cursor" / "skills" / "continuous-learning-data"
    
    # 如果全局目录存在，使用全局目录
    if global_dir.exists():
        return global_dir
    
    # 否则创建全局目录
    global_dir.mkdir(parents=True, exist_ok=True)
    return global_dir


def ensure_data_dirs():
    """确保数据目录存在"""
    data_dir = get_data_dir()
    
    dirs = [
        data_dir / "observations",
        data_dir / "instincts",
        data_dir / "evolved" / "skills",
        data_dir / "evolved" / "commands",
        data_dir / "profile"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# 配置管理
# ─────────────────────────────────────────────

def load_config() -> Dict:
    """加载配置"""
    data_dir = get_data_dir()
    config_path = data_dir / "config.json"
    
    if config_path.exists():
        return json.loads(config_path.read_text())
    
    # 从默认配置复制
    default_config = get_skill_dir() / "default_config.json"
    if default_config.exists():
        config = json.loads(default_config.read_text())
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2))
        return config
    
    return {}


def save_config(config: Dict):
    """保存配置"""
    config_path = get_data_dir() / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2))


# ─────────────────────────────────────────────
# 时间工具
# ─────────────────────────────────────────────

def get_timestamp() -> str:
    """获取 ISO8601 时间戳"""
    return datetime.now().isoformat()


def get_date_str() -> str:
    """获取日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


def get_month_str() -> str:
    """获取月份字符串 YYYY-MM"""
    return datetime.now().strftime("%Y-%m")


# ─────────────────────────────────────────────
# Pending Session 管理
# ─────────────────────────────────────────────

def get_pending_session_path() -> Path:
    """获取 pending session 文件路径"""
    return get_data_dir() / "pending_session.json"


def load_pending_session() -> Optional[Dict]:
    """加载 pending session"""
    path = get_pending_session_path()
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_pending_session(data: Dict):
    """保存 pending session"""
    path = get_pending_session_path()
    if "session_start" not in data:
        data["session_start"] = get_timestamp()
    if "observations" not in data:
        data["observations"] = []
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def clear_pending_session():
    """清除 pending session"""
    path = get_pending_session_path()
    if path.exists():
        path.unlink()


def add_observation_to_pending(observation: Dict):
    """添加观察记录到 pending session"""
    pending = load_pending_session()
    if pending is None:
        pending = {"session_start": get_timestamp(), "observations": []}
    
    observation["timestamp"] = get_timestamp()
    pending["observations"].append(observation)
    save_pending_session(pending)


# ─────────────────────────────────────────────
# 技能索引管理
# ─────────────────────────────────────────────

def load_skills_index() -> Dict:
    """加载技能索引"""
    index_path = get_data_dir() / "evolved" / "skills-index.json"
    if index_path.exists():
        return json.loads(index_path.read_text())
    return {"skills": [], "last_updated": None}


def save_skills_index(index: Dict):
    """保存技能索引"""
    index["last_updated"] = get_timestamp()
    index_path = get_data_dir() / "evolved" / "skills-index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))


def add_skill_to_index(skill_info: Dict):
    """添加技能到索引"""
    index = load_skills_index()
    
    # 检查是否已存在
    existing = [s for s in index["skills"] if s["name"] == skill_info["name"]]
    if existing:
        # 更新现有记录
        for i, s in enumerate(index["skills"]):
            if s["name"] == skill_info["name"]:
                index["skills"][i] = skill_info
                break
    else:
        # 添加新记录
        index["skills"].append(skill_info)
    
    save_skills_index(index)


def remove_skill_from_index(skill_name: str):
    """从索引中移除技能"""
    index = load_skills_index()
    index["skills"] = [s for s in index["skills"] if s["name"] != skill_name]
    save_skills_index(index)


# ─────────────────────────────────────────────
# 本能文件解析
# ─────────────────────────────────────────────

def parse_instinct_file(content: str) -> Dict:
    """解析本能文件"""
    result = {}
    lines = content.split('\n')
    
    in_frontmatter = False
    content_lines = []
    
    for line in lines:
        if line.strip() == '---':
            if in_frontmatter:
                in_frontmatter = False
            else:
                in_frontmatter = True
            continue
        
        if in_frontmatter:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == 'confidence':
                    result[key] = float(value)
                elif key == 'evidence_count':
                    result[key] = int(value)
                else:
                    result[key] = value
        else:
            content_lines.append(line)
    
    result['content'] = '\n'.join(content_lines).strip()
    return result


def generate_instinct_file(instinct: Dict) -> str:
    """生成本能文件内容"""
    lines = ['---']
    
    for key in ['id', 'trigger', 'confidence', 'domain', 'source', 
                'created_at', 'updated_at', 'evidence_count']:
        if key in instinct:
            value = instinct[key]
            if isinstance(value, str) and ' ' in value:
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f'{key}: {value}')
    
    lines.append('---')
    lines.append('')
    
    if 'content' in instinct:
        lines.append(instinct['content'])
    
    return '\n'.join(lines)
```

### 3.2 observe.py - 观察脚本

```python
#!/usr/bin/env python3
"""
观察脚本 - 管理会话生命周期

用法：
  --init                  会话开始时调用
  --record <json>         记录观察
  --finalize <json>       会话结束时调用
"""

import argparse
import json
import sys
from pathlib import Path

from utils import (
    get_data_dir, ensure_data_dirs, get_timestamp, get_month_str,
    load_config, load_pending_session, save_pending_session,
    clear_pending_session, add_observation_to_pending,
    load_skills_index
)


def auto_finalize_pending_session() -> dict:
    """自动 finalize 上一个未完成的会话"""
    pending = load_pending_session()
    if not pending:
        return None
    
    observations = pending.get("observations", [])
    if not observations:
        clear_pending_session()
        return {"status": "skipped", "reason": "no_observations"}
    
    # 保存观察记录
    try:
        save_observations(pending)
        clear_pending_session()
        return {
            "status": "success",
            "message": "上一个会话已自动保存",
            "observation_count": len(observations)
        }
    except Exception as e:
        clear_pending_session()
        return {"status": "error", "message": str(e)}


def save_observations(session_data: dict):
    """保存观察记录到文件"""
    data_dir = get_data_dir()
    month_dir = data_dir / "observations" / get_month_str()
    month_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    timestamp = get_timestamp().replace(":", "-").replace(".", "-")
    filename = f"obs_{timestamp}.jsonl"
    filepath = month_dir / filename
    
    # 写入观察记录
    with open(filepath, 'w', encoding='utf-8') as f:
        for obs in session_data.get("observations", []):
            f.write(json.dumps(obs, ensure_ascii=False) + '\n')


def load_relevant_skills(user_context: str = "") -> list:
    """加载相关的演化技能"""
    index = load_skills_index()
    relevant = []
    
    for skill in index.get("skills", []):
        # 简单的关键词匹配
        triggers = skill.get("triggers", [])
        for trigger in triggers:
            if trigger.lower() in user_context.lower():
                relevant.append(skill)
                break
    
    return relevant


def handle_init() -> dict:
    """会话开始时的初始化"""
    try:
        ensure_data_dirs()
        
        # 1. 自动 finalize 上一个会话
        auto_result = auto_finalize_pending_session()
        
        # 2. 创建新的 pending session
        save_pending_session({})
        
        # 3. 加载配置
        config = load_config()
        
        # 4. 加载已学习的知识
        skills_index = load_skills_index()
        learned_skills = skills_index.get("skills", [])
        
        # 5. 加载本能摘要
        instincts_summary = load_instincts_summary()
        
        result = {
            "status": "success",
            "learned_skills_count": len(learned_skills),
            "instincts_count": instincts_summary.get("count", 0),
            "suggestions": generate_suggestions(learned_skills, instincts_summary)
        }
        
        if auto_result and auto_result.get("status") == "success":
            result["auto_finalized"] = auto_result
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def load_instincts_summary() -> dict:
    """加载本能摘要"""
    data_dir = get_data_dir()
    instincts_dir = data_dir / "instincts"
    
    if not instincts_dir.exists():
        return {"count": 0, "domains": [], "high_confidence": []}
    
    instincts = []
    for f in instincts_dir.glob("*.yaml"):
        try:
            from utils import parse_instinct_file
            content = f.read_text()
            instinct = parse_instinct_file(content)
            instincts.append(instinct)
        except:
            pass
    
    # 统计
    domains = list(set(i.get("domain", "general") for i in instincts))
    high_confidence = [i for i in instincts if i.get("confidence", 0) >= 0.7]
    
    return {
        "count": len(instincts),
        "domains": domains,
        "high_confidence": [
            {"id": i.get("id"), "trigger": i.get("trigger"), "confidence": i.get("confidence")}
            for i in high_confidence
        ]
    }


def generate_suggestions(skills: list, instincts: dict) -> list:
    """生成建议"""
    suggestions = []
    
    if skills:
        suggestions.append(f"已学习 {len(skills)} 个技能")
    
    if instincts.get("high_confidence"):
        for inst in instincts["high_confidence"][:3]:
            suggestions.append(f"高置信度本能: {inst['trigger']} ({inst['confidence']:.0%})")
    
    return suggestions


def handle_record(data: dict) -> dict:
    """记录观察"""
    try:
        ensure_data_dirs()
        add_observation_to_pending(data)
        return {"status": "success", "message": "观察已记录"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_finalize(data: dict) -> dict:
    """会话结束时的处理"""
    try:
        ensure_data_dirs()
        
        # 1. 获取 pending session
        pending = load_pending_session()
        if pending:
            # 合并数据
            if "observations" not in data:
                data["observations"] = []
            data["observations"].extend(pending.get("observations", []))
            data["session_start"] = pending.get("session_start")
        
        data["session_end"] = get_timestamp()
        
        # 2. 保存观察记录
        save_observations(data)
        
        # 3. 触发模式分析（可选）
        config = load_config()
        if config.get("detection", {}).get("enabled", True):
            from analyze import analyze_observations
            analysis_result = analyze_observations(data.get("observations", []))
        else:
            analysis_result = None
        
        # 4. 清除 pending session
        clear_pending_session()
        
        return {
            "status": "success",
            "message": "会话已保存",
            "observation_count": len(data.get("observations", [])),
            "analysis": analysis_result
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description='观察脚本')
    parser.add_argument('--init', action='store_true', help='会话开始')
    parser.add_argument('--record', type=str, help='记录观察')
    parser.add_argument('--finalize', type=str, help='会话结束')
    
    args = parser.parse_args()
    
    if args.init:
        result = handle_init()
    elif args.record:
        try:
            data = json.loads(args.record)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_record(data)
    elif args.finalize:
        try:
            data = json.loads(args.finalize)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_finalize(data)
    else:
        result = {"status": "error", "message": "请指定 --init, --record 或 --finalize"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### 3.3 analyze.py - 分析脚本

```python
#!/usr/bin/env python3
"""
分析脚本 - 从观察记录中提取模式

用法：
  --session <path>        分析指定会话文件
  --recent <days>         分析最近 N 天
  --observations <json>   分析观察数据
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

from utils import get_data_dir, get_timestamp, load_config


def analyze_observations(observations: List[Dict]) -> Dict:
    """分析观察记录，提取模式"""
    result = {
        "patterns_found": [],
        "user_corrections": [],
        "error_resolutions": [],
        "tool_preferences": []
    }
    
    # 1. 检测用户纠正
    corrections = detect_user_corrections(observations)
    result["user_corrections"] = corrections
    
    # 2. 检测错误解决
    resolutions = detect_error_resolutions(observations)
    result["error_resolutions"] = resolutions
    
    # 3. 检测工具偏好
    preferences = detect_tool_preferences(observations)
    result["tool_preferences"] = preferences
    
    # 4. 汇总模式
    all_patterns = corrections + resolutions + preferences
    result["patterns_found"] = all_patterns
    result["pattern_count"] = len(all_patterns)
    
    return result


def detect_user_corrections(observations: List[Dict]) -> List[Dict]:
    """检测用户纠正模式"""
    corrections = []
    
    # 纠正关键词
    correction_keywords = [
        "不要", "不是", "错了", "改成", "应该是",
        "no", "not", "wrong", "should be", "instead"
    ]
    
    for i, obs in enumerate(observations):
        if obs.get("event") == "user_feedback":
            content = obs.get("content", "").lower()
            
            # 检查是否包含纠正关键词
            is_correction = any(kw in content for kw in correction_keywords)
            
            if is_correction:
                # 查找之前的 AI 操作
                prev_action = find_previous_action(observations, i)
                
                if prev_action:
                    corrections.append({
                        "type": "user_correction",
                        "original_action": prev_action,
                        "correction": obs.get("content"),
                        "timestamp": obs.get("timestamp")
                    })
    
    return corrections


def detect_error_resolutions(observations: List[Dict]) -> List[Dict]:
    """检测错误解决模式"""
    resolutions = []
    
    for i, obs in enumerate(observations):
        if obs.get("event") == "tool_error" or obs.get("has_error"):
            error_content = obs.get("error", obs.get("output", ""))
            
            # 查找后续的修复操作
            fix_action = find_fix_action(observations, i)
            
            if fix_action:
                resolutions.append({
                    "type": "error_resolution",
                    "error": error_content[:200],  # 截断
                    "fix": fix_action,
                    "timestamp": obs.get("timestamp")
                })
    
    return resolutions


def detect_tool_preferences(observations: List[Dict]) -> List[Dict]:
    """检测工具偏好"""
    tool_counts = {}
    
    for obs in observations:
        if obs.get("event") == "tool_call":
            tool = obs.get("tool", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    # 找出高频工具
    preferences = []
    total = sum(tool_counts.values())
    
    for tool, count in tool_counts.items():
        if count >= 3 and count / total >= 0.2:  # 至少 3 次且占比 20%
            preferences.append({
                "type": "tool_preference",
                "tool": tool,
                "count": count,
                "ratio": count / total
            })
    
    return preferences


def find_previous_action(observations: List[Dict], current_index: int) -> Optional[Dict]:
    """查找之前的 AI 操作"""
    for i in range(current_index - 1, -1, -1):
        obs = observations[i]
        if obs.get("event") == "tool_call":
            return {
                "tool": obs.get("tool"),
                "input": obs.get("input"),
                "timestamp": obs.get("timestamp")
            }
    return None


def find_fix_action(observations: List[Dict], error_index: int) -> Optional[Dict]:
    """查找修复操作"""
    # 在错误后的 5 个操作内查找
    for i in range(error_index + 1, min(error_index + 6, len(observations))):
        obs = observations[i]
        if obs.get("event") == "tool_call":
            return {
                "tool": obs.get("tool"),
                "input": obs.get("input"),
                "timestamp": obs.get("timestamp")
            }
    return None


def main():
    parser = argparse.ArgumentParser(description='分析脚本')
    parser.add_argument('--session', type=str, help='分析指定会话文件')
    parser.add_argument('--recent', type=int, help='分析最近 N 天')
    parser.add_argument('--observations', type=str, help='分析观察数据 JSON')
    
    args = parser.parse_args()
    
    if args.observations:
        try:
            observations = json.loads(args.observations)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}, ensure_ascii=False))
            sys.exit(1)
        result = analyze_observations(observations)
    elif args.session:
        # 从文件加载
        path = Path(args.session)
        if not path.exists():
            print(json.dumps({"status": "error", "message": "文件不存在"}, ensure_ascii=False))
            sys.exit(1)
        observations = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                observations.append(json.loads(line))
        result = analyze_observations(observations)
    else:
        result = {"status": "error", "message": "请指定 --session, --recent 或 --observations"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### 3.4 instinct.py - 本能管理脚本

```python
#!/usr/bin/env python3
"""
本能管理脚本

用法：
  status                  显示所有本能
  create <json>           创建新本能
  update <id> <json>      更新本能
  delete <id>             删除本能
  evolve                  演化本能为技能
  --check-skill <name>    检查技能类型
  --delete-skill <name>   删除演化技能
  --sync                  同步和清理
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

from utils import (
    get_data_dir, get_timestamp, load_config,
    parse_instinct_file, generate_instinct_file,
    load_skills_index, save_skills_index,
    add_skill_to_index, remove_skill_from_index
)


def list_instincts() -> List[Dict]:
    """列出所有本能"""
    instincts_dir = get_data_dir() / "instincts"
    if not instincts_dir.exists():
        return []
    
    instincts = []
    for f in instincts_dir.glob("*.yaml"):
        try:
            content = f.read_text()
            instinct = parse_instinct_file(content)
            instinct["_file"] = str(f)
            instincts.append(instinct)
        except Exception as e:
            print(f"Warning: Failed to parse {f}: {e}", file=sys.stderr)
    
    return instincts


def create_instinct(data: Dict) -> Dict:
    """创建新本能"""
    instincts_dir = get_data_dir() / "instincts"
    instincts_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置默认值
    if "id" not in data:
        return {"status": "error", "message": "缺少 id 字段"}
    
    data.setdefault("confidence", 0.3)
    data.setdefault("domain", "general")
    data.setdefault("source", "manual")
    data.setdefault("created_at", get_timestamp())
    data.setdefault("updated_at", get_timestamp())
    data.setdefault("evidence_count", 1)
    
    # 生成文件内容
    content = generate_instinct_file(data)
    
    # 保存文件
    filepath = instincts_dir / f"{data['id']}.yaml"
    filepath.write_text(content)
    
    return {
        "status": "success",
        "message": f"本能 '{data['id']}' 已创建",
        "path": str(filepath)
    }


def update_instinct(instinct_id: str, data: Dict) -> Dict:
    """更新本能"""
    instincts_dir = get_data_dir() / "instincts"
    filepath = instincts_dir / f"{instinct_id}.yaml"
    
    if not filepath.exists():
        return {"status": "error", "message": f"本能 '{instinct_id}' 不存在"}
    
    # 加载现有本能
    content = filepath.read_text()
    instinct = parse_instinct_file(content)
    
    # 更新字段
    instinct.update(data)
    instinct["updated_at"] = get_timestamp()
    
    # 保存
    new_content = generate_instinct_file(instinct)
    filepath.write_text(new_content)
    
    return {
        "status": "success",
        "message": f"本能 '{instinct_id}' 已更新"
    }


def delete_instinct(instinct_id: str) -> Dict:
    """删除本能"""
    instincts_dir = get_data_dir() / "instincts"
    filepath = instincts_dir / f"{instinct_id}.yaml"
    
    if not filepath.exists():
        return {"status": "error", "message": f"本能 '{instinct_id}' 不存在"}
    
    filepath.unlink()
    
    return {
        "status": "success",
        "message": f"本能 '{instinct_id}' 已删除"
    }


def check_skill(skill_name: str) -> Dict:
    """检查技能是否是演化生成的"""
    index = load_skills_index()
    
    for skill in index.get("skills", []):
        if skill["name"] == skill_name:
            return {
                "is_evolved": True,
                "skill_name": skill_name,
                "path": skill.get("path"),
                "cursor_path": skill.get("cursor_path")
            }
    
    # 检查是否存在于 Cursor skills 目录
    cursor_path = Path.home() / ".cursor" / "skills" / skill_name
    if cursor_path.exists():
        return {
            "is_evolved": False,
            "skill_name": skill_name,
            "suggestion": f"'{skill_name}' 不是演化生成的技能。"
                         f"如果要删除，请手动执行: rm -rf {cursor_path}"
        }
    
    return {
        "is_evolved": False,
        "skill_name": skill_name,
        "suggestion": f"未找到名为 '{skill_name}' 的技能"
    }


def delete_evolved_skill(skill_name: str, delete_instincts: bool = False) -> Dict:
    """删除演化生成的技能"""
    result = {"status": "success", "deleted": [], "errors": []}
    
    # 1. 检查是否是演化技能
    check_result = check_skill(skill_name)
    if not check_result.get("is_evolved"):
        return {
            "status": "not_evolved",
            "message": check_result.get("suggestion")
        }
    
    # 2. 删除源文件
    evolved_path = get_data_dir() / "evolved" / "skills" / skill_name
    if evolved_path.exists():
        shutil.rmtree(evolved_path)
        result["deleted"].append(f"源文件: {evolved_path}")
    
    # 3. 删除 Cursor 同步
    cursor_path = Path.home() / ".cursor" / "skills" / f"evolved-{skill_name}"
    if cursor_path.exists():
        if cursor_path.is_symlink():
            cursor_path.unlink()
            result["deleted"].append(f"符号链接: {cursor_path}")
        else:
            shutil.rmtree(cursor_path)
            result["deleted"].append(f"同步目录: {cursor_path}")
    
    # 4. 更新索引
    remove_skill_from_index(skill_name)
    result["deleted"].append("技能索引已更新")
    
    return result


def evolve_instincts() -> Dict:
    """将相关本能演化为技能"""
    instincts = list_instincts()
    
    if len(instincts) < 3:
        return {
            "status": "insufficient",
            "message": f"需要至少 3 个本能才能演化，当前有 {len(instincts)} 个"
        }
    
    # 按领域分组
    by_domain = {}
    for inst in instincts:
        domain = inst.get("domain", "general")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(inst)
    
    # 找出可以演化的领域
    evolvable = []
    for domain, domain_instincts in by_domain.items():
        if len(domain_instincts) >= 3:
            avg_confidence = sum(i.get("confidence", 0.5) for i in domain_instincts) / len(domain_instincts)
            if avg_confidence >= 0.5:
                evolvable.append({
                    "domain": domain,
                    "instincts": domain_instincts,
                    "avg_confidence": avg_confidence
                })
    
    if not evolvable:
        return {
            "status": "no_candidates",
            "message": "没有找到可以演化的本能组合"
        }
    
    # 生成技能
    created_skills = []
    for candidate in evolvable:
        skill_name = f"{candidate['domain']}-workflow"
        skill_result = create_evolved_skill(skill_name, candidate["instincts"])
        if skill_result.get("status") == "success":
            created_skills.append(skill_name)
    
    return {
        "status": "success",
        "created_skills": created_skills,
        "message": f"已创建 {len(created_skills)} 个技能"
    }


def create_evolved_skill(skill_name: str, instincts: List[Dict]) -> Dict:
    """创建演化技能"""
    # 1. 创建技能目录
    skill_dir = get_data_dir() / "evolved" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 生成 SKILL.md
    skill_content = generate_skill_content(skill_name, instincts)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(skill_content)
    
    # 3. 同步到 Cursor
    cursor_dir = Path.home() / ".cursor" / "skills" / f"evolved-{skill_name}"
    if cursor_dir.exists():
        shutil.rmtree(cursor_dir)
    shutil.copytree(skill_dir, cursor_dir)
    
    # 4. 更新索引
    triggers = []
    for inst in instincts:
        trigger = inst.get("trigger", "")
        triggers.extend(trigger.split())
    
    add_skill_to_index({
        "name": skill_name,
        "path": str(skill_dir),
        "cursor_path": str(cursor_dir),
        "triggers": list(set(triggers)),
        "domains": [inst.get("domain", "general") for inst in instincts],
        "evolved_at": get_timestamp(),
        "synced": True
    })
    
    return {
        "status": "success",
        "skill_name": skill_name,
        "path": str(skill_dir),
        "cursor_path": str(cursor_dir)
    }


def generate_skill_content(skill_name: str, instincts: List[Dict]) -> str:
    """生成技能文件内容"""
    lines = [
        "---",
        f"name: {skill_name}",
        f"description: 基于 {len(instincts)} 个本能演化生成的技能",
        "evolved_from:"
    ]
    
    for inst in instincts:
        lines.append(f"  - {inst.get('id')} (置信度: {inst.get('confidence', 0.5)})")
    
    lines.append(f"evolved_at: \"{get_timestamp()}\"")
    lines.append("---")
    lines.append("")
    lines.append(f"# {skill_name.replace('-', ' ').title()}")
    lines.append("")
    lines.append("## 触发条件")
    lines.append("")
    
    for inst in instincts:
        lines.append(f"- {inst.get('trigger', '未知触发条件')}")
    
    lines.append("")
    lines.append("## 行为")
    lines.append("")
    
    for inst in instincts:
        content = inst.get("content", "")
        # 提取行为部分
        if "## 行为" in content:
            action = content.split("## 行为")[1].split("##")[0].strip()
            lines.append(f"- {action[:100]}")
    
    return "\n".join(lines)


def sync_and_cleanup() -> Dict:
    """同步和清理"""
    result = {"synced": [], "cleaned": [], "errors": []}
    
    # 1. 检查索引中的技能是否存在
    index = load_skills_index()
    for skill in index.get("skills", []):
        skill_path = Path(skill.get("path", ""))
        if not skill_path.exists():
            # 技能不存在，清理索引
            remove_skill_from_index(skill["name"])
            result["cleaned"].append(f"索引: {skill['name']}")
            
            # 清理 Cursor 同步
            cursor_path = Path(skill.get("cursor_path", ""))
            if cursor_path.exists():
                if cursor_path.is_symlink():
                    cursor_path.unlink()
                else:
                    shutil.rmtree(cursor_path)
                result["cleaned"].append(f"Cursor: {cursor_path}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='本能管理脚本')
    parser.add_argument('command', nargs='?', help='命令: status, create, update, delete, evolve')
    parser.add_argument('args', nargs='*', help='命令参数')
    parser.add_argument('--check-skill', type=str, help='检查技能类型')
    parser.add_argument('--delete-skill', type=str, help='删除演化技能')
    parser.add_argument('--sync', action='store_true', help='同步和清理')
    
    args = parser.parse_args()
    
    if args.check_skill:
        result = check_skill(args.check_skill)
    elif args.delete_skill:
        result = delete_evolved_skill(args.delete_skill)
    elif args.sync:
        result = sync_and_cleanup()
    elif args.command == 'status':
        instincts = list_instincts()
        result = {
            "status": "success",
            "count": len(instincts),
            "instincts": [
                {
                    "id": i.get("id"),
                    "trigger": i.get("trigger"),
                    "confidence": i.get("confidence"),
                    "domain": i.get("domain")
                }
                for i in instincts
            ]
        }
    elif args.command == 'create':
        if not args.args:
            result = {"status": "error", "message": "请提供本能数据 JSON"}
        else:
            try:
                data = json.loads(args.args[0])
            except json.JSONDecodeError as e:
                result = {"status": "error", "message": f"Invalid JSON: {e}"}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                sys.exit(1)
            result = create_instinct(data)
    elif args.command == 'delete':
        if not args.args:
            result = {"status": "error", "message": "请提供本能 ID"}
        else:
            result = delete_instinct(args.args[0])
    elif args.command == 'evolve':
        result = evolve_instincts()
    else:
        result = {"status": "error", "message": "请指定命令: status, create, update, delete, evolve"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### 3.5 setup_rule.py - 规则安装脚本

```python
#!/usr/bin/env python3
"""
设置持续学习规则

为不同的 AI 助手生成持续学习规则文件，使 Continuous Learning Skill 能够自动记录和学习。
"""

import sys
import json
from pathlib import Path

from utils import get_data_dir

# 规则模板 - Cursor 格式 (.mdc)
CURSOR_RULE_TEMPLATE = '''---
description: 持续学习 - 会话生命周期管理
globs: ["**/*"]
alwaysApply: true
---

# 持续学习规则

> **版本**: v1.0
> **说明**: 管理会话生命周期，自动学习用户行为模式

## 一、会话开始时

**每次新会话开始时**，调用初始化脚本：

```bash
python3 {observe_script_path} --init
```

返回的信息包含：
- 已学习的技能数量
- 高置信度本能列表
- 建议

## 二、会话过程中

### 记录关键动作

在以下时机调用记录脚本：
- 完成文件创建/修改后
- 用户给出反馈/纠正后
- 完成一个功能点后

```bash
python3 {observe_script_path} --record '{{
  "event": "tool_call",
  "tool": "Write",
  "input": {{"file": "src/api.py"}},
  "stage": "implement"
}}'
```

### 记录用户反馈

当用户给出反馈时：

```bash
python3 {observe_script_path} --record '{{
  "event": "user_feedback",
  "type": "correction",
  "content": "用户的反馈内容"
}}'
```

## 三、会话结束时

### 自动 Finalize

下次 `--init` 会自动保存上次会话，无需手动触发。

### 手动触发（可选）

检测到结束信号时，可以手动调用：

```bash
python3 {observe_script_path} --finalize '{{
  "topic": "会话主题",
  "summary": "会话摘要"
}}'
```

## 四、技能管理命令

### 查看学习到的知识

```bash
python3 {instinct_script_path} status
```

### 演化本能为技能

```bash
python3 {instinct_script_path} evolve
```

### 删除技能

当用户说 "删除技能: xxx" 时：

1. 先检查技能类型：
```bash
python3 {instinct_script_path} --check-skill <name>
```

2. 如果是演化技能，执行删除：
```bash
python3 {instinct_script_path} --delete-skill <name>
```

3. 如果不是演化技能，告诉用户如何手动删除。

**重要**：
- ❌ 不要直接使用 rm 或 Delete 工具删除技能文件
- ✅ 始终通过脚本删除，确保同步文件和索引正确处理

## 五、注意事项

1. 脚本调用过程不需要向用户详细展示
2. 如果脚本调用失败，不影响正常对话
3. 观察记录是可选的，不强制每次都记录
'''

# 规则模板 - Claude 格式 (.md)
CLAUDE_RULE_TEMPLATE = '''---
name: continuous-learning
description: 持续学习 - 会话生命周期管理，自动学习用户行为模式
allowed-tools: Shell, Read, Grep, Glob
---

# 持续学习规则

## 一、会话开始时

**每次新会话开始时**，调用初始化脚本：

```bash
python3 {observe_script_path} --init
```

## 二、会话过程中

在关键时机记录观察：

```bash
python3 {observe_script_path} --record '{{...}}'
```

## 三、会话结束时

下次 `--init` 会自动保存上次会话。

## 四、注意事项

- 静默执行脚本调用
- 失败不阻塞正常对话
'''

# 通用规则模板 (.md)
GENERIC_RULE_TEMPLATE = '''# 持续学习规则

## 一、会话开始时

```bash
python3 {observe_script_path} --init
```

## 二、会话过程中

```bash
python3 {observe_script_path} --record '{{...}}'
```

## 三、会话结束时

下次 `--init` 会自动保存上次会话。
'''


def get_rule_config(assistant_type: str) -> dict:
    """获取不同 AI 助手的规则配置"""
    configs = {
        "cursor": {
            "dir_name": ".cursor",
            "rules_dir": "rules",
            "file_name": "continuous-learning.mdc",
            "template": CURSOR_RULE_TEMPLATE
        },
        "claude": {
            "dir_name": ".claude",
            "rules_dir": "rules",
            "file_name": "continuous-learning.md",
            "template": CLAUDE_RULE_TEMPLATE
        },
        "generic": {
            "dir_name": ".ai",
            "rules_dir": "rules",
            "file_name": "continuous-learning.md",
            "template": GENERIC_RULE_TEMPLATE
        }
    }
    return configs.get(assistant_type, configs["generic"])


def detect_assistant_type() -> str:
    """检测当前使用的 AI 助手类型"""
    # 检查 .cursor 目录是否存在
    if (Path.home() / ".cursor").exists():
        return "cursor"
    elif (Path.home() / ".claude").exists():
        return "claude"
    else:
        return "generic"


def setup_rule(location: str = "global", assistant_type: str = None, force: bool = False) -> dict:
    """设置持续学习规则"""
    if assistant_type is None:
        assistant_type = detect_assistant_type()
    
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    base_dir = Path.home() / config["dir_name"]
    rules_dir = base_dir / config["rules_dir"]
    rule_file = rules_dir / config["file_name"]
    
    # 检查规则文件是否已存在
    if rule_file.exists() and not force:
        return {
            "success": False,
            "message": f"规则文件已存在: {rule_file}，使用 force=true 强制覆盖",
            "rule_file": str(rule_file)
        }
    
    # 创建规则目录
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    # 计算脚本路径
    scripts_dir = base_dir / "skills" / "continuous-learning" / "scripts"
    observe_script_path = str(scripts_dir / "observe.py")
    instinct_script_path = str(scripts_dir / "instinct.py")
    
    # 生成规则内容
    rule_content = config["template"].format(
        observe_script_path=observe_script_path,
        instinct_script_path=instinct_script_path
    )
    
    # 写入规则文件
    try:
        rule_file.write_text(rule_content, encoding='utf-8')
    except Exception as e:
        return {
            "success": False,
            "message": f"写入规则文件失败: {e}"
        }
    
    return {
        "success": True,
        "rule_file": str(rule_file),
        "assistant_type": assistant_type,
        "location": location,
        "message": f"持续学习规则已创建: {rule_file}"
    }


def remove_rule(location: str = "global", assistant_type: str = None) -> dict:
    """移除持续学习规则"""
    if assistant_type is None:
        assistant_type = detect_assistant_type()
    
    config = get_rule_config(assistant_type)
    
    base_dir = Path.home() / config["dir_name"]
    rule_file = base_dir / config["rules_dir"] / config["file_name"]
    
    if not rule_file.exists():
        return {
            "success": False,
            "message": f"规则文件不存在: {rule_file}"
        }
    
    try:
        rule_file.unlink()
    except Exception as e:
        return {
            "success": False,
            "message": f"删除规则文件失败: {e}"
        }
    
    return {
        "success": True,
        "rule_file": str(rule_file),
        "message": f"持续学习规则已移除: {rule_file}"
    }


def check_rule(location: str = "global", assistant_type: str = None) -> dict:
    """检查持续学习规则状态"""
    if assistant_type is None:
        assistant_type = detect_assistant_type()
    
    config = get_rule_config(assistant_type)
    
    base_dir = Path.home() / config["dir_name"]
    rule_file = base_dir / config["rules_dir"] / config["file_name"]
    
    exists = rule_file.exists()
    
    return {
        "success": True,
        "exists": exists,
        "enabled": exists,
        "rule_file": str(rule_file),
        "assistant_type": assistant_type,
        "location": location,
        "message": f"持续学习规则{'已启用' if exists else '未启用'}"
    }


def update_rule(location: str = "global", assistant_type: str = None) -> dict:
    """更新持续学习规则到最新版本"""
    check_result = check_rule(location, assistant_type)
    
    if not check_result["exists"]:
        return {
            "success": False,
            "message": "持续学习规则未启用，请先使用 enable 操作启用"
        }
    
    return setup_rule(location, assistant_type, force=True)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": """用法:
  启用持续学习规则: python3 setup_rule.py '{"action": "enable"}'
  启用(全局): python3 setup_rule.py '{"action": "enable", "location": "global"}'
  禁用持续学习规则: python3 setup_rule.py '{"action": "disable"}'
  更新规则: python3 setup_rule.py '{"action": "update"}'
  检查状态: python3 setup_rule.py '{"action": "check"}'
  指定助手类型: python3 setup_rule.py '{"action": "enable", "assistant_type": "cursor"}'
  
支持的助手类型: cursor, claude, generic
支持的操作: enable, disable, update, check"""
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "message": f"JSON 解析错误: {e}"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    action = data.get("action", "check")
    location = data.get("location", "global")
    assistant_type = data.get("assistant_type")
    force = data.get("force", False)
    
    if action == "enable":
        result = setup_rule(location, assistant_type, force)
        if result["success"]:
            result["message"] = f"持续学习规则已启用: {result['rule_file']}"
    elif action == "disable":
        result = remove_rule(location, assistant_type)
        if result["success"]:
            result["message"] = "持续学习规则已禁用"
    elif action == "update":
        result = update_rule(location, assistant_type)
        if result["success"]:
            result["message"] = f"持续学习规则已更新: {result['rule_file']}"
    elif action == "check":
        result = check_rule(location, assistant_type)
    else:
        result = {
            "success": False,
            "message": f"未知操作: {action}，支持的操作: enable, disable, update, check"
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 4. 规则文件

### 4.1 continuous-learning.mdc

```markdown
---
description: 持续学习 - 会话生命周期管理
globs: ["**/*"]
alwaysApply: true
---

# 持续学习规则

> **版本**: v1.0
> **说明**: 管理会话生命周期，自动学习用户行为模式

## 一、会话开始时

**每次新会话开始时**，调用初始化脚本：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init
```

返回的信息包含：
- 已学习的技能数量
- 高置信度本能列表
- 建议

## 二、会话过程中

### 记录关键动作

在以下时机调用记录脚本：
- 完成文件创建/修改后
- 用户给出反馈/纠正后
- 完成一个功能点后

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{
  "event": "tool_call",
  "tool": "Write",
  "input": {"file": "src/api.py"},
  "stage": "implement"
}'
```

### 记录用户反馈

当用户给出反馈时：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{
  "event": "user_feedback",
  "type": "correction",
  "content": "用户的反馈内容"
}'
```

## 三、会话结束时

### 自动 Finalize

下次 `--init` 会自动保存上次会话，无需手动触发。

### 手动触发（可选）

检测到结束信号时，可以手动调用：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --finalize '{
  "topic": "会话主题",
  "summary": "会话摘要"
}'
```

## 四、技能管理命令

### 查看学习到的知识

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py status
```

### 演化本能为技能

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py evolve
```

### 删除技能

当用户说 "删除技能: xxx" 时：

1. 先检查技能类型：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --check-skill <name>
```

2. 如果是演化技能，执行删除：
```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --delete-skill <name>
```

3. 如果不是演化技能，告诉用户如何手动删除。

**重要**：
- ❌ 不要直接使用 rm 或 Delete 工具删除技能文件
- ✅ 始终通过脚本删除，确保同步文件和索引正确处理

## 五、注意事项

1. 脚本调用过程不需要向用户详细展示
2. 如果脚本调用失败，不影响正常对话
3. 观察记录是可选的，不强制每次都记录
```

---

## 5. 配置文件

### 5.1 default_config.json

```json
{
  "version": "1.0",
  "enabled": true,
  "observation": {
    "enabled": true,
    "retention_days": 90,
    "max_file_size_mb": 10
  },
  "detection": {
    "enabled": true,
    "patterns": [
      "user_corrections",
      "error_resolutions",
      "tool_preferences",
      "project_conventions"
    ],
    "min_evidence_count": 2
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_apply_threshold": 0.7,
    "confidence_decay_rate": 0.02,
    "max_instincts": 100
  },
  "evolution": {
    "enabled": true,
    "cluster_threshold": 3,
    "auto_evolve": false,
    "retention_days": 180
  }
}
```

---

## 6. SKILL.md 入口文件

```markdown
---
name: continuous-learning
description: 为 Cursor 提供持续学习能力，从用户与 AI 的交互中自动提取可复用的知识
---

# Continuous Learning Skill

从用户与 AI 的交互中自动学习，生成可复用的技能文件。

## 安装后提示

✅ **Continuous Learning Skill 安装成功！**

### 快速开始

| 命令 | 说明 |
|------|------|
| `启用持续学习规则` | 开启自动学习功能（推荐） |
| `查看学习到的知识` | 查看本能和技能 |
| `演化本能` | 将本能聚合为技能 |

### 工作原理

1. **观察**：记录你与 AI 的交互过程
2. **检测**：识别可学习的模式（用户纠正、错误解决等）
3. **学习**：生成本能（原子化知识）
4. **演化**：将相关本能聚合为技能

### 用户命令

| 命令 | 描述 |
|------|------|
| `查看学习到的知识` | 显示所有本能和技能 |
| `查看本能状态` | 显示本能的置信度和证据 |
| `演化本能` | 将相关本能聚合为技能 |
| `删除技能: xxx` | 删除演化生成的技能 |
| `删除本能: xxx` | 删除特定本能 |

### 脚本命令

```bash
# 会话开始
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init

# 记录观察
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{...}'

# 会话结束
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --finalize '{...}'

# 查看本能
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py status

# 演化本能
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py evolve

# 删除技能
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py --delete-skill <name>
```

### 隐私说明

- 所有数据存储在本地
- 不上传任何信息到服务器
- 用户可以随时删除学习数据
```

---

## 7. 安装脚本

### 7.1 install.sh

```bash
#!/bin/bash
# Continuous Learning Skill 安装脚本

set -e

SKILL_NAME="continuous-learning"
CURSOR_SKILLS_DIR="$HOME/.cursor/skills"
CURSOR_RULES_DIR="$HOME/.cursor/rules"

echo "安装 Continuous Learning Skill..."

# 1. 创建目录
mkdir -p "$CURSOR_SKILLS_DIR/$SKILL_NAME/scripts"
mkdir -p "$CURSOR_SKILLS_DIR/$SKILL_NAME/rules"
mkdir -p "$CURSOR_SKILLS_DIR/${SKILL_NAME}-data"
mkdir -p "$CURSOR_RULES_DIR"

# 2. 复制脚本文件
cp scripts/*.py "$CURSOR_SKILLS_DIR/$SKILL_NAME/scripts/"

# 3. 复制配置文件
cp default_config.json "$CURSOR_SKILLS_DIR/$SKILL_NAME/"

# 4. 复制 SKILL.md
cp SKILL.md "$CURSOR_SKILLS_DIR/$SKILL_NAME/"

# 5. 复制规则文件
cp rules/continuous-learning.mdc "$CURSOR_RULES_DIR/"

echo "✅ 安装完成！"
echo ""
echo "已安装到: $CURSOR_SKILLS_DIR/$SKILL_NAME"
echo "规则文件: $CURSOR_RULES_DIR/continuous-learning.mdc"
echo ""
echo "下一步: 说 '启用持续学习规则' 开始使用"
```

---

## 8. 实施步骤

### 第一阶段：基础框架（1-2 天）

1. 创建目录结构
2. 实现 utils.py
3. 实现 observe.py 基础功能（init/record/finalize）
4. 创建规则文件
5. 创建 SKILL.md

### 第二阶段：模式检测（1-2 天）

1. 实现 analyze.py
2. 实现用户纠正检测
3. 实现错误解决检测
4. 实现工具偏好检测

### 第三阶段：本能管理（1-2 天）

1. 实现 instinct.py
2. 实现本能创建/更新/删除
3. 实现本能演化为技能
4. 实现技能同步到 Cursor

### 第四阶段：测试和优化（1-2 天）

1. 编写单元测试
2. 编写集成测试
3. 优化性能
4. 完善文档
