#!/usr/bin/env python3
"""
设置自动行为记录规则

为不同的 AI 助手生成自动行为记录规则文件，使 Behavior Prediction Skill 能够自动记录用户行为。
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
description: Behavior Prediction Skill 自动行为记录规则 - 记录用户行为并提供智能预测
globs:
alwaysApply: true
---

# Behavior Prediction Skill 自动行为记录规则

## 功能概述

该规则使 AI 助手能够：
1. **自动记录**用户在 AI 助手中执行的每个动作
2. **学习模式**：分析行为序列，发现 A → B 的关联模式
3. **智能预测**：当用户执行动作 A 时，预测并建议动作 B

## 一、行为记录（每次工具调用后）

**每次执行工具调用后**，需要记录该动作。

### 1.1 动作分类

根据工具调用的类型和意图，将动作分类为以下类型之一：

**文件操作**：
- `create_file`: 创建新文件（使用 Write 工具创建）
- `edit_file`: 修改已有文件（使用 StrReplace 工具）
- `delete_file`: 删除文件（使用 Delete 工具）
- `read_file`: 读取文件（使用 Read 工具）

**代码相关**：
- `write_code`: 编写代码
- `write_test`: 编写测试
- `refactor`: 重构代码
- `fix_bug`: 修复 bug

**命令执行**：
- `run_test`: 运行测试
- `run_build`: 构建项目
- `run_server`: 启动服务
- `install_dep`: 安装依赖
- `shell_command`: 其他 Shell 命令

**Git 操作**：
- `git_add`: 暂存文件
- `git_commit`: 提交代码
- `git_push`: 推送代码
- `git_pull`: 拉取代码

**搜索操作**：
- `search_code`: 搜索代码（使用 Grep 工具）
- `search_file`: 搜索文件（使用 Glob 工具）

**可以创建新类型**：如 `train_model`、`deploy_app`、`generate_docs` 等

### 1.2 记录执行

每次工具调用完成后，执行记录：

```bash
python3 {record_script_path} '{{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {{
    "file_path": "相关文件路径（如有）",
    "command": "执行的命令（如有）"
  }},
  "classification": {{
    "confidence": 0.95,
    "is_new_type": false,
    "description": "类型描述（新类型时）"
  }}
}}'
```

### 1.3 分类要求

1. **理解语义**：不只看工具名称，要理解实际意图
2. **结合上下文**：参考用户消息理解意图
3. **可以创建新类型**：如果现有类型不匹配，可以创建新类型
4. **输出置信度**：评估分类的确信程度

## 二、智能预测（可选）

当完成一个动作后，可以获取统计数据来提供预测建议。

### 2.1 获取统计

```bash
python3 {statistics_script_path} '{{"current_action": "刚完成的动作类型"}}'
```

### 2.2 预测决策

| 置信度 | 条件 | 建议方式 |
|--------|------|----------|
| > 0.9 | 历史概率高 + 上下文支持 + 样本量大 | 肯定语气 |
| 0.7-0.9 | 历史概率中等或上下文部分支持 | 建议语气 |
| 0.5-0.7 | 历史概率较低或样本量小 | 询问语气 |
| < 0.5 | 数据不足或上下文不支持 | 不建议 |

### 2.3 预测展示

如果有高置信度的预测，可以展示建议：

```
✨ 基于你的习惯，你可能想要：
→ 运行测试 (置信度: 85%)

要执行吗？[Y/n]
```

## 三、会话管理

### 3.1 会话开始检查

每次新会话开始时，建议执行检查：

```bash
python3 {check_script_path}
```

### 3.2 会话结束处理（可选）

当检测到会话结束信号时，可以执行会话总结：

```bash
python3 {finalize_script_path} '{{
  "actions_summary": [...],
  "start_time": "...",
  "end_time": "..."
}}'
```

## 四、用户命令

| 命令 | 效果 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `预测下一步` | 手动触发预测 |
| `查看行为统计` | 显示统计数据概览 |
| `清除行为记录` | 删除所有行为记录 |

## 五、注意事项

- 记录失败不应阻塞正常对话
- 预测建议是可选的，不强制执行
- 尊重用户的选择，不强制预测
- 所有数据存储在本地，不上传到服务器
'''

# 规则模板 - Claude 格式 (.md)
CLAUDE_RULE_TEMPLATE = '''---
name: behavior-prediction
description: Behavior Prediction Skill 自动行为记录规则 - 记录用户行为并提供智能预测
allowed-tools: Shell, Read, Grep, Glob, Write, StrReplace, Delete
---

# Behavior Prediction Skill 自动行为记录规则

## 功能概述

该规则使 AI 助手能够：
1. **自动记录**用户在 AI 助手中执行的每个动作
2. **学习模式**：分析行为序列，发现 A → B 的关联模式
3. **智能预测**：当用户执行动作 A 时，预测并建议动作 B

## 一、行为记录（每次工具调用后）

每次执行工具调用后，记录该动作：

```bash
python3 {record_script_path} '{{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {{}},
  "classification": {{"confidence": 0.95, "is_new_type": false}}
}}'
```

### 动作类型

- 文件操作：`create_file`, `edit_file`, `delete_file`, `read_file`
- 代码相关：`write_code`, `write_test`, `refactor`, `fix_bug`
- 命令执行：`run_test`, `run_build`, `run_server`, `install_dep`
- Git 操作：`git_add`, `git_commit`, `git_push`, `git_pull`
- 搜索操作：`search_code`, `search_file`
- 可以创建新类型

## 二、智能预测（可选）

获取统计数据来提供预测建议：

```bash
python3 {statistics_script_path} '{{"current_action": "动作类型"}}'
```

## 三、用户命令

| 命令 | 效果 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `预测下一步` | 手动触发预测 |
| `查看行为统计` | 显示统计数据概览 |

## 四、注意事项

- 记录失败不应阻塞正常对话
- 预测建议是可选的，不强制执行
'''

# 通用规则模板 (.md)
GENERIC_RULE_TEMPLATE = '''# Behavior Prediction Skill 自动行为记录规则

## 功能概述

该规则使 AI 助手能够：
1. **自动记录**用户在 AI 助手中执行的每个动作
2. **学习模式**：分析行为序列，发现 A → B 的关联模式
3. **智能预测**：当用户执行动作 A 时，预测并建议动作 B

## 一、行为记录

每次执行工具调用后，记录该动作：

```bash
python3 {record_script_path} '{{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {{}},
  "classification": {{"confidence": 0.95, "is_new_type": false}}
}}'
```

## 二、智能预测

获取统计数据来提供预测建议：

```bash
python3 {statistics_script_path} '{{"current_action": "动作类型"}}'
```

## 三、用户命令

| 命令 | 效果 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `预测下一步` | 手动触发预测 |
| `查看行为统计` | 显示统计数据概览 |
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
            "file_name": "behavior-prediction-auto-record.mdc",
            "template": CURSOR_RULE_TEMPLATE
        },
        "claude": {
            "dir_name": ".claude",
            "rules_dir": "rules",
            "file_name": "behavior-prediction-auto-record.md",
            "template": CLAUDE_RULE_TEMPLATE
        },
        "generic": {
            "dir_name": ".ai",
            "rules_dir": "rules",
            "file_name": "behavior-prediction-auto-record.md",
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


def setup_auto_record_rule(
    location: str = "project",
    assistant_type: str = None,
    force: bool = False
) -> dict:
    """
    设置自动行为记录规则
    
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
    
    record_script_path = str(scripts_dir / "record_action.py")
    statistics_script_path = str(scripts_dir / "get_statistics.py")
    check_script_path = str(scripts_dir / "check_last_session.py")
    finalize_script_path = str(scripts_dir / "finalize_session.py")
    
    # 生成规则内容
    rule_content = config["template"].format(
        record_script_path=record_script_path,
        statistics_script_path=statistics_script_path,
        check_script_path=check_script_path,
        finalize_script_path=finalize_script_path
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
        "message": f"自动行为记录规则已创建: {rule_file}"
    }


