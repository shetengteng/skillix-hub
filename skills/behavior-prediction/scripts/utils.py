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
