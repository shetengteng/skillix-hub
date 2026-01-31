#!/usr/bin/env python3
"""
Behavior Prediction Skill - 工具函数

提供数据读写、配置管理等通用功能。
支持多种 AI 助手：Cursor, Claude, Copilot, Codeium 等。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# 支持的 AI 助手 skills 目录名称（按优先级排序）
SUPPORTED_SKILLS_DIRS = [".cursor", ".claude", ".ai", ".copilot", ".codeium"]

# 获取 Skill 目录（相对于脚本位置）
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent


def get_project_root() -> Path:
    """
    获取项目根目录
    
    查找顺序：
    1. 从脚本位置向上查找支持的 AI 助手目录或 .git 目录
    2. 从当前工作目录向上查找支持的 AI 助手目录或 .git 目录
    """
    # 首先尝试从脚本位置向上查找
    script_path = Path(__file__).resolve()
    current = script_path.parent
    while current != current.parent:
        # 检查是否存在任何支持的 AI 助手目录
        for skills_dir in SUPPORTED_SKILLS_DIRS:
            if (current / skills_dir).exists():
                return current
        if (current / ".git").exists():
            return current
        current = current.parent
    
    # 否则从当前工作目录向上查找
    current = Path.cwd()
    while current != current.parent:
        for skills_dir in SUPPORTED_SKILLS_DIRS:
            if (current / skills_dir).exists():
                return current
        if (current / ".git").exists():
            return current
        current = current.parent
    
    # 如果没找到，返回当前目录
    return Path.cwd()


def get_skills_base_dir(project_root: Path = None) -> str:
    """
    获取当前项目使用的 AI 助手目录名称
    
    Args:
        project_root: 项目根目录，如果为 None 则自动获取
        
    Returns:
        AI 助手目录名称（如 ".cursor", ".ai" 等）
    """
    if project_root is None:
        project_root = get_project_root()
    
    # 按优先级检查存在的目录
    for skills_dir in SUPPORTED_SKILLS_DIRS:
        if (project_root / skills_dir).exists():
            return skills_dir
    
    # 默认使用 .cursor（向后兼容）
    return ".cursor"


def get_data_dir(location: str = "project") -> Path:
    """
    获取数据目录
    
    Args:
        location: "project" 或 "global"
    
    优先级：
    1. 项目级：<project>/<ai_dir>/skills/behavior-prediction-data/
    2. 全局级：~/<ai_dir>/skills/behavior-prediction-data/
    
    支持的 AI 助手目录：.cursor, .claude, .ai, .copilot, .codeium
    """
    if location == "global":
        # 全局目录优先使用 .cursor，保持向后兼容
        global_base = ".cursor"
        for skills_dir in SUPPORTED_SKILLS_DIRS:
            if (Path.home() / skills_dir).exists():
                global_base = skills_dir
                break
        return Path.home() / global_base / "skills" / "behavior-prediction-data"
    else:
        project_root = get_project_root()
        skills_base = get_skills_base_dir(project_root)
        return project_root / skills_base / "skills" / "behavior-prediction-data"


# 默认使用项目级数据目录
DATA_DIR = get_data_dir("project")


def ensure_data_dirs():
    """确保数据目录存在"""
    (DATA_DIR / "actions").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "patterns").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "stats").mkdir(parents=True, exist_ok=True)


def load_json(file_path: Path, default: Optional[dict] = None) -> dict:
    """
    加载 JSON 文件
    
    Args:
        file_path: JSON 文件路径
        default: 文件不存在或解析失败时返回的默认值
    
    Returns:
        解析后的字典
    """
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return default or {}
    return default or {}


def save_json(file_path: Path, data: dict):
    """
    保存 JSON 文件
    
    Args:
        file_path: JSON 文件路径
        data: 要保存的数据
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def get_today() -> str:
    """获取今天的日期字符串 (YYYY-MM-DD)"""
    return datetime.now().strftime("%Y-%m-%d")


def get_timestamp() -> str:
    """获取当前 ISO8601 时间戳"""
    return datetime.now().isoformat() + "Z"


