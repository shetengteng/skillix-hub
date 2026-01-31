#!/usr/bin/env python3
"""
设置行为预测规则

为不同的 AI 助手生成行为预测规则文件，使 Behavior Prediction Skill 能够自动记录会话和预测行为。
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import get_project_root, get_ai_dir, SUPPORTED_AI_DIRS


# 规则模板 - Cursor 格式 (.mdc)
CURSOR_RULE_TEMPLATE = '''---
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
python3 {hook_script_path} --init
```

### 1.3 返回的信息

Hook 返回用户的行为模式和偏好：

```json
{{
  "status": "success",
  "ai_summary": {{
    "summary": {{
      "description": "这是一个活跃了 15 天的用户，主要从事 API 开发、测试相关工作"
    }},
    "predictions": {{
      "rules": [
        {{
          "when": "用户完成 implement 阶段后",
          "then": "85% 概率会进入 test 阶段",
          "action": "主动询问：要运行测试验证一下吗？"
        }}
      ]
    }}
  }},
  "suggestions": [
    "你常见的工作流程：implement → test → commit",
    "你最常使用的技术：Python, FastAPI"
  ]
}}
```

### 1.4 如何使用

获取用户行为模式后，AI 应该：
1. **了解用户习惯**：根据 `ai_summary` 了解用户的工作风格
2. **主动预测**：当用户完成某个阶段后，参考 `predictions.rules` 主动提供建议
3. **调整交互**：根据用户偏好调整交互方式

## 二、会话过程中

### 2.1 工作流程阶段识别

在会话过程中，AI 需要识别用户当前处于哪个工作流程阶段：

| 阶段 | 识别特征 |
|------|----------|
| design | 讨论方案、设计文档、架构规划 |
| implement | 编写代码、创建文件、实现功能 |
| test | 编写测试、运行测试、验证功能 |
| debug | 调试问题、修复 bug、排查错误 |
| refactor | 重构代码、优化性能、改进结构 |
| document | 编写文档、添加注释、更新 README |
| deploy | 部署应用、发布版本 |
| review | 代码审查、检查质量 |
| commit | 提交代码、推送更改 |

### 2.2 主动预测与自动执行

当用户完成某个阶段后，根据行为模式和置信度决定是否自动执行：

#### 自动执行判断逻辑

```
置信度 >= 95%  且 动作在允许列表中  → 直接执行，无需确认
置信度 >= 85%  且 动作在允许列表中  → 询问确认后执行
置信度 < 85%   → 仅提供建议，不自动执行
动作在禁止列表中 → 永远不自动执行
```

#### 允许自动执行的动作

| 动作 | 命令示例 | 说明 |
|------|----------|------|
| run_test | `pytest` | 运行测试 |
| run_lint | `ruff check .` | 代码检查 |
| git_status | `git status` | 查看状态 |
| git_add | `git add -A` | 暂存更改 |

#### 禁止自动执行的动作

| 动作 | 说明 |
|------|------|
| delete_file | 删除文件（危险操作） |
| git_push | 推送代码（不可逆） |
| git_reset | 重置代码（危险操作） |
| deploy | 部署应用（生产环境） |
| rm, drop | 任何删除操作 |

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
python3 {hook_script_path} --finalize '{{
  "session_summary": {{
    "topic": "会话主题（一句话描述）",
    "goals": ["目标1", "目标2"],
    "completed_tasks": ["完成的任务1", "完成的任务2"],
    "technologies_used": ["Python", "FastAPI", "pytest"],
    "workflow_stages": ["design", "implement", "test"],
    "tags": ["#api", "#backend", "#testing"]
  }},
  "operations": {{
    "files": {{
      "created": ["src/api/auth.py", "tests/test_auth.py"],
      "modified": ["src/main.py"],
      "deleted": []
    }},
    "commands": [
      {{"command": "pytest tests/", "type": "run_test", "exit_code": 0}}
    ]
  }},
  "conversation": {{
    "user_messages": ["用户消息1", "用户消息2"],
    "message_count": 5
  }},
  "time": {{
    "start": "会话开始时间 ISO8601",
    "end": "会话结束时间 ISO8601"
  }}
}}'
```

### 3.3 会话摘要生成指南

生成会话摘要时，请提取以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| topic | 会话主题（一句话） | "用户认证功能开发" |
| goals | 用户的目标 | ["创建认证 API", "实现 JWT"] |
| completed_tasks | 完成的具体任务 | ["创建 auth.py", "添加测试"] |
| technologies_used | 使用的技术/工具 | ["FastAPI", "PyJWT", "pytest"] |
| workflow_stages | 经历的工作流程阶段 | ["implement", "test"] |
| tags | 标签（以 # 开头） | ["#auth", "#api"] |

## 四、注意事项

1. **会话开始时调用 --init**：加载用户行为模式
2. **会话结束时调用 --finalize**：记录会话并更新模式
3. **主动预测**：根据行为模式，在适当时机主动提供建议
4. **自动执行**：高置信度时可自动执行安全操作
5. **静默执行**：hook 调用过程不需要向用户详细展示
6. **失败不阻塞**：如果 hook 调用失败，不影响正常对话
7. **安全优先**：危险操作永远不自动执行
'''

# 规则模板 - Claude 格式 (.md)
CLAUDE_RULE_TEMPLATE = '''---
name: behavior-prediction
description: 行为预测 V2 - 会话生命周期管理，自动记录会话和预测用户行为
allowed-tools: Shell, Read, Grep, Glob
---

# 行为预测规则

> **版本**: v2.0
> **说明**: 统一管理会话全生命周期的行为记录和预测

## 一、会话开始时

**每次新会话开始时**（用户发送第一条消息），调用 init hook：

```bash
python3 {hook_script_path} --init
```

返回用户的行为模式和偏好，AI 应该根据这些信息了解用户习惯并主动提供建议。

## 二、会话过程中

识别用户当前处于哪个工作流程阶段：
- design: 讨论方案、设计文档
- implement: 编写代码、创建文件
- test: 编写测试、运行测试
- debug: 调试问题、修复 bug
- refactor: 重构代码、优化性能
- document: 编写文档
- commit: 提交代码

根据行为模式和置信度决定是否自动执行：
- 置信度 >= 95% 且安全操作 → 直接执行
- 置信度 >= 85% 且安全操作 → 询问确认
- 置信度 < 85% → 仅提供建议

## 三、会话结束时

当检测到结束信号（谢谢、好的、结束、thanks、done、bye）时，调用 finalize hook：

```bash
python3 {hook_script_path} --finalize '{{
  "session_summary": {{"topic": "主题", "workflow_stages": ["implement", "test"]}},
  "time": {{"start": "ISO8601", "end": "ISO8601"}}
}}'
```

## 四、注意事项

- 静默执行 hook 调用
- 失败不阻塞正常对话
- 危险操作永远不自动执行
'''

# 通用规则模板 (.md)
GENERIC_RULE_TEMPLATE = '''# 行为预测规则

> **版本**: v2.0
> **说明**: 统一管理会话全生命周期的行为记录和预测

## 一、会话开始时

**每次新会话开始时**，调用 init hook：

```bash
python3 {hook_script_path} --init
```

返回用户的行为模式和偏好。

## 二、会话过程中

识别用户当前处于哪个工作流程阶段（design, implement, test, debug, refactor, document, commit）。

根据行为模式和置信度决定是否自动执行安全操作。

## 三、会话结束时

当检测到结束信号时，调用 finalize hook：

```bash
python3 {hook_script_path} --finalize '{{...session_data...}}'
```

## 四、注意事项

- 静默执行 hook 调用
- 失败不阻塞正常对话
- 危险操作永远不自动执行
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
            "file_name": "behavior-prediction.mdc",
            "template": CURSOR_RULE_TEMPLATE
        },
        "claude": {
            "dir_name": ".claude",
            "rules_dir": "rules",
            "file_name": "behavior-prediction.md",
            "template": CLAUDE_RULE_TEMPLATE
        },
        "generic": {
            "dir_name": ".ai",
            "rules_dir": "rules",
            "file_name": "behavior-prediction.md",
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
    
    ai_dir = get_ai_dir(project_root)
    
    if ai_dir == ".cursor":
        return "cursor"
    elif ai_dir == ".claude":
        return "claude"
    else:
        return "generic"


def setup_rule(
    location: str = "project",
    assistant_type: str = None,
    force: bool = False
) -> dict:
    """
    设置行为预测规则
    
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
        scripts_dir = Path.home() / config["dir_name"] / "skills" / "behavior-prediction" / "scripts"
    else:
        scripts_dir = project_root / config["dir_name"] / "skills" / "behavior-prediction" / "scripts"
    
    hook_script_path = str(scripts_dir / "hook.py")
    
    # 生成规则内容
    rule_content = config["template"].format(
        hook_script_path=hook_script_path
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
        "message": f"行为预测规则已创建: {rule_file}"
    }


