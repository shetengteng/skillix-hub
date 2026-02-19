"""
Config 类实现：分层配置加载器

从 config 模块导入默认值、校验规则和工具函数。
"""
import os
import copy
from .defaults import (
    _DEFAULTS,
    _SCHEMA,
    _ENV_MAP,
    REBUILD_FIELDS,
    _GLOBAL_CONFIG_PATH,
    _deep_merge,
    _get_dotpath,
    _set_dotpath,
    _load_json_file,
    _save_json_file,
)


class Config:
    """
    分层配置加载器。

    加载顺序（低 → 高优先级）：
      1. 代码默认值 (_DEFAULTS)
      2. 全局配置 (~/.memory-skill/config.json)
      3. 项目级配置 ({project}/.cursor/skills/memory-data/config.json)
      4. 环境变量 (MEMORY_*)
    """

    def __init__(self, project_path: str = None):
        self._project_path = project_path
        self._sources = {}
        self._config = copy.deepcopy(_DEFAULTS)

        global_cfg = _load_json_file(_GLOBAL_CONFIG_PATH)
        if global_cfg:
            global_cfg_clean = {k: v for k, v in global_cfg.items() if k != "version"}
            self._config = _deep_merge(self._config, global_cfg_clean)
            self._mark_sources(global_cfg_clean, "global")

        if project_path:
            proj_cfg_path = self._project_config_path(project_path)
            proj_cfg = _load_json_file(proj_cfg_path)
            if proj_cfg:
                proj_cfg_clean = {k: v for k, v in proj_cfg.items() if k != "version"}
                self._config = _deep_merge(self._config, proj_cfg_clean)
                self._mark_sources(proj_cfg_clean, "project")

        self._apply_env()
        self._validate()

    def _project_config_path(self, project_path: str) -> str:
        data_dir = _get_dotpath(self._config, "paths.data_dir",
                                _DEFAULTS["paths"]["data_dir"])
        return os.path.join(project_path, data_dir, "config.json")

    def _mark_sources(self, cfg: dict, source: str, prefix: str = ""):
        for k, v in cfg.items():
            path = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            if isinstance(v, dict):
                self._mark_sources(v, source, path)
            else:
                self._sources[path] = source

    def _apply_env(self):
        for env_var, (dotpath, cast) in _ENV_MAP.items():
            val = os.environ.get(env_var)
            if val is not None:
                try:
                    _set_dotpath(self._config, dotpath, cast(val))
                    self._sources[dotpath] = f"env:{env_var}"
                except (ValueError, TypeError):
                    pass

    def _validate(self):
        """校验配置值，非法值回退到默认值"""
        for dotpath, rule in _SCHEMA.items():
            val = self.get(dotpath)
            if val is None:
                continue
            valid = True
            if not isinstance(val, rule["type"]):
                try:
                    val = rule["type"](val)
                    _set_dotpath(self._config, dotpath, val)
                except (ValueError, TypeError):
                    valid = False
            if valid and "min" in rule and val < rule["min"]:
                valid = False
            if valid and "max" in rule and val > rule["max"]:
                valid = False
            if valid and "enum" in rule:
                check_val = val.upper() if isinstance(val, str) else val
                if check_val not in rule["enum"]:
                    valid = False
            if not valid:
                default_val = _get_dotpath(_DEFAULTS, dotpath)
                _set_dotpath(self._config, dotpath, default_val)
                self._sources.pop(dotpath, None)

        full = self.get("memory.load_days_full")
        partial = self.get("memory.load_days_partial")
        mx = self.get("memory.load_days_max")
        if full >= partial:
            _set_dotpath(self._config, "memory.load_days_partial", full + 3)
        if partial >= mx:
            _set_dotpath(self._config, "memory.load_days_max", partial + 2)
        if self.get("index.chunk_overlap") >= self.get("index.chunk_tokens"):
            _set_dotpath(self._config, "index.chunk_overlap",
                         self.get("index.chunk_tokens") // 5)

    def get(self, dotpath: str, default=None):
        """按点分路径取值"""
        return _get_dotpath(self._config, dotpath, default)

    def get_all(self) -> dict:
        """返回完整配置（深拷贝）"""
        return copy.deepcopy(self._config)

    def get_sources(self) -> dict:
        """返回非默认值来源映射"""
        return dict(self._sources)

    def set_value(self, dotpath: str, value, scope: str = "project") -> dict:
        """
        设置配置值并持久化。
        返回 {"old_value", "new_value", "needs_rebuild", "file"}
        """
        old_value = self.get(dotpath)

        if scope == "global":
            cfg_path = _GLOBAL_CONFIG_PATH
        elif self._project_path:
            cfg_path = self._project_config_path(self._project_path)
        else:
            raise ValueError("未指定 project_path，无法写入项目配置")

        file_data = _load_json_file(cfg_path)
        _set_dotpath(file_data, dotpath, value)
        file_data.setdefault("version", 1)
        _save_json_file(cfg_path, file_data)

        _set_dotpath(self._config, dotpath, value)
        self._sources[dotpath] = scope

        return {
            "old_value": old_value,
            "new_value": value,
            "needs_rebuild": dotpath in REBUILD_FIELDS,
            "file": cfg_path,
        }

    def reset_value(self, dotpath: str, scope: str = "project") -> dict:
        """重置指定字段到默认值，从配置文件中移除"""
        default_val = _get_dotpath(_DEFAULTS, dotpath)
        old_value = self.get(dotpath)

        if scope == "global":
            cfg_path = _GLOBAL_CONFIG_PATH
        elif self._project_path:
            cfg_path = self._project_config_path(self._project_path)
        else:
            raise ValueError("未指定 project_path")

        file_data = _load_json_file(cfg_path)
        keys = dotpath.split(".")
        cur = file_data
        for k in keys[:-1]:
            if k in cur and isinstance(cur[k], dict):
                cur = cur[k]
            else:
                break
        else:
            cur.pop(keys[-1], None)
            _save_json_file(cfg_path, file_data)

        _set_dotpath(self._config, dotpath, default_val)
        self._sources.pop(dotpath, None)

        return {"old_value": old_value, "new_value": default_val}

    def validate_report(self) -> list:
        """返回校验问题列表"""
        issues = []
        for dotpath, rule in _SCHEMA.items():
            val = self.get(dotpath)
            if val is None:
                continue
            if not isinstance(val, rule["type"]):
                issues.append(f"{dotpath}: 类型应为 {rule['type'].__name__}，实际为 {type(val).__name__}")
            elif "min" in rule and val < rule["min"]:
                issues.append(f"{dotpath}: 值 {val} 小于最小值 {rule['min']}")
            elif "max" in rule and val > rule["max"]:
                issues.append(f"{dotpath}: 值 {val} 大于最大值 {rule['max']}")
            elif "enum" in rule:
                check_val = val.upper() if isinstance(val, str) else val
                if check_val not in rule["enum"]:
                    issues.append(f"{dotpath}: 值 {val!r} 不在允许范围 {rule['enum']}")
        return issues
