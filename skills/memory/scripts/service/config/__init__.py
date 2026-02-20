"""配置服务：提供 Config 类、默认值、常量和配置访问函数。"""
import os
from .defaults import (
    _DEFAULTS, _get_dotpath,
    DAILY_DIR_NAME, MEMORY_MD, SESSIONS_FILE, INDEX_DB, FACTS_FILE,
    get_project_path,
)
from .manager import Config


def init_hook_context(event: dict) -> str:
    """Hook 统一初始化：提取项目路径、设置环境变量、重定向日志。

    合并 get_project_path + os.environ + redirect_to_project 三步操作，
    避免 Hook 脚本遗漏某一步导致日志写入错误目录。
    """
    from service.logger import redirect_to_project
    project_path = get_project_path(event)
    os.environ["MEMORY_PROJECT_PATH"] = project_path
    redirect_to_project(project_path)
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