def remove_auto_record_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    移除自动行为记录规则
    
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
        "message": f"自动行为记录规则已移除: {rule_file}"
    }


def check_auto_record_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    检查自动行为记录规则状态
    
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
        "message": f"自动行为记录{'已启用' if exists else '未启用'}"
    }


def update_auto_record_rule(
    location: str = "project",
    assistant_type: str = None
) -> dict:
    """
    更新自动行为记录规则到最新版本
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        
    Returns:
        更新结果
    """
    # 先检查规则是否存在
    check_result = check_auto_record_rule(location, assistant_type)
    
    if not check_result["exists"]:
        return {
            "success": False,
            "message": "自动行为记录未启用，请先使用 enable 操作启用"
        }
    
    # 强制覆盖更新
    return setup_auto_record_rule(location, assistant_type, force=True)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": """用法:
  启用自动行为记录: python3 setup_auto_record.py '{"action": "enable"}'
  启用(全局): python3 setup_auto_record.py '{"action": "enable", "location": "global"}'
  禁用自动行为记录: python3 setup_auto_record.py '{"action": "disable"}'
  更新规则: python3 setup_auto_record.py '{"action": "update"}'
  检查状态: python3 setup_auto_record.py '{"action": "check"}'
  指定助手类型: python3 setup_auto_record.py '{"action": "enable", "assistant_type": "cursor"}'
  
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
    
    if action == "enable":
        result = setup_auto_record_rule(location, assistant_type, force)
        if result["success"]:
            result["message"] = f"""✅ 自动行为记录已启用！

规则文件: {result['rule_file']}

现在 AI 会自动：
• 记录你的每次操作
• 学习你的行为模式
• 在适当时候提供预测建议

使用一段时间后，说「查看我的行为模式」查看学习结果。"""
    elif action == "disable":
        result = remove_auto_record_rule(location, assistant_type)
        if result["success"]:
            result["message"] = """✅ 自动行为记录已禁用

AI 将不再自动记录你的操作。
已有的行为记录不会被删除，你可以随时重新启用。"""
    elif action == "update":
        result = update_auto_record_rule(location, assistant_type)
        if result["success"]:
            result["message"] = f"""✅ 自动行为记录规则已更新！

规则文件: {result['rule_file']}"""
    elif action == "check":
        result = check_auto_record_rule(location, assistant_type)
        if result["success"]:
            if result["enabled"]:
                result["message"] = f"""✅ 自动行为记录已启用

规则文件: {result['rule_file']}

AI 正在自动记录你的操作并学习行为模式。"""
            else:
                result["message"] = """❌ 自动行为记录未启用

说「启用自动行为记录」来开启此功能。"""
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
