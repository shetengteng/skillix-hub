"""配置服务：提供 Config 类、默认值、常量和配置访问函数。"""
import os
import json
import copy
from .defaults import (
    _DEFAULTS, _get_dotpath,
    DAILY_DIR_NAME, MEMORY_MD, SESSIONS_FILE, INDEX_DB, FACTS_FILE,
    get_project_path,
)
from .manager import Config

_DIR_ENSURED = set()


def ensure_memory_dir(memory_dir):
    """确保 memory-data 目录结构完整（MEMORY.md、config.json、daily/）。

    全局安装后在新项目中首次使用时，init/index.py 不会执行，
    需要在运行时补全目录结构。使用 _DIR_ENSURED 缓存避免重复检查。
    """
    if memory_dir in _DIR_ENSURED:
        return
    _DIR_ENSURED.add(memory_dir)

    os.makedirs(os.path.join(memory_dir, DAILY_DIR_NAME), exist_ok=True)

    memory_md_path = os.path.join(memory_dir, MEMORY_MD)
    if not os.path.exists(memory_md_path):
        with open(memory_md_path, "w", encoding="utf-8") as f:
            f.write("# 核心记忆\n\n## 用户偏好\n\n## 项目背景\n\n## 重要决策\n")

    config_json = os.path.join(memory_dir, "config.json")
    if not os.path.exists(config_json):
        default_config = copy.deepcopy(_DEFAULTS)
        default_config["version"] = 1
        with open(config_json, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
            f.write("\n")


def init_hook_context(event: dict) -> str:
    """Hook 统一初始化：提取项目路径、设置环境变量、重定向日志、确保目录结构。

    合并 get_project_path + os.environ + redirect_to_project + ensure_memory_dir，
    避免 Hook 脚本遗漏某一步导致日志写入错误目录或目录结构不完整。
    """
    from service.logger import redirect_to_project
    project_path = get_project_path(event)
    os.environ["MEMORY_PROJECT_PATH"] = project_path
    redirect_to_project(project_path)
    if is_memory_enabled(project_path):
        memory_dir = os.path.join(
            project_path,
            _get_dotpath(_DEFAULTS, "paths.data_dir", ".cursor/skills/memory-data"),
        )
        ensure_memory_dir(memory_dir)
    return project_path


def get_config(project_path=None):
    """获取配置实例。传入 project_path 会合并项目级配置。"""
    return Config(project_path) if project_path else Config()


def get_memory_dir(project_path):
    """项目的记忆数据目录绝对路径。"""
    cfg = get_config(project_path)
    return os.path.join(project_path, cfg.get("paths.data_dir"))


def get_daily_dir(project_path):
    """每日事实日志目录绝对路径。"""
    return os.path.join(get_memory_dir(project_path), DAILY_DIR_NAME)


DISABLE_FILE = ".memory-disable"


def is_memory_enabled(project_path):
    """检查项目是否启用 Memory 功能（.cursor/skills/.memory-disable 不存在即启用）。"""
    disable_file = os.path.join(project_path, ".cursor", "skills", DISABLE_FILE)
    return not os.path.exists(disable_file)
