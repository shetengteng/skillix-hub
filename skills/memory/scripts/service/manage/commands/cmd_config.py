"""config 子命令组"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import get_config
from service.config import _DEFAULTS, _get_dotpath

from ._helpers import _json_out, _parse_value, _all_dotpaths


def cmd_config_show(cfg, args):
    _json_out("ok", "config show", {"effective": cfg.get_all(), "sources": cfg.get_sources()})


def cmd_config_get(cfg, args):
    val = cfg.get(args.key)
    if val is None:
        dv = _get_dotpath(_DEFAULTS, args.key)
        if dv is None:
            _json_out("error", "config get", error={"code": "UNKNOWN_KEY", "message": f"未知: {args.key}", "available": _all_dotpaths(_DEFAULTS)})
            sys.exit(2)
        val = dv
    _json_out("ok", "config get", {"key": args.key, "value": val, "source": cfg.get_sources().get(args.key, "default")})


def cmd_config_set(cfg, args):
    dv = _get_dotpath(_DEFAULTS, args.key)
    if dv is None:
        _json_out("error", "config set", error={"code": "UNKNOWN_KEY", "message": f"未知: {args.key}"})
        sys.exit(2)
    value = _parse_value(args.value)
    scope = "global" if args.scope_global else "project"
    try:
        r = cfg.set_value(args.key, value, scope=scope)
    except ValueError as e:
        _json_out("error", "config set", error={"code": "SET_FAILED", "message": str(e)})
        sys.exit(4)
    data = {"field": args.key, "old_value": r["old_value"], "new_value": r["new_value"], "scope": scope, "file": r["file"], "needs_rebuild": r["needs_rebuild"]}
    if r["needs_rebuild"]:
        data["rebuild_reason"] = "需要 rebuild-index --full 重建索引"
        if args.key == "embedding.model":
            data["rebuild_reason"] = "嵌入模型已变更，所有现有向量与新模型不兼容，必须立即执行 rebuild-index --full 重建全部嵌入向量"
            data["warning"] = "模型切换后若不重建索引，向量搜索将返回错误结果或报错"
    _json_out("ok", "config set", data)


def cmd_config_reset(cfg, args):
    dv = _get_dotpath(_DEFAULTS, args.key)
    if dv is None and args.key != "--all":
        _json_out("error", "config reset", error={"code": "UNKNOWN_KEY", "message": f"未知: {args.key}"})
        sys.exit(2)
    scope = "global" if args.scope_global else "project"
    try:
        r = cfg.reset_value(args.key, scope=scope)
    except ValueError as e:
        _json_out("error", "config reset", error={"code": "RESET_FAILED", "message": str(e)})
        sys.exit(4)
    _json_out("ok", "config reset", {"field": args.key, "old_value": r["old_value"], "new_value": r["new_value"]})


def cmd_config_validate(cfg, args):
    issues = cfg.validate_report()
    _json_out("ok", "config validate", {"valid": len(issues) == 0, "issues": issues})
