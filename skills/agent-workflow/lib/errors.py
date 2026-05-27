"""统一错误码 + 错误对象工厂。

对齐 SKILL.md《错误码表》与设计文档 §4.10。
每个错误码默认带：retryable + suggestion，调用方可在 make_error 时覆盖。
"""
from __future__ import annotations

from typing import Any, Final


class ErrorCode:
    """错误码常量（字符串）。新增时同步 SKILL.md 与设计文档。"""

    YAML_PARSE_ERROR: Final[str] = "YAML_PARSE_ERROR"
    WORKFLOW_INVALID: Final[str] = "WORKFLOW_INVALID"
    WORKFLOW_SNAPSHOT_CORRUPTED: Final[str] = "WORKFLOW_SNAPSHOT_CORRUPTED"
    NODE_OUTPUT_REQUIRED: Final[str] = "NODE_OUTPUT_REQUIRED"
    NODE_TIMEOUT: Final[str] = "NODE_TIMEOUT"
    NODE_EMPTY_OUTPUT: Final[str] = "NODE_EMPTY_OUTPUT"

    RUN_NOT_FOUND: Final[str] = "RUN_NOT_FOUND"
    RUN_ALREADY_TERMINAL: Final[str] = "RUN_ALREADY_TERMINAL"
    RUN_BUSY: Final[str] = "RUN_BUSY"

    EXECUTOR_NOT_FOUND: Final[str] = "EXECUTOR_NOT_FOUND"
    EXECUTOR_NONZERO_EXIT: Final[str] = "EXECUTOR_NONZERO_EXIT"
    EXECUTOR_STALLED: Final[str] = "EXECUTOR_STALLED"

    LOOP_EXCEEDED: Final[str] = "LOOP_EXCEEDED"
    SCHEMA_VIOLATION: Final[str] = "SCHEMA_VIOLATION"
    VAR_NOT_IN_SCOPE: Final[str] = "VAR_NOT_IN_SCOPE"
    CALLER_ERROR: Final[str] = "CALLER_ERROR"

    UNKNOWN_ACTION: Final[str] = "UNKNOWN_ACTION"
    PARAMS_INVALID: Final[str] = "PARAMS_INVALID"
    NOT_IMPLEMENTED: Final[str] = "NOT_IMPLEMENTED"
    INTERNAL: Final[str] = "INTERNAL"


_DEFAULTS: dict[str, dict[str, Any]] = {
    ErrorCode.YAML_PARSE_ERROR: {
        "retryable": False,
        "suggestion": "fix YAML syntax at reported line/col then re-run validate",
    },
    ErrorCode.WORKFLOW_INVALID: {
        "retryable": False,
        "suggestion": "review violations[] and fix the workflow YAML; then re-run validate",
    },
    ErrorCode.WORKFLOW_SNAPSHOT_CORRUPTED: {
        "retryable": False,
        "suggestion": "snapshot file is corrupted; restart the workflow from source YAML",
    },
    ErrorCode.NODE_OUTPUT_REQUIRED: {
        "retryable": False,
        "suggestion": "add an `output` field on the producer node",
    },
    ErrorCode.NODE_TIMEOUT: {
        "retryable": False,
        "suggestion": "increase node-level timeout_ms or split the work into smaller steps",
    },
    ErrorCode.NODE_EMPTY_OUTPUT: {
        "retryable": False,
        "suggestion": "executor stdout was empty; check the prompt or executor configuration",
    },
    ErrorCode.RUN_NOT_FOUND: {
        "retryable": False,
        "suggestion": "verify the run_id; use `list` to enumerate known runs",
    },
    ErrorCode.RUN_ALREADY_TERMINAL: {
        "retryable": False,
        "suggestion": "the run already finished; start a new run instead of advancing this one",
    },
    ErrorCode.RUN_BUSY: {
        "retryable": True,
        "suggestion": "another process holds the state lock; wait 1s then retry",
    },
    ErrorCode.EXECUTOR_NOT_FOUND: {
        "retryable": False,
        "suggestion": "install the missing CLI or set allow_missing_executors=true to defer the check",
    },
    ErrorCode.EXECUTOR_NONZERO_EXIT: {
        "retryable": False,
        "suggestion": "inspect stderr_tail; rerun the workflow after fixing the prompt or CLI",
    },
    ErrorCode.EXECUTOR_STALLED: {
        "retryable": False,
        "suggestion": "executor produced no stdout for stall_timeout_ms; increase the timeout or switch executor",
    },
    ErrorCode.LOOP_EXCEEDED: {
        "retryable": False,
        "suggestion": "loop reached max_iterations; raise the cap or refine the condition",
    },
    ErrorCode.SCHEMA_VIOLATION: {
        "retryable": True,
        "suggestion": "input does not match wait_user.input_schema; collect user input again",
    },
    ErrorCode.VAR_NOT_IN_SCOPE: {
        "retryable": False,
        "suggestion": "variable referenced before it was produced; reorder nodes or check the alias",
    },
    ErrorCode.CALLER_ERROR: {
        "retryable": False,
        "suggestion": "caller reported an error; do not advance further",
    },
    ErrorCode.UNKNOWN_ACTION: {
        "retryable": False,
        "suggestion": "use one of: create, validate, start, advance, resume, status, list, abort, executors",
    },
    ErrorCode.PARAMS_INVALID: {
        "retryable": False,
        "suggestion": "params must be a valid JSON object; check the action contract in SKILL.md",
    },
    ErrorCode.NOT_IMPLEMENTED: {
        "retryable": False,
        "suggestion": "feature not yet implemented in this milestone",
    },
    ErrorCode.INTERNAL: {
        "retryable": True,
        "suggestion": "internal error; report with debug_trace if persists",
    },
}


class WorkflowError(Exception):
    """携带错误码的异常，可被 dispatch 层直接转成统一错误对象。"""

    def __init__(self, code: str, message: str, **extras: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.extras = extras

    def to_dict(self) -> dict[str, Any]:
        return make_error(self.code, message=self.message, **self.extras)


def make_error(
    code: str,
    *,
    message: str | None = None,
    retryable: bool | None = None,
    suggestion: str | None = None,
    **extras: Any,
) -> dict[str, Any]:
    """构造统一错误对象。

    返回结构：
        {
            "code": "...",
            "message": "...",
            "retryable": bool,
            "suggestion": "...",
            ... (extras: location / context / stderr_tail / violations / debug_trace ...)
        }
    """
    defaults = _DEFAULTS.get(code, {})
    err: dict[str, Any] = {
        "code": code,
        "message": message or code.replace("_", " ").lower(),
        "retryable": defaults.get("retryable", False) if retryable is None else bool(retryable),
        "suggestion": suggestion or defaults.get("suggestion", ""),
    }
    for key, value in extras.items():
        if value is None:
            continue
        err[key] = value
    return err
