#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 工具函数

提供数据读写、配置管理等通用功能。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# 支持的 AI 助手目录（按优先级排序）
SUPPORTED_AI_DIRS = [".cursor", ".claude", ".ai", ".copilot", ".codeium"]

# Skill 目录
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent


def get_project_root() -> Path:
    """
    获取项目根目录
    
    查找顺序：
    1. 从脚本位置向上查找 AI 助手目录或 .git 目录
    2. 从当前工作目录向上查找
    """
    # 从脚本位置向上查找
    current = Path(__file__).resolve().parent
    while current != current.parent:
        for ai_dir in SUPPORTED_AI_DIRS:
            if (current / ai_dir).exists():
                return current
        if (current / ".git").exists():
            return current
        current = current.parent
    
    # 从当前工作目录向上查找
    current = Path.cwd()
    while current != current.parent:
        for ai_dir in SUPPORTED_AI_DIRS:
            if (current / ai_dir).exists():
                return current
        if (current / ".git").exists():
            return current
        current = current.parent
    
    return Path.cwd()


def get_ai_dir(project_root: Path = None) -> str:
    """获取当前使用的 AI 助手目录名称"""
    if project_root is None:
        project_root = get_project_root()
    
    for ai_dir in SUPPORTED_AI_DIRS:
        if (project_root / ai_dir).exists():
            return ai_dir
    
    return ".cursor"


def get_data_dir(location: str = "project") -> Path:
    """
    获取数据目录
    
    Args:
        location: "project" 或 "global"
    
    Returns:
        数据目录路径
    """
    if location == "global":
        ai_dir = ".cursor"
        for d in SUPPORTED_AI_DIRS:
            if (Path.home() / d).exists():
                ai_dir = d
                break
        return Path.home() / ai_dir / "skills" / "behavior-prediction-data"
    else:
        project_root = get_project_root()
        ai_dir = get_ai_dir(project_root)
        return project_root / ai_dir / "skills" / "behavior-prediction-data"


# 默认数据目录
DATA_DIR = get_data_dir("project")


def ensure_dir(path: Path):
    """确保目录存在"""
    if path.suffix:  # 如果是文件路径
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path.mkdir(parents=True, exist_ok=True)


def ensure_data_dirs():
    """确保所有数据目录存在"""
    (DATA_DIR / "sessions").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "patterns").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "profile").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "index").mkdir(parents=True, exist_ok=True)


def load_json(file_path: Path, default: Optional[dict] = None) -> dict:
    """加载 JSON 文件"""
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return default or {}
    return default or {}


