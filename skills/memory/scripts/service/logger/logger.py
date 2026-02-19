"""
Memory Skill 统一日志模块

特点：
- 按天自动创建日志文件（memory-data/logs/YYYY-MM-DD.log）
- 同时输出到 stderr（不污染 stdout 的 JSON 输出）
- 自动清理超过保留天数的旧日志
- 通过环境变量 MEMORY_LOG_LEVEL 控制日志级别
"""
import os
import logging
import glob
from datetime import datetime, timezone, timedelta

from service.config.defaults import _DEFAULTS

_LOG_DIR = None
_initialized = False


def _get_log_dir():
    """日志目录：优先使用 MEMORY_LOG_DIR 环境变量，否则使用 memory-data/logs/"""
    global _LOG_DIR
    if _LOG_DIR:
        return _LOG_DIR
    env_dir = os.environ.get("MEMORY_LOG_DIR")
    if env_dir:
        _LOG_DIR = env_dir
    else:
        data_dir = _DEFAULTS["paths"]["data_dir"]
        _LOG_DIR = os.path.join(os.getcwd(), data_dir, "logs")
    os.makedirs(_LOG_DIR, exist_ok=True)
    return _LOG_DIR


def _cleanup_old_logs():
    """清理超过保留天数的旧日志文件"""
    log_dir = _get_log_dir()
    cutoff = datetime.now(timezone.utc) - timedelta(days=_DEFAULTS["log"]["retain_days"])
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    for f in glob.glob(os.path.join(log_dir, "*.log")):
        basename = os.path.splitext(os.path.basename(f))[0]
        if basename < cutoff_str:
            try:
                os.remove(f)
            except OSError:
                pass


def _ensure_init():
    """确保执行一次性初始化（进程生命周期内只执行一次）"""
    global _initialized
    if _initialized:
        return
    _initialized = True
    try:
        _cleanup_old_logs()
    except Exception:
        pass


class _DailyFileHandler(logging.FileHandler):
    """
    按天自动轮转的日志文件 Handler

    当日期变化时自动关闭旧文件并创建新文件，无需外部管理。
    """

    def __init__(self):
        self._current_date = None
        self._log_dir = _get_log_dir()
        filepath = self._today_path()
        super().__init__(filepath, mode="a", encoding="utf-8")

    def _today_path(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._current_date = today
        return os.path.join(self._log_dir, f"{today}.log")

    def emit(self, record):
        # 检测日期变化，自动切换文件
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            self.close()
            self.baseFilename = self._today_path()
            self.stream = self._open()
        super().emit(record)


_file_handler = None  # 全局共享的文件 Handler（避免每个 logger 创建独立文件句柄）


def get_logger(name: str) -> logging.Logger:
    """
    获取模块专属的日志器

    参数：
        name: 模块名，如 "embedding"、"search"、"sync"

    返回的 logger 名称格式为 "memory.{name}"，同时输出到 stderr 和日志文件。
    """
    global _file_handler
    _ensure_init()

    logger = logging.getLogger(f"memory.{name}")
    if logger.handlers:
        return logger

    level = getattr(logging, _DEFAULTS["log"]["level"].upper(), logging.INFO)
    logger.setLevel(level)
    logger.propagate = False  # 不向上传播，避免重复输出

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stderr Handler：日志输出到标准错误流（不影响 Hook 的 stdout JSON 输出）
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(fmt)
    logger.addHandler(stderr_handler)

    # 文件 Handler：全局共享，按天轮转
    if _file_handler is None:
        _file_handler = _DailyFileHandler()
        _file_handler.setLevel(level)
        _file_handler.setFormatter(fmt)

    logger.addHandler(_file_handler)
    return logger
