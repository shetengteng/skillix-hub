"""mock executor — 单元/集成测试用，通过环境变量注入 stdout / 错误。

环境变量协议：
    AGENT_WORKFLOW_MOCK_<ALIAS>            -> stdout 文本（直接作为 output 返回）
    AGENT_WORKFLOW_MOCK_<ALIAS>_EXIT       -> 退出码，非 0 抛 EXECUTOR_NONZERO_EXIT
    AGENT_WORKFLOW_MOCK_<ALIAS>_STALL      -> "1" 表示模拟 stall

ALIAS 大小写不敏感：mock 会同时匹配 upper / lower 形式。
若未配置任何匹配变量，则默认返回 "mock-<alias>"。
"""
from __future__ import annotations

import os
from typing import Any

from lib.errors import ErrorCode, WorkflowError
from lib.executors.base import BaseExecutor, ExecutionOutcome


def _read_env(alias: str, suffix: str = "") -> str | None:
    key_upper = f"AGENT_WORKFLOW_MOCK_{alias.upper()}{suffix}"
    if key_upper in os.environ:
        return os.environ[key_upper]
    return None


class MockExecutor(BaseExecutor):
    name = "mock"

    def __init__(self) -> None:
        super().__init__(name="mock")

    def execute(
        self,
        *,
        prompt: str,
        node: dict[str, Any],
        vars_: dict[str, Any],
        run_context: dict[str, Any],
    ) -> ExecutionOutcome:
        alias = node.get("alias") or node.get("_internal_id") or "anon"
        if _read_env(alias, "_STALL") == "1":
            raise WorkflowError(
                ErrorCode.EXECUTOR_STALLED,
                f"mock stall triggered for alias={alias!r}",
                location={"alias": alias},
            )
        exit_str = _read_env(alias, "_EXIT")
        if exit_str and exit_str != "0":
            raise WorkflowError(
                ErrorCode.EXECUTOR_NONZERO_EXIT,
                f"mock exit_code={exit_str} for alias={alias!r}",
                location={"alias": alias, "exit_code": exit_str},
                stderr_tail=_read_env(alias, "_STDERR") or "",
            )
        stdout = _read_env(alias) or f"mock-{alias}"
        return ExecutionOutcome(
            kind="completed",
            output=stdout,
            duration_ms=0,
            stdout_size=len(stdout.encode("utf-8")),
            exit_code=0,
            extra={"executor": "mock", "alias": alias, "prompt_len": len(prompt)},
        )
