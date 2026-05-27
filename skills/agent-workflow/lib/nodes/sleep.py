"""sleep 原子节点：同步等待 N 秒（v1：CLI 内 time.sleep）。"""
from __future__ import annotations

import time
from typing import Any

from lib.errors import ErrorCode, WorkflowError
from lib.template import render

MAX_SECONDS = 300.0
MIN_SECONDS = 0.0


def resolve_seconds(node: dict[str, Any], vars_: dict[str, Any]) -> float:
    raw = node.get("seconds")
    if isinstance(raw, str):
        rendered = render(raw, vars_, strict_vars=True)
        try:
            value = float(rendered)
        except ValueError as exc:
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"sleep.seconds did not render to a number: {rendered!r}",
                location={"alias": node.get("alias")},
            ) from exc
    elif isinstance(raw, (int, float)):
        value = float(raw)
    else:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            "sleep.seconds is required (number or template)",
            location={"alias": node.get("alias")},
        )
    if value < MIN_SECONDS or value > MAX_SECONDS:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"sleep.seconds out of range [{MIN_SECONDS}, {MAX_SECONDS}]: {value}",
            location={"alias": node.get("alias")},
        )
    return value


def execute_sleep(node: dict[str, Any], state: dict[str, Any]) -> float:
    seconds = resolve_seconds(node, state.get("vars") or {})
    if seconds > 0:
        time.sleep(seconds)
    return seconds
