#!/usr/bin/env python3
"""
设置持续学习规则

为不同的 AI 助手生成持续学习规则文件，使 Continuous Learning Skill 能够自动记录和学习。
"""

import sys
import json
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))


# ─────────────────────────────────────────────
# 规则模板 - Cursor 格式 (.mdc)
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# 规则模板 - Claude 格式 (.md)
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# 通用规则模板 (.md)
# ─────────────────────────────────────────────

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


def get_project_root() -> Path:
    """获取项目根目录"""
    current = Path.cwd()
    
    while current != current.parent:
        if (current / ".cursor").exists() or (current / ".git").exists():
            return current
        current = current.parent
    
    return Path.cwd()


def setup_rule(location: str = "global", assistant_type: str = None, force: bool = False) -> dict:
    """
    设置持续学习规则
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
        force: 是否强制覆盖已存在的规则文件
    
    Returns:
        设置结果
    """
    if assistant_type is None:
        assistant_type = detect_assistant_type()
    
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    if location == "global":
        base_dir = Path.home() / config["dir_name"]
    else:
        base_dir = get_project_root() / config["dir_name"]
    
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
        scripts_dir = base_dir / "skills" / "continuous-learning" / "scripts"
    else:
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
    """
    移除持续学习规则
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
    
    Returns:
        移除结果
    """
    if assistant_type is None:
        assistant_type = detect_assistant_type()
    
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    if location == "global":
        base_dir = Path.home() / config["dir_name"]
    else:
        base_dir = get_project_root() / config["dir_name"]
    
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
    """
    检查持续学习规则状态
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
    
    Returns:
        检查结果
    """
    if assistant_type is None:
        assistant_type = detect_assistant_type()
    
    config = get_rule_config(assistant_type)
    
    # 确定规则文件路径
    if location == "global":
        base_dir = Path.home() / config["dir_name"]
    else:
        base_dir = get_project_root() / config["dir_name"]
    
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
    """
    更新持续学习规则到最新版本
    
    Args:
        location: 规则位置 ("project" 或 "global")
        assistant_type: AI 助手类型，如果为 None 则自动检测
    
    Returns:
        更新结果
    """
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
  启用(项目): python3 setup_rule.py '{"action": "enable", "location": "project"}'
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
