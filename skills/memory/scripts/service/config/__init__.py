"""配置服务：提供 Config 类、默认值、常量和配置访问函数。"""
import os
from .defaults import (
    _DEFAULTS, _SCHEMA, _ENV_MAP, REBUILD_FIELDS, _GLOBAL_CONFIG_PATH,
    _deep_merge, _get_dotpath, _set_dotpath, _load_json_file, _save_json_file,
    DAILY_DIR_NAME, MEMORY_MD, SESSIONS_FILE, INDEX_DB, FACTS_FILE,
    get_project_path,
)
from .manager import Config


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
