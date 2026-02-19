#!/usr/bin/env python3
"""
设置自动检索规则

为不同的 AI 助手生成自动检索规则文件，使 Memory Skill 能够在对话开始时自动触发检索。
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_project_root,
    get_skills_base_dir,
    SUPPORTED_SKILLS_DIRS
)


# 规则模板 - Cursor 格式 (.mdc)
CURSOR_RULE_TEMPLATE = '''---
description: Memory Skill 自动记忆规则 - 采用三层保障机制确保记忆数据完整性
globs:
alwaysApply: true
---

# Memory Skill 自动记忆规则

## 核心设计：三层保障机制

由于 AI 助手可能在任何时候被关闭，无法可靠地检测"对话结束"时刻。因此采用三层保障机制：

| 层级 | 机制 | 触发时机 | 可靠性 |
|------|------|----------|--------|
| 第一层 | 实时保存 | 每次有价值的对话后立即保存 | ⭐⭐⭐⭐⭐ |
| 第二层 | 会话结束处理 | 检测到结束信号时 | ⭐⭐⭐ |
| 第三层 | 下次会话检查 | 新会话开始时 | ⭐⭐⭐⭐⭐ |

## 一、检索触发（对话开始时）

**每次对话开始时**，执行以下操作：

### 1.1 会话检查（第三层兜底）

首先执行会话检查，获取数据摘要：
```bash
python3 {check_script_path}
```

### 1.2 信号词检测

检查用户的第一条消息是否包含以下信号词：

**强信号词（必须触发检索）**：
- 延续性：继续、上次、之前、昨天、我们讨论过、你记得、continue、last time、yesterday
- 偏好：我喜欢、我习惯、按照我的风格、I prefer、my style
- 项目：这个项目、我们的、当前、项目里、this project、our codebase

**排除信号词（不触发检索）**：
- 换个话题、新问题、另外、顺便问一下、change topic、new question

### 1.3 检索执行

如果检测到强信号词且无排除信号词：

1. 立即执行记忆检索：
   ```bash
   python3 {search_script_path} "用户问题关键词"
   ```

2. 将检索结果作为上下文注入回答

## 二、实时保存（第一层核心）

**不等到对话结束**，而是在每次有价值的对话后立即保存。

### 2.1 触发条件

- 用户表达了重要决策（"我们决定使用 FastAPI"）
- 用户表达了偏好（"我喜欢用 TypeScript"）
- 讨论了项目配置（"API 前缀是 /api/v2"）
- 完成了复杂任务（详细的实现方案）

### 2.2 不保存的内容

- **通用问答**：Python 怎么读文件、async/await 用法
- **临时调试**：错误排查、临时修复
- **闲聊内容**：与项目无关的对话
- **重复内容**：已经保存过的相同信息

### 2.3 保存执行

如果判断值得保存，立即提取关键信息并保存：

```bash
python3 {save_script_path} '{{"topic": "主题", "key_info": ["要点1", "要点2"], "tags": ["#tag1", "#tag2"]}}'
```

## 三、会话结束处理（第二层可选）

当检测到结束信号时，进行汇总保存。

### 结束信号
- 用户说"谢谢"、"好的"、"结束"、"拜拜"
- 用户说"thanks"、"done"、"bye"

**注意**：此层是可选的，因为 AI 助手可能在任何时候被关闭，不保证能执行。

## 四、用户控制

| 命令 | 效果 |
|------|------|
| `记住这个` / `save this` | 强制保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |
| `检查会话状态` | 执行会话检查 |

## 五、注意事项

- 检索失败不应阻塞正常对话
- 检索结果为空时正常继续对话
- 保存失败时提示用户但不影响对话
- 尊重用户的保存/不保存指令
- **优先实时保存**：不要等到对话结束才保存
'''

# 规则模板 - Claude 格式 (.md)
CLAUDE_RULE_TEMPLATE = '''---
name: memory-skill
description: Memory Skill 自动记忆规则 - 采用三层保障机制确保记忆数据完整性（实时保存、会话结束处理、下次会话检查）
allowed-tools: Shell, Read, Grep, Glob
---

# Memory Skill 自动记忆规则

## 核心设计：三层保障机制

由于 AI 助手可能在任何时候被关闭，无法可靠地检测"对话结束"时刻。因此采用三层保障机制：

| 层级 | 机制 | 触发时机 | 可靠性 |
|------|------|----------|--------|
| 第一层 | 实时保存 | 每次有价值的对话后立即保存 | ⭐⭐⭐⭐⭐ |
| 第二层 | 会话结束处理 | 检测到结束信号时 | ⭐⭐⭐ |
| 第三层 | 下次会话检查 | 新会话开始时 | ⭐⭐⭐⭐⭐ |

## 一、检索触发（对话开始时）

**每次对话开始时**，执行以下操作：

### 1.1 会话检查（第三层兜底）

首先执行会话检查，获取数据摘要：
```bash
python3 {check_script_path}
```

### 1.2 信号词检测

**强信号词（必须触发检索）**：
- 延续性：继续、上次、之前、昨天、我们讨论过、你记得、continue、last time、yesterday
- 偏好：我喜欢、我习惯、按照我的风格、I prefer、my style
- 项目：这个项目、我们的、当前、项目里、this project、our codebase

**排除信号词（不触发检索）**：
- 换个话题、新问题、另外、顺便问一下、change topic、new question

### 1.3 检索执行

如果检测到强信号词且无排除信号词：
```bash
python3 {search_script_path} "用户问题关键词"
```

## 二、实时保存（第一层核心）

**不等到对话结束**，而是在每次有价值的对话后立即保存。

### 触发条件
- 用户表达了重要决策
- 用户表达了偏好
- 讨论了项目配置
- 完成了复杂任务

### 保存执行
```bash
python3 {save_script_path} '{{"topic": "主题", "key_info": ["要点1", "要点2"], "tags": ["#tag1", "#tag2"]}}'
```

## 三、用户控制

| 命令 | 效果 |
|------|------|
| `记住这个` / `save this` | 强制保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |

## 四、注意事项

- 检索失败不应阻塞正常对话
- **优先实时保存**：不要等到对话结束才保存
- 尊重用户的保存/不保存指令
'''

# 通用规则模板 (.md)
GENERIC_RULE_TEMPLATE = '''# Memory Skill 自动记忆规则

## 核心设计：三层保障机制

由于 AI 助手可能在任何时候被关闭，无法可靠地检测"对话结束"时刻。因此采用三层保障机制：

| 层级 | 机制 | 触发时机 | 可靠性 |
|------|------|----------|--------|
| 第一层 | 实时保存 | 每次有价值的对话后立即保存 | ⭐⭐⭐⭐⭐ |
| 第二层 | 会话结束处理 | 检测到结束信号时 | ⭐⭐⭐ |
| 第三层 | 下次会话检查 | 新会话开始时 | ⭐⭐⭐⭐⭐ |

## 一、检索触发（对话开始时）

**每次对话开始时**，执行以下操作：

### 1.1 会话检查（第三层兜底）

首先执行会话检查，获取数据摘要：
```bash
python3 {check_script_path}
```

### 1.2 信号词检测

**强信号词（必须触发检索）**：
- 延续性：继续、上次、之前、昨天、我们讨论过、你记得、continue、last time、yesterday
- 偏好：我喜欢、我习惯、按照我的风格、I prefer、my style
- 项目：这个项目、我们的、当前、项目里、this project、our codebase

**排除信号词（不触发检索）**：
- 换个话题、新问题、另外、顺便问一下、change topic、new question

### 1.3 检索执行

如果检测到强信号词且无排除信号词：
```bash
python3 {search_script_path} "用户问题关键词"
```

## 二、实时保存（第一层核心）

**不等到对话结束**，而是在每次有价值的对话后立即保存。

### 触发条件
- 用户表达了重要决策
- 用户表达了偏好
- 讨论了项目配置
- 完成了复杂任务

### 保存执行
```bash
python3 {save_script_path} '{{"topic": "主题", "key_info": ["要点1", "要点2"], "tags": ["#tag1", "#tag2"]}}'
```

## 三、用户控制

| 命令 | 效果 |
|------|------|
| `记住这个` / `save this` | 强制保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |

## 四、注意事项

- 检索失败不应阻塞正常对话
- **优先实时保存**：不要等到对话结束才保存
- 尊重用户的保存/不保存指令
'''


def get_rule_config(assistant_type: str) -> dict:
    """
    获取不同 AI 助手的规则配置
    
    Args:
        assistant_type: AI 助手类型 ("cursor", "claude", "generic")
        
    Returns:
        规则配置字典
    """
    configs = {
        "cursor": {
            "dir_name": ".cursor",
            "rules_dir": "rules",
            "file_name": "memory-auto-retrieve.mdc",
            "template": CURSOR_RULE_TEMPLATE
        },
        "claude": {
            "dir_name": ".claude",
            "rules_dir": "rules",  # Claude 也可以使用 rules 目录
            "file_name": "memory-auto-retrieve.md",
            "template": CLAUDE_RULE_TEMPLATE
        },
        "generic": {
            "dir_name": ".ai",
            "rules_dir": "rules",
            "file_name": "memory-auto-retrieve.md",
            "template": GENERIC_RULE_TEMPLATE
        }
    }
    return configs.get(assistant_type, configs["generic"])


def detect_assistant_type(project_root: Path = None) -> str:
    """
    检测当前项目使用的 AI 助手类型
    
    Args:
        project_root: 项目根目录
        
    Returns:
        AI 助手类型
    """
    if project_root is None:
        project_root = get_project_root()
    
    skills_base = get_skills_base_dir(project_root)
    
    if skills_base == ".cursor":
        return "cursor"
    elif skills_base == ".claude":
        return "claude"
    else:
        return "generic"


def setup_auto_retrieve_rule(
    location: str = "project",
    assistant_type: str = None,
    force: bool = False
) -> dict:
    """
    设置自动检索规则
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        force: 是否强制覆盖已存在的规则文件
        
    Returns:
        设置结果
    """
    project_root = get_project_root()
    
    # 自动检测 AI 助手类型
    if assistant_type is None:
        assistant_type = detect_assistant_type(project_root)
    
    # 获取规则配置
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    if location == "global":
        base_dir = Path.home() / config["dir_name"]
    else:
        base_dir = project_root / config["dir_name"]
    
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
    if location == "global":
        scripts_dir = Path.home() / config["dir_name"] / "skills" / "memory" / "scripts"
    else:
        scripts_dir = project_root / config["dir_name"] / "skills" / "memory" / "scripts"
    
    search_script_path = str(scripts_dir / "search_memory.py")
    save_script_path = str(scripts_dir / "save_memory.py")
    check_script_path = str(scripts_dir / "check_session.py")
    
    # 生成规则内容
    rule_content = config["template"].format(
        search_script_path=search_script_path,
        save_script_path=save_script_path,
        check_script_path=check_script_path
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
        "message": f"自动检索规则已创建: {rule_file}"
    }


def remove_auto_retrieve_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    移除自动检索规则
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        
    Returns:
        移除结果
    """
    project_root = get_project_root()
    
    # 自动检测 AI 助手类型
    if assistant_type is None:
        assistant_type = detect_assistant_type(project_root)
    
    # 获取规则配置
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    if location == "global":
        base_dir = Path.home() / config["dir_name"]
    else:
        base_dir = project_root / config["dir_name"]
    
    rule_file = base_dir / config["rules_dir"] / config["file_name"]
    
    # 检查规则文件是否存在
    if not rule_file.exists():
        return {
            "success": False,
            "message": f"规则文件不存在: {rule_file}"
        }
    
    # 删除规则文件
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
        "message": f"自动检索规则已移除: {rule_file}"
    }