def remove_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    移除行为预测规则
    
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
        "message": f"行为预测规则已移除: {rule_file}"
    }


def check_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    检查行为预测规则状态
    
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
        "message": f"行为预测规则{'已启用' if exists else '未启用'}"
    }


def update_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    更新行为预测规则到最新版本
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        
    Returns:
        更新结果
    """
    # 先检查规则是否存在
    check_result = check_rule(location, assistant_type)
    
    if not check_result["exists"]:
        return {
            "success": False,
            "message": "行为预测规则未启用，请先使用 enable 操作启用"
        }
    
    # 强制覆盖更新
    return setup_rule(location, assistant_type, force=True)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": """用法:
  启用行为预测规则: python3 setup_rule.py '{"action": "enable"}'
  启用(全局): python3 setup_rule.py '{"action": "enable", "location": "global"}'
  禁用行为预测规则: python3 setup_rule.py '{"action": "disable"}'
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
        result = setup_rule(location, assistant_type, force)
        if result["success"]:
            result["message"] = f"行为预测规则已启用: {result['rule_file']}"
    elif action == "disable":
        result = remove_rule(location, assistant_type)
        if result["success"]:
            result["message"] = "行为预测规则已禁用"
    elif action == "update":
        result = update_rule(location, assistant_type)
        if result["success"]:
            result["message"] = f"行为预测规则已更新: {result['rule_file']}"
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
