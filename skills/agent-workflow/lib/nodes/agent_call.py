"""agent_call 节点：渲染 prompt → 分派 executor → 返回 outcome。"""
from __future__ import annotations

from typing import Any

from lib.executors.base import ExecutionOutcome
from lib.executors.registry import get_executor
from lib.template import render


def execute_agent_call(
    node: dict[str, Any],
    state: dict[str, Any],
    run_context: dict[str, Any],
    *,
    workflow_executors: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> ExecutionOutcome:
    executor_name = node.get("executor") or "caller"
    executor = get_executor(
        executor_name,
        workflow_executors=workflow_executors,
        config=config,
    )
    prompt = render(node.get("prompt") or "", state.get("vars") or {}, strict_vars=True)
    return executor.execute(
        prompt=prompt,
        node=node,
        vars_=state.get("vars") or {},
        run_context=run_context,
    )