def load_config() -> dict:
    """
    加载用户配置
    
    优先级：用户配置 > 默认配置
    """
    # 默认配置
    default_config_file = SKILL_DIR / "default_config.json"
    default_config = load_json(default_config_file, {
        "version": "1.0",
        "enabled": True,
        "prediction": {
            "enabled": True,
            "suggest_threshold": 0.5,
            "auto_execute_threshold": 0.95,
            "max_suggestions": 3
        },
        "recording": {
            "enabled": True,
            "retention_days": 90
        },
        "learning": {
            "enabled": True,
            "min_samples_for_prediction": 3
        }
    })
    
    # 用户配置
    user_config_file = DATA_DIR / "config.json"
    user_config = load_json(user_config_file, {})
    
    # 合并配置（用户配置覆盖默认配置）
    def deep_merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    return deep_merge(default_config, user_config)


def load_transition_matrix() -> dict:
    """
    加载转移矩阵
    
    Returns:
        {
            "version": "1.0",
            "matrix": {
                "action_a": {
                    "action_b": {"count": 10, "probability": 0.5},
                    ...
                },
                ...
            },
            "total_transitions": 100
        }
    """
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
    """
    加载动作类型注册表
    
    Returns:
        {
            "version": "1.0",
            "types": {
                "create_file": {
                    "description": "创建新文件",
                    "source": "predefined",
                    "first_seen": "2026-01-31",
                    "count": 10
                },
                ...
            }
        }
    """
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


def register_action_type(
    action_type: str,
    description: str = "",
    is_new: bool = False
):
    """
    注册动作类型
    
    Args:
        action_type: 动作类型名称
        description: 类型描述（新类型时提供）
        is_new: 是否是新类型
    """
    registry = load_types_registry()
    
    if action_type not in registry["types"]:
        registry["types"][action_type] = {
            "description": description,
            "source": "auto_generated" if is_new else "predefined",
            "first_seen": get_today(),
            "count": 0
        }
    
    # 更新计数和最后使用时间
    registry["types"][action_type]["count"] = \
        registry["types"][action_type].get("count", 0) + 1
    registry["types"][action_type]["last_seen"] = get_today()
    
    # 如果提供了描述且原来没有，更新描述
    if description and not registry["types"][action_type].get("description"):
        registry["types"][action_type]["description"] = description
    
    save_types_registry(registry)


def get_recent_actions(limit: int = 10) -> list:
    """
    获取最近的动作序列
    
    Args:
        limit: 返回的最大动作数量
    
    Returns:
        动作类型列表，如 ["create_file", "edit_file", "run_test"]
    """
    today = get_today()
    log_file = DATA_DIR / "actions" / f"{today}.json"
    
    log_data = load_json(log_file, {"actions": []})
    actions = log_data.get("actions", [])
    
    # 返回最近的动作类型
    recent = [a.get("type", "unknown") for a in actions[-limit:]]
    return recent


def collect_context() -> dict:
    """
    收集当前上下文信息
    
    Returns:
        上下文信息字典
    """
    context = {
        "date": get_today(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "has_data": (DATA_DIR / "actions").exists()
    }
    
    # 可以扩展更多上下文信息
    # 如：当前项目类型、最近修改的文件类型等
    
    return context


# 预定义的动作类型（作为参考）
PREDEFINED_ACTION_TYPES = {
    # 文件操作
    "create_file": "创建新文件",
    "edit_file": "修改已有文件",
    "delete_file": "删除文件",
    "rename_file": "重命名文件",
    "read_file": "读取文件",
    
    # 代码相关
    "write_code": "编写代码",
    "write_test": "编写测试",
    "refactor": "重构代码",
    "fix_bug": "修复 bug",
    
    # 命令执行
    "run_test": "运行测试",
    "run_build": "构建项目",
    "run_server": "启动服务",
    "install_dep": "安装依赖",
    "shell_command": "执行 Shell 命令",
    
    # Git 操作
    "git_add": "暂存文件",
    "git_commit": "提交代码",
    "git_push": "推送代码",
    "git_pull": "拉取代码",
    "git_merge": "合并分支",
    
    # 搜索操作
    "search_code": "搜索代码",
    "search_file": "搜索文件",
}


if __name__ == "__main__":
    # 测试工具函数
    print(f"Skill 目录: {SKILL_DIR}")
    print(f"数据目录: {DATA_DIR}")
    print(f"今天日期: {get_today()}")
    print(f"当前时间戳: {get_timestamp()}")
    
    # 确保目录存在
    ensure_data_dirs()
    print("数据目录已创建")
    
    # 加载配置
    config = load_config()
    print(f"配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
