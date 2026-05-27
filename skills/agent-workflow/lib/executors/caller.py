"""caller executor — 不 spawn 子进程，把 prompt 抛回给 IDE agent。

engine 收到 kind="needs_caller" 会把 status 改为 awaiting_agent，
并把 payload 作为 CLI 顶层 result 返回，IDE agent 拿到 prompt 自己推理，
然后调 advance 把结果送回。
"""
from __future__ import annotations

from typing import Any

from lib.executors.base import BaseExecutor, ExecutionOutcome


class CallerExecutor(BaseExecutor):
    name = "caller"

    def __init__(self) -> None:
        super().__init__(name="caller")

    def execute(
        self,
        *,
        prompt: str,
        node: dict[str, Any],
        vars_: dict[str, Any],
        run_context: dict[str, Any],
    ) -> ExecutionOutcome:
        payload = {
            "prompt": prompt,
            "node_description": node.get("description") or "",
            "alias": node.get("alias"),
            "internal_id": node.get("_internal_id"),
            "expected_output": node.get("output"),
            "context_files": node.get("context_files") or [],
        }
        return ExecutionOutcome(
            kind="needs_caller",
            payload=payload,
            duration_ms=0,
            extra={"executor": "caller", "alias": node.get("alias")},
        )