def save_json(file_path: Path, data: dict):
    """保存 JSON 文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def get_today() -> str:
    """获取今天的日期 (YYYY-MM-DD)"""
    return datetime.now().strftime("%Y-%m-%d")


def get_month() -> str:
    """获取当前月份 (YYYY-MM)"""
    return datetime.now().strftime("%Y-%m")


def get_timestamp() -> str:
    """获取当前 ISO8601 时间戳"""
    return datetime.now().isoformat()


def load_config() -> dict:
    """加载配置（默认配置 + 用户配置）"""
    # 默认配置
    default_config_file = SKILL_DIR / "default_config.json"
    default_config = load_json(default_config_file, {
        "version": "2.0",
        "enabled": True,
        "recording": {"enabled": True, "retention_days": 90},
        "patterns": {"extraction_enabled": True, "min_sessions_for_pattern": 3},
        "profile": {"auto_update": True, "update_interval_sessions": 10},
        "prediction": {"enabled": True, "suggest_threshold": 0.5, "max_suggestions": 3}
    })
    
    # 用户配置
    user_config_file = DATA_DIR / "config.json"
    user_config = load_json(user_config_file, {})
    
    # 合并配置
    def deep_merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    return deep_merge(default_config, user_config)


def detect_project_info() -> dict:
    """检测当前项目信息"""
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
        try:
            pkg = json.loads((cwd / "package.json").read_text())
            deps = list(pkg.get("dependencies", {}).keys())
            dev_deps = list(pkg.get("devDependencies", {}).keys())
            all_deps = deps + dev_deps
            
            if "vue" in all_deps:
                project_info["tech_stack"].append("vue")
                project_info["type"] = "frontend"
            if "react" in all_deps:
                project_info["tech_stack"].append("react")
                project_info["type"] = "frontend"
            if "express" in all_deps or "fastify" in all_deps:
                project_info["tech_stack"].append("nodejs")
                project_info["type"] = "backend_api"
            if "typescript" in all_deps:
                project_info["tech_stack"].append("typescript")
        except:
            pass
    
    if (cwd / "requirements.txt").exists() or (cwd / "pyproject.toml").exists():
        project_info["tech_stack"].append("python")
        if project_info["type"] == "unknown":
            project_info["type"] = "backend_api"
    
    if (cwd / "go.mod").exists():
        project_info["tech_stack"].append("go")
        project_info["type"] = "backend_api"
    
    if (cwd / "Cargo.toml").exists():
        project_info["tech_stack"].append("rust")
    
    return project_info


def get_retention_days() -> int:
    """获取数据保留天数，-1 表示永久"""
    config = load_config()
    return config.get("recording", {}).get("retention_days", 90)


def should_retain(date_str: str) -> bool:
    """检查指定日期的数据是否应该保留"""
    retention_days = get_retention_days()
    
    # -1 表示永久保留
    if retention_days == -1:
        return True
    
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        days_old = (datetime.now() - date).days
        return days_old <= retention_days
    except:
        return True


# 工作流程阶段定义
WORKFLOW_STAGES = {
    "design": "设计、规划、讨论方案",
    "implement": "编写代码、创建文件",
    "test": "编写测试、运行测试",
    "debug": "调试、修复问题",
    "refactor": "重构、优化代码",
    "document": "编写文档",
    "deploy": "部署、发布",
    "review": "代码审查",
    "commit": "提交代码"
}


# ============================================================
# Pending Session 管理（用于自动 finalize 未完成的会话）
# ============================================================

PENDING_SESSION_FILE = "pending_session.json"


def get_pending_session_path() -> Path:
    """获取 pending session 文件路径"""
    return get_data_dir() / PENDING_SESSION_FILE


def save_pending_session(session_data: dict):
    """
    保存当前会话为 pending 状态
    
    在 --init 时调用，记录会话开始信息
    """
    pending_file = get_pending_session_path()
    pending_data = {
        "session_start": get_timestamp(),
        "project": detect_project_info(),
        "actions": [],
        "status": "pending"
    }
    pending_data.update(session_data)
    save_json(pending_file, pending_data)


def load_pending_session() -> Optional[dict]:
    """
    加载 pending session
    
    返回 None 如果没有 pending session
    """
    pending_file = get_pending_session_path()
    if not pending_file.exists():
        return None
    
    data = load_json(pending_file, None)
    if data and data.get("status") == "pending":
        return data
    return None


def add_action_to_pending_session(action: dict):
    """
    向 pending session 添加动作记录
    
    在 --record 时调用
    """
    pending_file = get_pending_session_path()
    pending_data = load_json(pending_file, {
        "session_start": get_timestamp(),
        "actions": [],
        "status": "pending"
    })
    
    if "actions" not in pending_data:
        pending_data["actions"] = []
    
    pending_data["actions"].append(action)
    pending_data["last_action_time"] = get_timestamp()
    save_json(pending_file, pending_data)


def clear_pending_session():
    """
    清除 pending session（会话正常结束后调用）
    """
    pending_file = get_pending_session_path()
    if pending_file.exists():
        pending_file.unlink()


def check_pending_session_timeout(timeout_hours: float = 2.0) -> bool:
    """
    检查 pending session 是否超时
    
    Args:
        timeout_hours: 超时时间（小时），默认 2 小时
    
    Returns:
        True 如果超时，False 如果未超时或没有 pending session
    """
    pending_data = load_pending_session()
    if not pending_data:
        return False
    
    # 获取最后活动时间
    last_time_str = pending_data.get("last_action_time") or pending_data.get("session_start")
    if not last_time_str:
        return False
    
    try:
        last_time = datetime.fromisoformat(last_time_str)
        elapsed_hours = (datetime.now() - last_time).total_seconds() / 3600
        return elapsed_hours >= timeout_hours
    except:
        return False


def build_session_data_from_pending(pending_data: dict) -> dict:
    """
    从 pending session 构建完整的 session data（用于自动 finalize）
    
    Args:
        pending_data: pending session 数据
    
    Returns:
        可用于 finalize 的 session data
    """
    actions = pending_data.get("actions", [])
    
    # 提取文件操作
    files_created = []
    files_modified = []
    files_deleted = []
    commands = []
    workflow_stages = set()
    technologies = set()
    
    for action in actions:
        action_type = action.get("type", "")
        details = action.get("details", {})
        context = action.get("context", {})
        
        # 文件操作
        file_path = details.get("file_path", "")
        if file_path:
            if action_type == "create_file":
                files_created.append(file_path)
            elif action_type in ["edit_file", "write_code", "write_test", "refactor", "fix_bug"]:
                files_modified.append(file_path)
            elif action_type == "delete_file":
                files_deleted.append(file_path)
            
            # 检测技术栈
            if file_path.endswith(".py"):
                technologies.add("python")
            elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
                technologies.add("javascript")
            elif file_path.endswith(".vue"):
                technologies.add("vue")
        
        # 命令
        command = details.get("command", "")
        if command:
            commands.append({
                "command": command,
                "exit_code": details.get("exit_code", 0)
            })
        
        # 工作流阶段
        stage = context.get("task_stage", "")
        if stage:
            workflow_stages.add(stage)
    
    # 构建 session data
    session_data = {
        "time": {
            "start": pending_data.get("session_start", get_timestamp()),
            "end": pending_data.get("last_action_time", get_timestamp())
        },
        "operations": {
            "files": {
                "created": files_created,
                "modified": list(set(files_modified)),
                "deleted": files_deleted
            },
            "commands": commands
        },
        "session_summary": {
            "topic": "自动保存的会话",
            "workflow_stages": list(workflow_stages) if workflow_stages else ["implement"],
            "technologies_used": list(technologies),
            "auto_finalized": True,
            "action_count": len(actions)
        },
        "conversation": {
            "message_count": 0,
            "user_messages": []
        }
    }
    
    return session_data


if __name__ == "__main__":
    print(f"Skill 目录: {SKILL_DIR}")
    print(f"数据目录: {DATA_DIR}")
    print(f"今天日期: {get_today()}")
    print(f"当前月份: {get_month()}")
    print(f"时间戳: {get_timestamp()}")
    
    ensure_data_dirs()
    print("数据目录已创建")
    
    config = load_config()
    print(f"配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
    
    project = detect_project_info()
    print(f"项目信息: {json.dumps(project, indent=2, ensure_ascii=False)}")
