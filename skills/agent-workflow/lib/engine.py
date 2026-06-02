"""状态机 + 8 个 action 入口（start / advance / resume / status / list / abort / executors / validate）。

控制流：
    - cursor.path = [idx1, idx2, ...]  指向当前待执行节点；loop 内 path 会再加一层
    - cursor.iteration_counts[<loop_id>] = N
    - 节点执行后调 _advance_cursor：同层 +1，越界则弹出上层；上层是 loop 时决定 continue/exit
    - chain_timeout（默认 25s）保护：内部链式执行超时 → 返回 action="continue"，
      caller 重新调 advance 让 CLI 接着推进，避免 IDE shell 超时

action 返回结构（统一）：
    execute_agent  : 把 prompt 抛给 caller agent，下次调 advance 带 result
    wait_user      : 抛 schema 给 caller，下次调 resume 带 input
    completed      : workflow 全部完成
    failed         : workflow 失败（错误对象返回顶层 error）
    aborted        : workflow 被用户 abort
    continue       : chain_timeout 触发，请 caller 立即再调 advance
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from lib.errors import ErrorCode, WorkflowError
from lib.logger import read_events, write_audit, write_event
from lib.nodes import loop as loop_node
from lib.nodes import sleep as sleep_node
from lib.nodes import wait_user as wait_user_node
from lib.nodes.agent_call import execute_agent_call
from lib.parser import assign_internal_ids, load_workflow, validate_action as _validate_action
from lib.store import (
    StateTransaction,
    append_history,
    create_run,
    get_run_dir,
    list_runs,
    list_workflows,
    load_workflow_snapshot,
    read_state,
    render_runs_table,
    write_state,
)

DEFAULT_CHAIN_TIMEOUT_MS = 25_000
TERMINAL_STATUSES = {"completed", "failed", "aborted"}


# ---------------------------------------------------------------------------
# cursor helpers
# ---------------------------------------------------------------------------


def _find_node_at(workflow: dict[str, Any], path: list[int]) -> dict[str, Any]:
    nodes = workflow.get("nodes") or []
    if not path:
        raise WorkflowError(ErrorCode.WORKFLOW_INVALID, "cursor.path is empty")
    node = nodes[path[0]]
    for depth, idx in enumerate(path[1:], start=1):
        if node.get("type") != "loop":
            raise WorkflowError(
                ErrorCode.WORKFLOW_INVALID,
                f"cursor path expects loop at depth {depth}, got {node.get('type')!r}",
            )
        node = (node.get("body") or [])[idx]
    return node


def _parent_nodes_for(workflow: dict[str, Any], path: list[int]) -> list[dict[str, Any]]:
    if len(path) == 1:
        return workflow.get("nodes") or []
    parent = _find_node_at(workflow, path[:-1])
    return parent.get("body") or []


def _advance_cursor(
    workflow: dict[str, Any],
    cursor: dict[str, Any],
    vars_: dict[str, Any],
) -> bool:
    """前进 cursor，返回 True 表示仍有节点待执行，False 表示 workflow 完成。

    可能修改：cursor.path / cursor.iteration_counts。
    """
    path: list[int] = cursor["path"]
    iters: dict[str, int] = cursor.setdefault("iteration_counts", {})
    while path:
        siblings = _parent_nodes_for(workflow, path)
        next_idx = path[-1] + 1
        if next_idx < len(siblings):
            path[-1] = next_idx
            return True

        # 同层结束。如果当前 frame 在 loop body 内，看 loop 是否继续。
        if len(path) >= 2:
            loop_path = path[:-1]
            loop = _find_node_at(workflow, loop_path)
            if loop.get("type") == "loop":
                loop_id = loop.get("_internal_id") or ".".join(map(str, loop_path))
                iters[loop_id] = iters.get(loop_id, 0) + 1
                max_iter = loop_node.resolve_max_iterations(loop, vars_)
                if loop_node.should_continue(
                    loop, vars_, current_iteration=iters[loop_id], max_iterations=max_iter
                ):
                    path[-1] = 0
                    return True
                # exit loop：检查 LOOP_EXCEEDED
                if iters[loop_id] >= max_iter:
                    try:
                        condition_still_true = _loop_condition_safe(loop, vars_)
                    except Exception:  # noqa: BLE001
                        condition_still_true = False
                    if condition_still_true:
                        raise WorkflowError(
                            ErrorCode.LOOP_EXCEEDED,
                            f"loop {loop.get('alias') or loop_id!r} hit max_iterations={max_iter}",
                            location={
                                "alias": loop.get("alias"),
                                "internal_id": loop.get("_internal_id"),
                                "iterations": iters[loop_id],
                            },
                        )
                # 清理 loop 状态，回到上层并继续推进
                iters.pop(loop_id, None)
        path.pop()
    return False


# 给 loop helper 暴露一个安全的 condition 评估（吞 VAR_NOT_IN_SCOPE 当作 false）
def _loop_condition_safe(loop: dict[str, Any], vars_: dict[str, Any]) -> bool:
    try:
        return loop_node.should_continue(loop, vars_, current_iteration=0, max_iterations=10**9)
    except WorkflowError:
        return False


def _loop_should_continue(
    node: dict[str, Any], vars_: dict[str, Any], *, current_iteration: int, max_iterations: int
) -> bool:
    """do-while 友好：iter_count == 0 时如果 condition 引用了尚未产生的变量，默认进入。"""
    try:
        return loop_node.should_continue(
            node, vars_, current_iteration=current_iteration, max_iterations=max_iterations
        )
    except WorkflowError as exc:
        if exc.code == ErrorCode.VAR_NOT_IN_SCOPE and current_iteration == 0:
            return True
        raise


def _normalise_loop_entry(
    workflow: dict[str, Any],
    cursor: dict[str, Any],
    vars_: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    """如果 cursor 当前指向 loop 节点，尝试 dive in / skip。

    返回 (待执行节点 | None, advanced)
        advanced=True 时说明本次发生了 cursor 变更（dive in 或 skip）。
        节点为 None 表示整个 workflow 完成。
    """
    advanced = False
    path = cursor["path"]
    while True:
        if not path:
            return None, advanced
        node = _find_node_at(workflow, path)
        if node.get("type") != "loop":
            return node, advanced
        loop_id = node.get("_internal_id") or ".".join(map(str, path))
        iters = cursor.setdefault("iteration_counts", {})
        if loop_id not in iters:
            iters[loop_id] = 0
        max_iter = loop_node.resolve_max_iterations(node, vars_)
        if _loop_should_continue(
            node, vars_, current_iteration=iters[loop_id], max_iterations=max_iter
        ):
            path.append(0)
            advanced = True
            continue
        if iters[loop_id] >= max_iter:
            try:
                still_true = loop_node.should_continue(
                    node, vars_, current_iteration=0, max_iterations=max_iter + 1
                )
            except WorkflowError:
                still_true = False
            if still_true:
                raise WorkflowError(
                    ErrorCode.LOOP_EXCEEDED,
                    f"loop {node.get('alias') or loop_id!r} hit max_iterations={max_iter}",
                    location={
                        "alias": node.get("alias"),
                        "internal_id": node.get("_internal_id"),
                    },
                )
        iters.pop(loop_id, None)
        if not _advance_cursor(workflow, cursor, vars_):
            return None, True
        advanced = True


# ---------------------------------------------------------------------------
# 单步执行
# ---------------------------------------------------------------------------


def _utc_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_run_context(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state.get("run_id"),
        "project_root": state.get("project_root"),
        "caller": state.get("caller"),
    }


def _execute_agent_call(
    node: dict[str, Any],
    state: dict[str, Any],
    workflow: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    started_at = _utc_iso()
    start_mono = time.monotonic()
    write_event(
        run_dir,
        "node_start",
        internal_id=node.get("_internal_id"),
        alias=node.get("alias"),
        node_type="agent_call",
        executor=node.get("executor") or "caller",
    )
    try:
        outcome = execute_agent_call(
            node,
            state,
            _build_run_context(state),
            workflow_executors=workflow.get("executors"),
            config=workflow.get("config"),
        )
    except WorkflowError as exc:
        duration_ms = int((time.monotonic() - start_mono) * 1000)
        write_event(
            run_dir,
            "node_end",
            internal_id=node.get("_internal_id"),
            alias=node.get("alias"),
            status="failed",
            duration_ms=duration_ms,
            error_code=exc.code,
        )
        append_history(
            state,
            {
                "internal_id": node.get("_internal_id"),
                "alias": node.get("alias"),
                "type": "agent_call",
                "executor": node.get("executor") or "caller",
                "status": "failed",
                "started_at": started_at,
                "ended_at": _utc_iso(),
                "duration_ms": duration_ms,
                "error": exc.to_dict(),
            },
            run_dir=run_dir,
        )
        raise

    duration_ms = outcome.duration_ms or int((time.monotonic() - start_mono) * 1000)
    if outcome.kind == "needs_caller":
        write_event(
            run_dir,
            "node_end",
            internal_id=node.get("_internal_id"),
            alias=node.get("alias"),
            status="awaiting_agent",
            duration_ms=duration_ms,
        )
        # 不写 history（在 advance 时根据用户回填创建一条 completed 记录）
        return {"action": "execute_agent", "payload": outcome.payload, "history_pending": {
            "internal_id": node.get("_internal_id"),
            "alias": node.get("alias"),
            "type": "agent_call",
            "executor": "caller",
            "status": "awaiting_agent",
            "started_at": started_at,
        }}

    output_name = node.get("output")
    if output_name:
        state.setdefault("vars", {})[output_name] = outcome.output
    history_entry = {
        "internal_id": node.get("_internal_id"),
        "alias": node.get("alias"),
        "type": "agent_call",
        "executor": node.get("executor") or "caller",
        "status": "completed",
        "started_at": started_at,
        "ended_at": _utc_iso(),
        "duration_ms": duration_ms,
        "output": output_name,
        "result": outcome.output,
    }
    append_history(state, history_entry, run_dir=run_dir)
    write_event(
        run_dir,
        "node_end",
        internal_id=node.get("_internal_id"),
        alias=node.get("alias"),
        status="completed",
        duration_ms=duration_ms,
        output=output_name,
    )
    return {"action": "node_completed"}


def _execute_wait_user(
    node: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    payload = wait_user_node.build_payload(node, state)
    write_event(
        run_dir,
        "node_start",
        internal_id=node.get("_internal_id"),
        alias=node.get("alias"),
        node_type="wait_user",
    )
    # 不写 history（在 resume 后写一条 completed 记录）
    return {"action": "wait_user", "payload": payload, "history_pending": {
        "internal_id": node.get("_internal_id"),
        "alias": node.get("alias"),
        "type": "wait_user",
        "status": "waiting_user",
        "started_at": _utc_iso(),
    }}


def _execute_sleep(
    node: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    started_at = _utc_iso()
    start_mono = time.monotonic()
    write_event(
        run_dir,
        "sleep_start",
        internal_id=node.get("_internal_id"),
        alias=node.get("alias"),
        seconds=node.get("seconds"),
    )
    seconds = sleep_node.execute_sleep(node, state)
    duration_ms = int((time.monotonic() - start_mono) * 1000)
    write_event(
        run_dir,
        "sleep_end",
        internal_id=node.get("_internal_id"),
        alias=node.get("alias"),
        seconds=seconds,
        duration_ms=duration_ms,
    )
    append_history(
        state,
        {
            "internal_id": node.get("_internal_id"),
            "alias": node.get("alias"),
            "type": "sleep",
            "status": "completed",
            "started_at": started_at,
            "ended_at": _utc_iso(),
            "duration_ms": duration_ms,
            "seconds": seconds,
        },
        run_dir=run_dir,
    )
    return {"action": "node_completed"}


# ---------------------------------------------------------------------------
# chain 主循环
# ---------------------------------------------------------------------------


def _chain_timeout_seconds(workflow: dict[str, Any]) -> float:
    cfg = workflow.get("config") or {}
    return float(cfg.get("chain_timeout_ms") or DEFAULT_CHAIN_TIMEOUT_MS) / 1000.0


def _bind_secrets(state: dict[str, Any]) -> None:
    """把当前 run 的 secrets 写入 logger 的 contextvar。供所有 *_action 入口调用。"""
    from lib.logger import set_run_secrets
    set_run_secrets(state.get("_secrets_values"))


def _chain(
    workflow: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    chain_started = time.monotonic()
    chain_timeout_s = _chain_timeout_seconds(workflow)
    _bind_secrets(state)

    while True:
        if state.get("status") in TERMINAL_STATUSES:
            return _finalise_result(state)
        cursor = state["cursor"]
        try:
            node, _ = _normalise_loop_entry(workflow, cursor, state.get("vars") or {})
        except WorkflowError as exc:
            return _fail(state, run_dir, exc)
        if node is None:
            state["status"] = "completed"
            write_event(run_dir, "run_end", status="completed")
            write_audit(run_dir, "run_end", status="completed")
            return _finalise_result(state)

        ntype = node.get("type")
        try:
            if ntype == "agent_call":
                step_result = _execute_agent_call(node, state, workflow, run_dir)
            elif ntype == "wait_user":
                step_result = _execute_wait_user(node, state, run_dir)
            elif ntype == "sleep":
                step_result = _execute_sleep(node, state, run_dir)
            else:
                raise WorkflowError(
                    ErrorCode.WORKFLOW_INVALID,
                    f"unsupported node type at cursor: {ntype!r}",
                )
        except WorkflowError as exc:
            return _fail(state, run_dir, exc)

        if step_result["action"] == "execute_agent":
            state["status"] = "awaiting_agent"
            state["last_payload"] = step_result["payload"]
            state["pending_node"] = step_result.get("history_pending")
            return {
                "action": "execute_agent",
                "run_id": state.get("run_id"),
                "status": "awaiting_agent",
                "payload": step_result["payload"],
            }
        if step_result["action"] == "wait_user":
            state["status"] = "waiting_user"
            state["last_payload"] = step_result["payload"]
            state["pending_node"] = step_result.get("history_pending")
            return {
                "action": "wait_user",
                "run_id": state.get("run_id"),
                "status": "waiting_user",
                "payload": step_result["payload"],
            }
        # node_completed → 推进 cursor，继续链式执行
        try:
            still_running = _advance_cursor(workflow, cursor, state.get("vars") or {})
        except WorkflowError as exc:
            return _fail(state, run_dir, exc)
        if not still_running:
            state["status"] = "completed"
            write_event(run_dir, "run_end", status="completed")
            write_audit(run_dir, "run_end", status="completed")
            return _finalise_result(state)

        if (time.monotonic() - chain_started) > chain_timeout_s:
            state["status"] = "awaiting_agent"  # caller 应再次 advance
            state["last_payload"] = None
            return {
                "action": "continue",
                "run_id": state.get("run_id"),
                "status": "awaiting_agent",
                "reason": "chain_timeout",
                "next_hint": "call advance again to resume internal chaining",
            }


def _fail(state: dict[str, Any], run_dir: Path, exc: WorkflowError) -> dict[str, Any]:
    state["status"] = "failed"
    state["error"] = exc.to_dict()
    write_event(run_dir, "run_end", status="failed", error_code=exc.code)
    write_audit(run_dir, "run_end", status="failed", error_code=exc.code)
    return {
        "action": "failed",
        "run_id": state.get("run_id"),
        "status": "failed",
        "error": exc.to_dict(),
    }


def _finalise_result(state: dict[str, Any]) -> dict[str, Any]:
    status = state.get("status") or "unknown"
    base = {
        "action": status,
        "run_id": state.get("run_id"),
        "status": status,
    }
    if status == "failed":
        base["error"] = state.get("error")
    if status == "completed":
        base["vars"] = {k: v for k, v in (state.get("vars") or {}).items() if k != "_secrets"}
    return base


# ---------------------------------------------------------------------------
# action 入口
# ---------------------------------------------------------------------------


def start_action(params: dict[str, Any]) -> dict[str, Any]:
    workflow_raw = params.get("workflow")
    if workflow_raw is None:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "workflow is required")
    initial_vars = params.get("vars") or {}
    caller = params.get("caller") or ""
    allow_missing = bool(params.get("allow_missing_executors", False))

    workflow = load_workflow(workflow_raw)
    _validate_action(
        {
            "workflow": workflow,
            "allow_missing_executors": allow_missing,
        }
    )
    assign_internal_ids(workflow)

    merged_vars = {**(workflow.get("vars") or {}), **(initial_vars or {})}
    from lib.template import collect_secret_values, expand_env_in_vars
    merged_vars = expand_env_in_vars(merged_vars)
    secrets = collect_secret_values(merged_vars)

    run_id, run_dir = create_run(
        workflow=workflow,
        workflow_source=workflow_raw if isinstance(workflow_raw, str) else None,
        initial_vars=merged_vars,
        caller=caller,
    )
    with StateTransaction(run_dir) as state:
        if secrets:
            state["_secrets_values"] = secrets
        _bind_secrets(state)
        write_event(run_dir, "run_start", run_id=run_id, workflow_name=workflow.get("name"))
        write_audit(run_dir, "run_start", caller=caller, workflow=workflow.get("name"))
        return _chain(workflow, state, run_dir)


def _ensure_run(run_id: str) -> tuple[Path, dict[str, Any]]:
    run_dir = get_run_dir(run_id)
    workflow = load_workflow_snapshot(run_dir)
    return run_dir, workflow


def _finalize_pending_history(
    state: dict[str, Any],
    *,
    run_dir: Path,
    executor: str,
    output_name: str | None,
    output_value: str | None,
    status: str = "completed",
    error: dict[str, Any] | None = None,
) -> None:
    pending = state.pop("pending_node", None)
    if not pending:
        return
    entry = {
        **pending,
        "executor": executor,
        "status": status,
        "ended_at": _utc_iso(),
    }
    try:
        started = pending.get("started_at")
        if started:
            from datetime import datetime

            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            entry["duration_ms"] = int(
                (datetime.fromisoformat(entry["ended_at"].replace("Z", "+00:00")) - dt).total_seconds() * 1000
            )
    except Exception:  # noqa: BLE001
        pass
    if output_name and output_value is not None:
        entry["output"] = output_name
        entry["result"] = output_value
    if error:
        entry["error"] = error
    append_history(state, entry, run_dir=run_dir)


def advance_action(params: dict[str, Any]) -> dict[str, Any]:
    run_id = params.get("run_id")
    if not run_id:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "run_id is required")
    result = params.get("result")
    caller_error = params.get("error")
    run_dir, workflow = _ensure_run(run_id)
    assign_internal_ids(workflow)

    with StateTransaction(run_dir) as state:
        _bind_secrets(state)
        if state.get("status") in TERMINAL_STATUSES:
            raise WorkflowError(
                ErrorCode.RUN_ALREADY_TERMINAL,
                f"run {run_id} is already {state.get('status')}",
                location={"run_id": run_id, "status": state.get("status")},
            )

        if caller_error:
            exc = WorkflowError(
                ErrorCode.CALLER_ERROR,
                f"caller reported error: {caller_error.get('message') or caller_error}",
                location={"run_id": run_id},
                caller_error=caller_error,
            )
            _finalize_pending_history(
                state,
                run_dir=run_dir,
                executor="caller",
                output_name=None,
                output_value=None,
                status="failed",
                error=exc.to_dict(),
            )
            return _fail(state, run_dir, exc)

        # 如果有 pending_node（说明上一步是 needs_caller），把 result 写回 vars + 完成 history
        if state.get("pending_node"):
            pending = state["pending_node"]
            output_name = None
            current_node = _find_node_at(workflow, state["cursor"]["path"]) if state["cursor"]["path"] else None
            if current_node and current_node.get("type") == "agent_call":
                output_name = current_node.get("output")
            if result is not None and output_name:
                state.setdefault("vars", {})[output_name] = result
            _finalize_pending_history(
                state,
                run_dir=run_dir,
                executor="caller",
                output_name=output_name,
                output_value=result if isinstance(result, str) else (str(result) if result is not None else None),
            )
            # 推进 cursor 到下一个节点
            try:
                still = _advance_cursor(workflow, state["cursor"], state.get("vars") or {})
            except WorkflowError as exc:
                return _fail(state, run_dir, exc)
            if not still:
                state["status"] = "completed"
                write_event(run_dir, "run_end", status="completed")
                return _finalise_result(state)

        state["last_payload"] = None
        return _chain(workflow, state, run_dir)


def resume_action(params: dict[str, Any]) -> dict[str, Any]:
    run_id = params.get("run_id")
    if not run_id:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "run_id is required")
    user_input = params.get("input")
    run_dir, workflow = _ensure_run(run_id)
    assign_internal_ids(workflow)

    with StateTransaction(run_dir) as state:
        _bind_secrets(state)
        if state.get("status") in TERMINAL_STATUSES:
            raise WorkflowError(
                ErrorCode.RUN_ALREADY_TERMINAL,
                f"run {run_id} is already {state.get('status')}",
                location={"run_id": run_id, "status": state.get("status")},
            )
        if state.get("status") != "waiting_user":
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"run is in status {state.get('status')!r}; resume only works for waiting_user",
                location={"run_id": run_id, "status": state.get("status")},
            )
        if state["cursor"]["path"]:
            node = _find_node_at(workflow, state["cursor"]["path"])
        else:
            raise WorkflowError(ErrorCode.WORKFLOW_INVALID, "cursor.path is empty during resume")
        if node.get("type") != "wait_user":
            raise WorkflowError(
                ErrorCode.WORKFLOW_INVALID,
                f"resume target is not wait_user (type={node.get('type')!r})",
            )

        validated = wait_user_node.validate_user_input(node, user_input)
        bind_key = node.get("output") or node.get("alias")
        if bind_key:
            state.setdefault("vars", {})[bind_key] = validated

        _finalize_pending_history(
            state,
            run_dir=run_dir,
            executor="user",
            output_name=bind_key,
            output_value=str(validated) if isinstance(validated, dict) else validated,
        )
        write_audit(run_dir, "wait_user_resumed", alias=node.get("alias"))

        try:
            still = _advance_cursor(workflow, state["cursor"], state.get("vars") or {})
        except WorkflowError as exc:
            return _fail(state, run_dir, exc)
        if not still:
            state["status"] = "completed"
            write_event(run_dir, "run_end", status="completed")
            return _finalise_result(state)

        state["last_payload"] = None
        return _chain(workflow, state, run_dir)


def status_action(params: dict[str, Any]) -> dict[str, Any]:
    run_id = params.get("run_id")
    if not run_id:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "run_id is required")
    include_events = bool(params.get("include_events", False))
    include_history = bool(params.get("include_history", True))
    event_limit = int(params.get("event_limit", 20))
    run_dir = get_run_dir(run_id)
    state = read_state(run_dir)
    payload: dict[str, Any] = {
        "run_id": state.get("run_id"),
        "workflow_name": state.get("workflow_name"),
        "status": state.get("status"),
        "caller": state.get("caller"),
        "project_root": state.get("project_root"),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
        "history_count": len(state.get("history") or []),
        "cursor": state.get("cursor"),
        "vars": {k: v for k, v in (state.get("vars") or {}).items() if k != "_secrets"},
    }
    if state.get("status") in ("awaiting_agent", "waiting_user"):
        payload["last_payload"] = state.get("last_payload")
    if state.get("status") == "failed":
        payload["error"] = state.get("error")
    if include_history:
        payload["history"] = state.get("history") or []
    if include_events:
        payload["events"] = read_events(run_dir, limit=event_limit)
    return payload


def list_action(params: dict[str, Any]) -> dict[str, Any]:
    status_filter = params.get("status")
    if isinstance(status_filter, str):
        status_filter = [status_filter]
    workflow_name = params.get("workflow_name")
    limit = int(params.get("limit", 50))
    fmt = params.get("format") or "json"
    runs = list_runs(
        status=status_filter,
        workflow_name=workflow_name,
        limit=limit,
    )
    out: dict[str, Any] = {"runs": runs, "count": len(runs)}
    if fmt == "table":
        out["table"] = render_runs_table(runs)
    return out


def abort_action(params: dict[str, Any]) -> dict[str, Any]:
    run_id = params.get("run_id")
    if not run_id:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "run_id is required")
    reason = params.get("reason") or "user_aborted"
    run_dir = get_run_dir(run_id)
    with StateTransaction(run_dir) as state:
        _bind_secrets(state)
        if state.get("status") in TERMINAL_STATUSES:
            raise WorkflowError(
                ErrorCode.RUN_ALREADY_TERMINAL,
                f"run {run_id} is already {state.get('status')}",
            )
        state["status"] = "aborted"
        state["error"] = {"code": "USER_ABORTED", "message": reason, "retryable": False}
        write_event(run_dir, "abort", reason=reason)
        write_audit(run_dir, "abort", reason=reason)
        return {
            "action": "aborted",
            "run_id": run_id,
            "status": "aborted",
            "reason": reason,
        }


def flows_action(params: dict[str, Any]) -> dict[str, Any]:
    """列出全局可用的 workflow 定义（渐进式披露入口）。"""
    from lib.store import workflows_root

    query = params.get("query")
    workflows = list_workflows(query=query)
    return {
        "workflows": workflows,
        "count": len(workflows),
        "workflows_root": str(workflows_root()),
    }


# ---------------------------------------------------------------------------
# retry：caller 显式从断点续跑
# ---------------------------------------------------------------------------


def _walk_nodes_with_path(
    nodes: list[dict[str, Any]],
    prefix: list[int] | None = None,
):
    """深度优先遍历 nodes，yield (path, node)。

    loop 节点同时 yield 其 body 内子节点（path 多一层）。
    """
    prefix = list(prefix or [])
    for idx, node in enumerate(nodes or []):
        path = prefix + [idx]
        yield path, node
        if node.get("type") == "loop":
            yield from _walk_nodes_with_path(node.get("body") or [], path)


def _cursor_path_for_alias(workflow: dict[str, Any], alias: str) -> list[int]:
    """按 alias 查找节点 path（最左匹配；alias 在 v1 已经强制同层唯一）。

    找不到 → 抛 PARAMS_INVALID。
    """
    nodes = workflow.get("nodes") or []
    for path, node in _walk_nodes_with_path(nodes):
        if node.get("alias") == alias:
            return path
    raise WorkflowError(
        ErrorCode.PARAMS_INVALID,
        f"workflow 中找不到 alias={alias!r}",
        location={"alias": alias},
    )


def _last_failed_alias(state: dict[str, Any]) -> tuple[str | None, list[int] | None]:
    """从 history / cursor / pending_node 推断"上一次失败 / 卡住的节点"。

    优先级：
        1. history 中最后一条 status == "failed" 的节点
        2. state["pending_node"]（awaiting_agent / waiting_user 卡住）
        3. cursor.path 当前指向（兜底）
    """
    history = state.get("history") or []
    for entry in reversed(history):
        if entry.get("status") == "failed" and entry.get("alias"):
            return entry["alias"], None
    pending = state.get("pending_node")
    if pending and pending.get("alias"):
        return pending["alias"], None
    cursor = state.get("cursor") or {}
    path = cursor.get("path") or []
    return None, list(path) if path else None


def _trim_history_from(state: dict[str, Any], alias: str) -> int:
    """删除 history 中从 alias 节点（含）开始的所有记录。

    返回被裁掉的条数。仅删 state 内存中的，不动 events.ndjson（审计保留）。
    """
    history: list[dict[str, Any]] = state.get("history") or []
    cut_index = None
    for idx, entry in enumerate(history):
        if entry.get("alias") == alias:
            cut_index = idx
            break
    if cut_index is None:
        return 0
    removed = len(history) - cut_index
    state["history"] = history[:cut_index]
    return removed


def _deep_merge_vars(target: dict[str, Any], patch: dict[str, Any]) -> None:
    """vars_patch 合并到 vars：dict 深合并；其他类型直接覆盖。"""
    for key, value in (patch or {}).items():
        if (
            isinstance(value, dict)
            and isinstance(target.get(key), dict)
        ):
            _deep_merge_vars(target[key], value)
        else:
            target[key] = value


def retry_action(params: dict[str, Any]) -> dict[str, Any]:
    """caller 显式从断点 / 指定 alias 重新执行。

    params:
        run_id: 必填
        alias: 可选；不传则自动从最后失败节点恢复
        vars_patch: 可选；合并到当前 vars
        skip: 可选；True 时不重跑该节点，直接把 vars_patch 当 output 写入并跳到下一节点
    """
    run_id = params.get("run_id")
    if not run_id:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "缺少必填参数 run_id")
    target_alias = params.get("alias")
    vars_patch = params.get("vars_patch") or {}
    skip = bool(params.get("skip", False))
    if vars_patch and not isinstance(vars_patch, dict):
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            "vars_patch 必须是 JSON 对象（dict）",
        )

    run_dir, workflow = _ensure_run(run_id)
    assign_internal_ids(workflow)

    with StateTransaction(run_dir) as state:
        _bind_secrets(state)
        cur_status = state.get("status")
        if cur_status not in (
            "failed",
            "awaiting_agent",
            "waiting_user",
            "executing_external",
        ):
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"retry 仅支持 failed / awaiting_agent / waiting_user / executing_external 状态的 run；当前 status={cur_status!r}",
                location={"run_id": run_id, "status": cur_status},
            )

        # 1) 决定目标 cursor.path
        if target_alias:
            new_path = _cursor_path_for_alias(workflow, target_alias)
            resolved_alias = target_alias
        else:
            inferred_alias, inferred_path = _last_failed_alias(state)
            if inferred_alias:
                new_path = _cursor_path_for_alias(workflow, inferred_alias)
                resolved_alias = inferred_alias
            elif inferred_path:
                new_path = inferred_path
                node_at = _find_node_at(workflow, new_path)
                resolved_alias = node_at.get("alias") or ""
            else:
                raise WorkflowError(
                    ErrorCode.PARAMS_INVALID,
                    "无法自动推断 retry 目标节点，请显式传入 alias 参数",
                    location={"run_id": run_id},
                )

        target_node = _find_node_at(workflow, new_path)
        target_type = target_node.get("type")

        # 2) skip 语义校验：只对 agent_call / wait_user 有意义
        if skip and target_type not in ("agent_call", "wait_user"):
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"skip=true 仅适用于 agent_call / wait_user 类型节点；目标节点 type={target_type!r}",
                location={"alias": resolved_alias, "type": target_type},
            )

        # 3) 合并 vars_patch
        if vars_patch:
            _deep_merge_vars(state.setdefault("vars", {}), vars_patch)

        # 4) 裁剪 history（从该节点开始的旧记录全部丢弃，避免审计串位）
        removed = _trim_history_from(state, resolved_alias)

        # 5) 重置 cursor / 清理 in-flight 状态
        state["cursor"] = {
            "path": list(new_path),
            "iteration_counts": (state.get("cursor") or {}).get("iteration_counts") or {},
        }
        state["error"] = None
        state["last_payload"] = None
        state["pending_node"] = None
        # 把状态翻回未完成 — skip/非skip 都需要，否则 _chain 入口会立刻 finalise
        state["status"] = "awaiting_agent"

        write_event(
            run_dir,
            "retry_invoked",
            target_alias=resolved_alias,
            target_path=list(new_path),
            skip=skip,
            vars_patch_keys=sorted(vars_patch.keys()) if vars_patch else [],
            history_trimmed=removed,
            previous_status=cur_status,
        )
        write_audit(
            run_dir,
            "retry_invoked",
            alias=resolved_alias,
            skip=skip,
            previous_status=cur_status,
        )

        # 6) skip 分支：把 vars_patch 当 output 写回 + 推进 cursor，然后再 chain
        if skip:
            output_name = target_node.get("output") or target_node.get("alias")
            output_value: Any = None
            if vars_patch and output_name and output_name in vars_patch:
                output_value = vars_patch[output_name]
            elif vars_patch and len(vars_patch) == 1:
                output_value = next(iter(vars_patch.values()))
            if output_name and output_value is not None:
                state.setdefault("vars", {})[output_name] = output_value
            append_history(
                state,
                {
                    "internal_id": target_node.get("_internal_id"),
                    "alias": resolved_alias,
                    "type": target_type,
                    "executor": target_node.get("executor") or "caller",
                    "status": "skipped",
                    "started_at": _utc_iso(),
                    "ended_at": _utc_iso(),
                    "duration_ms": 0,
                    "output": output_name,
                    "result": output_value,
                    "via": "retry_skip",
                },
                run_dir=run_dir,
            )
            try:
                still = _advance_cursor(workflow, state["cursor"], state.get("vars") or {})
            except WorkflowError as exc:
                return _fail(state, run_dir, exc)
            if not still:
                state["status"] = "completed"
                write_event(run_dir, "run_end", status="completed", via="retry_skip")
                return _finalise_result(state)
            return _chain(workflow, state, run_dir)

        # 7) 非 skip：进入 _chain 重新执行该节点
        return _chain(workflow, state, run_dir)
