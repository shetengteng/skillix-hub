"""
Memory Skill 配置定义模块

提供：_DEFAULTS（全部默认值）、_SCHEMA（校验规则）、文件名常量、工具函数。
Config 类和 get_config() 在 service.config 中。
"""
import os
import json
import copy

# ========== 默认值定义 ==========

_DEFAULTS = {
    "memory": {
        "load_days_full": 2,
        "load_days_partial": 5,
        "load_days_max": 7,
        "partial_per_day": 3,
        "important_confidence": 0.9,
        "facts_limit": 15,
    },
    "embedding": {
        "model": "Qwen/Qwen3-Embedding-0.6B",
        "cache_dir": os.path.join("~", ".memory", "models"),
    },
    "index": {
        "chunk_tokens": 400,
        "chunk_overlap": 80,
    },
    "log": {
        "level": "INFO",
        "retain_days": 7,
    },
    "paths": {
        "data_dir": os.path.join(".cursor", "skills", "memory-data"),
    },
    "cleanup": {
        "auto_cleanup_days": 90,
        "backup_retain_days": 30,
    },
}

# 字段校验规则
_SCHEMA = {
    "memory.load_days_full":        {"type": int,   "min": 1,   "max": 365},
    "memory.load_days_partial":     {"type": int,   "min": 1,   "max": 365},
    "memory.load_days_max":         {"type": int,   "min": 1,   "max": 365},
    "memory.partial_per_day":       {"type": int,   "min": 1,   "max": 100},
    "memory.important_confidence":  {"type": float, "min": 0.0, "max": 1.0},
    "memory.facts_limit":           {"type": int,   "min": 1,   "max": 500},
    "index.chunk_tokens":           {"type": int,   "min": 50,  "max": 2000},
    "index.chunk_overlap":          {"type": int,   "min": 0,   "max": 500},
    "log.level":                    {"type": str,   "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
    "log.retain_days":              {"type": int,   "min": 1,   "max": 365},
    "cleanup.auto_cleanup_days":    {"type": int,   "min": 0,   "max": 3650},
    "cleanup.backup_retain_days":   {"type": int,   "min": 1,   "max": 365},
}

# 环境变量 → 配置路径映射
_ENV_MAP = {
    "MEMORY_LOG_LEVEL":         ("log.level",               str),
    "MEMORY_LOAD_DAYS_FULL":    ("memory.load_days_full",   int),
    "MEMORY_LOAD_DAYS_MAX":     ("memory.load_days_max",    int),
    "MEMORY_FACTS_LIMIT":       ("memory.facts_limit",      int),
    "MEMORY_EMBEDDING_MODEL":   ("embedding.model",         str),
    "MEMORY_DATA_DIR":          ("paths.data_dir",          str),
}

# 变更后需要重建索引的字段
REBUILD_FIELDS = {"embedding.model", "index.chunk_tokens", "index.chunk_overlap"}

# 全局配置文件路径
_GLOBAL_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".memory", "config.json")


# ========== 工具函数 ==========

def _deep_merge(base: dict, overlay: dict) -> dict:
    """深度合并，overlay 覆盖 base 中的同名键"""
    result = copy.deepcopy(base)
    for k, v in overlay.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def _get_dotpath(d: dict, path: str, default=None):
    """按点分路径取值，如 get_dotpath(d, 'memory.facts_limit')"""
    keys = path.split(".")
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def _set_dotpath(d: dict, path: str, value):
    """按点分路径设值"""
    keys = path.split(".")
    cur = d
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def _load_json_file(path: str) -> dict:
    """安全加载 JSON 文件，失败返回空字典"""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {}
    try:
        with open(expanded, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json_file(path: str, data: dict):
    """原子写入 JSON 文件"""
    expanded = os.path.expanduser(path)
    os.makedirs(os.path.dirname(expanded), exist_ok=True)
    tmp = expanded + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, expanded)


# ========== 文件/目录名常量（固定值，不可配置） ==========

DAILY_DIR_NAME = "daily"
MEMORY_MD = "MEMORY.md"
FACTS_FILE = "facts.jsonl"
SESSIONS_FILE = "sessions.jsonl"
INDEX_DB = "index.sqlite"


def get_project_path(event: dict) -> str:
    """从 Cursor Hook 事件中提取项目根路径"""
    roots = event.get("workspace_roots", [])
    return roots[0] if roots else os.getcwd()
