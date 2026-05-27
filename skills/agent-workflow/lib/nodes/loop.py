"""loop 节点：解析 max_iterations / 评估 condition。

控制流（cursor 推进）由 engine.py 负责，本模块只提供单次判断工具。
"""
from __future__ import annotations

from typing import Any

from lib.errors import ErrorCode, WorkflowError
from lib.template import evaluate_condition, render

MAX_ITERATIONS_CAP = 100


def resolve_max_iterations(node: dict[str, Any], vars_: dict[str, Any]) -> int:
    raw = node.get("max_iterations")
    if isinstance(raw, str):
        rendered = render(raw, vars_, strict_vars=True)
        try:
            value = int(float(rendered))
        except ValueError as exc:
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"loop.max_iterations did not render to integer: {rendered!r}",
                location={"alias": node.get("alias")},
            ) from exc
    elif isinstance(raw, (int, float)):
        value = int(raw)
    else:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            "loop.max_iterations is required (integer or template)",
            location={"alias": node.get("alias")},
        )
    if value < 1 or value > MAX_ITERATIONS_CAP:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"loop.max_iterations out of range [1, {MAX_ITERATIONS_CAP}]: {value}",
            location={"alias": node.get("alias")},
        )
    return value


def should_continue(
    node: dict[str, Any],
    vars_: dict[str, Any],
    *,
    current_iteration: int,
    max_iterations: int,
) -> bool:
    if current_iteration >= max_iterations:
        return False
    condition = node.get("condition")
    if not isinstance(condition, str) or not condition.strip():
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            "loop.condition is required",
            location={"alias": node.get("alias")},
        )
    return bool(evaluate_condition(condition, vars_))
