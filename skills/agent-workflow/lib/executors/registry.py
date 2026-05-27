"""Executor 注册表 + 解析 + list_executors action。

优先级：
    1. workflow.executors[name]   （per-workflow override）
    2. 用户全局配置 ~/.agent-workflow/config.yaml -> executors[name]
    3. 内置（caller / claude / codex / mock）

mock executor 仅在以下情况启用：
    - workflow.executors.mock 存在
    - 或环境变量 AGENT_WORKFLOW_ENABLE_MOCK=1
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import yaml

from lib.errors import ErrorCode, WorkflowError
from lib.executors.base import BaseExecutor, SpawnExecutor
from lib.executors.caller import CallerExecutor
from lib.executors.mock import MockExecutor

USER_CONFIG_PATH = Path.home() / ".agent-workflow" / "config.yaml"

BUILTIN_SPECS: dict[str, dict[str, Any]] = {
    "caller": {"builtin": True, "kind": "caller"},
    "claude": {
        "builtin": True,
        "kind": "spawn",
        "cmd": ["claude"],
        "input_mode": "stdin",
        "output_parser": "text",
    },
    "codex": {
        "builtin": True,
        "kind": "spawn",
        "cmd": ["codex", "exec"],
        "input_mode": "stdin",
        "output_parser": "text",
    },
    "mock": {"builtin": True, "kind": "mock"},
}


def _load_user_config() -> dict[str, Any]:
    if not USER_CONFIG_PATH.exists():
        return {}
    try:
        data = yaml.safe_load(USER_CONFIG_PATH.read_text("utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _mock_enabled(workflow_executors: dict[str, Any]) -> bool:
    if "mock" in workflow_executors:
        return True
    return os.environ.get("AGENT_WORKFLOW_ENABLE_MOCK") == "1"


def _normalise_spec(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    """把用户/工作流给的 spec 标准化为内置可读的形态。"""
    if not isinstance(spec, dict):
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"executor {name!r} spec must be an object",
        )
    spec = dict(spec)
    spec.setdefault("kind", "spawn")
    if spec["kind"] == "spawn":
        cmd = spec.get("cmd")
        args = spec.get("args") or []
        if isinstance(cmd, str):
            spec["cmd"] = [cmd, *args]
        elif isinstance(cmd, list):
            spec["cmd"] = [*cmd, *args]
        else:
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"executor {name!r} requires 'cmd' (string or list)",
            )
        spec.setdefault("input_mode", "stdin")
        spec.setdefault("output_parser", "text")
    return spec


def resolve_specs(workflow_executors: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """合并优先级：builtin → user-config → workflow-override，返回最终 spec map。"""
    out: dict[str, dict[str, Any]] = {n: dict(s) for n, s in BUILTIN_SPECS.items()}
    user = _load_user_config().get("executors") or {}
    for name, spec in user.items():
        try:
            merged = {**(out.get(name) or {}), **_normalise_spec(name, spec)}
            merged["builtin"] = False
            out[name] = merged
        except WorkflowError:
            continue
    for name, spec in (workflow_executors or {}).items():
        merged = {**(out.get(name) or {}), **_normalise_spec(name, spec)}
        merged["builtin"] = False
        out[name] = merged
    return out


def get_executor(
    name: str,
    *,
    workflow_executors: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> BaseExecutor:
    """名字 → 实例。允许 caller / mock / spawn 三种 kind。"""
    workflow_executors = workflow_executors or {}
    if name == "mock" and not _mock_enabled(workflow_executors):
        raise WorkflowError(
            ErrorCode.EXECUTOR_NOT_FOUND,
            "mock executor is disabled; set AGENT_WORKFLOW_ENABLE_MOCK=1 or declare it under workflow.executors",
        )

    specs = resolve_specs(workflow_executors)
    spec = specs.get(name)
    if spec is None:
        raise WorkflowError(
            ErrorCode.EXECUTOR_NOT_FOUND,
            f"executor {name!r} is not registered",
            location={"executor": name},
        )

    kind = spec.get("kind")
    if kind == "caller":
        return CallerExecutor()
    if kind == "mock":
        return MockExecutor()
    if kind == "spawn":
        cfg = config or {}
        return SpawnExecutor(
            name=name,
            cmd=spec["cmd"],
            input_mode=spec.get("input_mode", "stdin"),
            output_parser=spec.get("output_parser", "text"),
            stall_timeout_ms=int(spec.get("stall_timeout_ms") or cfg.get("stall_timeout_ms") or 300_000),
            total_timeout_ms=int(spec.get("timeout_ms") or cfg.get("total_timeout_ms") or 600_000),
            env=spec.get("env") or None,
        )
    raise WorkflowError(
        ErrorCode.PARAMS_INVALID,
        f"executor {name!r} has unknown kind={kind!r}",
    )


def list_executors(params: dict[str, Any]) -> dict[str, Any]:
    """executors action 入口：列出可见 executor + 是否在 PATH。"""
    workflow_executors = params.get("workflow_executors") or {}
    specs = resolve_specs(workflow_executors)
    items: list[dict[str, Any]] = []
    for name in sorted(specs.keys()):
        spec = specs[name]
        kind = spec.get("kind", "spawn")
        entry: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "builtin": bool(spec.get("builtin")),
        }
        if kind == "spawn":
            cmd = spec.get("cmd") or []
            entry["cmd"] = cmd
            entry["input_mode"] = spec.get("input_mode", "stdin")
            entry["output_parser"] = spec.get("output_parser", "text")
            entry["available_in_path"] = bool(cmd and shutil.which(cmd[0]))
        elif kind == "mock":
            entry["enabled"] = _mock_enabled(workflow_executors)
        items.append(entry)
    return {"executors": items, "user_config_path": str(USER_CONFIG_PATH)}
