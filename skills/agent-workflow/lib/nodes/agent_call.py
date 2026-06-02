"""agent_call 节点：渲染 prompt + agent.role → 分派 executor → 返回 outcome。"""
from __future__ import annotations

from typing import Any

from lib.executors.base import ExecutionOutcome
from lib.executors.registry import get_executor
from lib.template import render


def _prepare_agent(
    node: dict[str, Any],
    vars_map: dict[str, Any],
) -> dict[str, Any] | None:
    """从 node 提取 agent 上下文，渲染 role 中的 {{var}}，归一化 skills 列表。

    返回 None 表示未配置或为空（caller payload 不带 agent 字段，spawn 不拼前缀）。
    """
    raw = node.get("agent")
    if not isinstance(raw, dict):
        return None
    result: dict[str, Any] = {}
    role = raw.get("role")
    if isinstance(role, str) and role.strip():
        result["role"] = render(role, vars_map, strict_vars=True)
    skills = raw.get("skills")
    if isinstance(skills, list):
        cleaned = [s for s in skills if isinstance(s, str) and s.strip()]
        if cleaned:
            result["skills"] = cleaned
    return result or None


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
        run_context=run_context,
    )
    vars_map = state.get("vars") or {}
    prompt = render(node.get("prompt") or "", vars_map, strict_vars=True)
    agent_ctx = _prepare_agent(node, vars_map)
    return executor.execute(
        prompt=prompt,
        node=node,
        vars_=vars_map,
        run_context=run_context,
        agent=agent_ctx,
    )
