"""配置服务：提供 Config 类、默认值、常量和配置访问函数。"""
import os
import sys
import json
import copy
import functools
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


def _extract_project_path_from_argv():
    """从 sys.argv 中提取 --project-path 参数值，默认返回 cwd。"""
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--project-path" and i + 1 < len(argv):
            return argv[i + 1]
    return os.getcwd()


def require_memory_enabled(main_fn):
    """装饰器：CLI 脚本的 main() 在执行前检查 .memory-disable。

    从 sys.argv 提取 --project-path（默认 cwd），
    disable 时输出 {"status": "skipped", "reason": "memory_disabled"} 并跳过执行。
    """
    @functools.wraps(main_fn)
    def wrapper(*args, **kwargs):
        project_path = _extract_project_path_from_argv()
        if not is_memory_enabled(project_path):
            print(json.dumps({"status": "skipped", "reason": "memory_disabled"}))
            return
        return main_fn(*args, **kwargs)
    return wrapper


def require_hook_memory(disabled_output=None):
    """装饰器：Hook 脚本的 main() 在 init_hook_context 之后检查 .memory-disable。

    disabled_output: disable 时输出的 JSON 对象，默认 {}。
    装饰器从 stdin 读取 event，调用 init_hook_context 初始化，
    disable 时直接输出 disabled_output 并跳过执行。
    enable 时将 (event, project_path) 作为参数传给被装饰函数。

    用法：
        @require_hook_memory()
        def main(event, project_path):
            ...

        @require_hook_memory(disabled_output={"additional_context": ""})
        def main(event, project_path):
            ...
    """
    if disabled_output is None:
        disabled_output = {}

    def decorator(main_fn):
        @functools.wraps(main_fn)
        def wrapper():
            event = {}
            try:
                raw = sys.stdin.read().strip()
                if raw:
                    event = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pass

            project_path = init_hook_context(event)

            if not is_memory_enabled(project_path):
                from service.logger import get_logger
                get_logger("hook").info("Memory 已禁用（.memory-disable），跳过")
                print(json.dumps(disabled_output))
                return

            return main_fn(event, project_path)
        return wrapper
    return decorator
