#!/usr/bin/env python3
"""agent-workflow CLI entry.

调用约定（与 SKILL.md 严格对齐）：
    python3 skills/agent-workflow/tool.py <action> '<JSON params>'

action 列表：
    flows      列出全局可用的 workflow 定义（渐进式披露入口）
    create     创建 workflow（list_templates / from_template / scaffold）
    validate   4 级校验 workflow
    start      启动新 run（支持路径或 workflow name）
    advance    推进 run（caller 返回 agent 输出后调用）
    resume     恢复 wait_user 节点
    status     查询 run 状态
    list       列出 runs（支持 format=table）
    abort      中止 run
    executors  列出可用 executor
    view       生成可视化 HTML（总览 / 单 run），自动打开浏览器

统一输出：{"result": {...}} 或 {"error": {...}}
退出码：0 = result，1 = error
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.errors import ErrorCode, WorkflowError, make_error  # noqa: E402


VALID_ACTIONS = {
    "create",
    "validate",
    "start",
    "advance",
    "resume",
    "status",
    "list",
    "abort",
    "executors",
    "view",
    "flows",
}


def _emit_result(payload: dict) -> int:
    print(json.dumps({"result": payload}, ensure_ascii=False, indent=2))
    return 0


def _emit_error(err: dict) -> int:
    print(json.dumps({"error": err}, ensure_ascii=False, indent=2))
    return 1


def _parse_params(raw: str) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"params is not valid JSON: {exc.msg} (line {exc.lineno} col {exc.colno})") from exc
    if not isinstance(data, dict):
        raise ValueError("params must be a JSON object")
    return data


def dispatch(action: str, params: dict) -> dict:
    """根据 action 路由到具体实现（T02-T10 逐步填充）。"""
    if action == "executors":
        from lib.executors.registry import list_executors

        return list_executors(params)
    if action == "validate":
        from lib.parser import validate_action

        return validate_action(params)
    if action == "create":
        from lib.builder.scaffold import create_action

        return create_action(params)
    if action == "start":
        from lib.engine import start_action

        return start_action(params)
    if action == "advance":
        from lib.engine import advance_action

        return advance_action(params)
    if action == "resume":
        from lib.engine import resume_action

        return resume_action(params)
    if action == "status":
        from lib.engine import status_action

        return status_action(params)
    if action == "list":
        from lib.engine import list_action

        return list_action(params)
    if action == "abort":
        from lib.engine import abort_action

        return abort_action(params)
    if action == "view":
        from lib.view.render import view_action

        return view_action(params)
    if action == "flows":
        from lib.engine import flows_action

        return flows_action(params)
    raise RuntimeError(f"unhandled action: {action}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        return _emit_error(
            make_error(
                ErrorCode.UNKNOWN_ACTION,
                message="missing action; expected one of: " + ", ".join(sorted(VALID_ACTIONS)),
            )
        )
    action = argv[0]
    if action in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if action not in VALID_ACTIONS:
        return _emit_error(
            make_error(
                ErrorCode.UNKNOWN_ACTION,
                message=f"unknown action: {action!r}",
                suggestion=f"valid actions: {sorted(VALID_ACTIONS)}",
            )
        )
    raw_params = argv[1] if len(argv) >= 2 else ""
    try:
        params = _parse_params(raw_params)
    except ValueError as exc:
        return _emit_error(
            make_error(ErrorCode.PARAMS_INVALID, message=str(exc))
        )
    try:
        result = dispatch(action, params)
    except WorkflowError as exc:
        return _emit_error(exc.to_dict())
    except NotImplementedError as exc:
        return _emit_error(
            make_error(
                ErrorCode.NOT_IMPLEMENTED,
                message=str(exc) or f"action {action!r} not implemented yet",
            )
        )
    except KeyError as exc:
        return _emit_error(
            make_error(
                ErrorCode.PARAMS_INVALID,
                message=f"missing required field: {exc.args[0]}" if exc.args else "missing required field",
            )
        )
    except Exception as exc:  # noqa: BLE001
        return _emit_error(
            make_error(
                ErrorCode.INTERNAL,
                message=f"{type(exc).__name__}: {exc}",
                debug_trace=traceback.format_exc().splitlines()[-8:],
            )
        )
    return _emit_result(result)


if __name__ == "__main__":
    sys.exit(main())