def check_auto_retrieve_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    检查自动检索规则状态
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        
    Returns:
        检查结果
    """
    project_root = get_project_root()
    
    # 自动检测 AI 助手类型
    if assistant_type is None:
        assistant_type = detect_assistant_type(project_root)
    
    # 获取规则配置
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    if location == "global":
        base_dir = Path.home() / config["dir_name"]
    else:
        base_dir = project_root / config["dir_name"]
    
    rule_file = base_dir / config["rules_dir"] / config["file_name"]
    
    exists = rule_file.exists()
    
    return {
        "success": True,
        "exists": exists,
        "enabled": exists,
        "rule_file": str(rule_file),
        "assistant_type": assistant_type,
        "location": location,
        "message": f"自动记忆检索{'已启用' if exists else '未启用'}"
    }


def update_auto_retrieve_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    更新自动检索规则到最新版本
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        
    Returns:
        更新结果
    """
    # 先检查规则是否存在
    check_result = check_auto_retrieve_rule(location, assistant_type)
    
    if not check_result["exists"]:
        return {
            "success": False,
            "message": "自动记忆检索未启用，请先使用 enable 操作启用"
        }
    
    # 强制覆盖更新
    return setup_auto_retrieve_rule(location, assistant_type, force=True)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": """用法:
  启用自动记忆检索: python3 setup_auto_retrieve.py '{"action": "enable"}'
  启用(全局): python3 setup_auto_retrieve.py '{"action": "enable", "location": "global"}'
  禁用自动记忆检索: python3 setup_auto_retrieve.py '{"action": "disable"}'
  更新规则: python3 setup_auto_retrieve.py '{"action": "update"}'
  检查状态: python3 setup_auto_retrieve.py '{"action": "check"}'
  指定助手类型: python3 setup_auto_retrieve.py '{"action": "enable", "assistant_type": "cursor"}'
  
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
    location = data.get("location", "project")
    assistant_type = data.get("assistant_type")
    force = data.get("force", False)
    
    # 支持旧的 action 名称（向后兼容）
    action_map = {
        "setup": "enable",
        "remove": "disable"
    }
    action = action_map.get(action, action)
    
    if action == "enable":
        result = setup_auto_retrieve_rule(location, assistant_type, force)
        if result["success"]:
            result["message"] = f"自动记忆检索已启用: {result['rule_file']}"
    elif action == "disable":
        result = remove_auto_retrieve_rule(location, assistant_type)
        if result["success"]:
            result["message"] = "自动记忆检索已禁用"
    elif action == "update":
        result = update_auto_retrieve_rule(location, assistant_type)
        if result["success"]:
            result["message"] = f"自动记忆检索规则已更新: {result['rule_file']}"
    elif action == "check":
        result = check_auto_retrieve_rule(location, assistant_type)
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
