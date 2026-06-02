"""view 命令：把 runs 数据序列化为 ``window.__AW_DATA__`` + 拷贝静态 SPA 模板。

设计原则:
    - ``data.js`` 只承载**纯 JSON 数据**，不含任何 HTML 字符串
    - 浏览器侧 JS 负责所有 DOM 构造与格式化
    - Python 端做的事：从 ``.agent-workflow/runs/`` 收集 state/workflow/events，
      把 nodes 打平、关联 history、解析 cursor，输出干净的结构化数据

输出 (``.agent-workflow/views/`` 下，固定每次覆盖):
    index.html        — overview SPA shell
    workflow.html     — single-run SPA shell (reads ``location.hash`` 为 run_id)
    _assets/
        base.css, overview.css, run.css       — 样式
        theme.js, overview.js, workflow.js    — 行为 + 渲染
        data.js                                — ``window.__AW_DATA__ = {...};``
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.errors import WorkflowError
from lib.logger import read_events
from lib.project_root import resolve_project_root
from lib.store import (
    GLOBAL_BASE,
    RUNS_SUBDIR,
    get_run_dir,
    list_runs,
    read_state,
    runs_root,
)

from . import templates as T

LIVE_STATUSES = {"running", "awaiting_agent", "waiting_user"}

ASSETS_DIRNAME = "_assets"
STATIC_ASSET_FILES = (
    "base.css",
    "overview.css",
    "run.css",
    "theme.js",
    "overview.js",
    "workflow.js",
)
STATIC_HTML_FILES = ("index.html", "workflow.html")


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


def _runtime_ms(created: str | None, updated: str | None) -> int | None:
    a = _parse_iso(created)
    b = _parse_iso(updated)
    if not a or not b:
        return None
    return max(0, int((b - a).total_seconds() * 1000))


def _open_url(url: str) -> bool:
    """跨平台打开 URL（支持 file:// + hash）。失败返回 False，不抛错。"""
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(
                ["open", url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif platform.system() == "Windows":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            opener = shutil.which("xdg-open") or shutil.which("sensible-browser")
            if not opener:
                return False
            subprocess.Popen(
                [opener, url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        return True
    except (FileNotFoundError, OSError):
        return False


# ---------------------------------------------------------------------------
# 节点拓扑遍历
# ---------------------------------------------------------------------------


def _flatten_nodes(workflow: dict[str, Any]) -> list[tuple[dict[str, Any], int]]:
    """把 nodes（含 loop.body）打平为 (node, indent_level) 列表。"""
    out: list[tuple[dict[str, Any], int]] = []

    def walk(nodes: list[dict[str, Any]], level: int) -> None:
        for node in nodes or []:
            out.append((node, level))
            if node.get("type") == "loop" and isinstance(node.get("body"), list):
                walk(node["body"], level + 1)

    walk(workflow.get("nodes") or [], 0)
    return out


def _resolve_cursor_alias(state: dict[str, Any], workflow: dict[str, Any]) -> str | None:
    cursor = state.get("cursor") or {}
    if not isinstance(cursor, dict):
        return None
    path = cursor.get("path")
    if not isinstance(path, list) or not path:
        return None
    try:
        nodes = workflow.get("nodes") or []
        if not (0 <= path[0] < len(nodes)):
            return None
        cur = nodes[path[0]]
        for idx in path[1:]:
            if not (isinstance(cur, dict) and isinstance(cur.get("body"), list)):
                return None
            if not (0 <= idx < len(cur["body"])):
                return None
            cur = cur["body"][idx]
        return cur.get("alias") if isinstance(cur, dict) else None
    except Exception:  # noqa: BLE001
        return None


def _group_history_by_alias(history: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in history:
        alias = entry.get("alias")
        if not alias:
            continue
        grouped.setdefault(alias, []).append(entry)
    return grouped


def _last_status_for_alias(entries: list[dict[str, Any]]) -> str | None:
    for entry in reversed(entries):
        if entry.get("status"):
            return entry["status"]
    return None


# ---------------------------------------------------------------------------
# 单 run 数据构造
# ---------------------------------------------------------------------------


def _node_summary(
    node: dict[str, Any],
    indent: int,
    entries: list[dict[str, Any]],
    is_cursor: bool,
) -> dict[str, Any]:
    """把单个 node + 其历史浓缩为前端友好的结构化数据。"""
    durations = [e.get("duration_ms") for e in entries if e.get("duration_ms") is not None]
    total_ms = sum(durations) if durations else None
    last = entries[-1] if entries else None
    last_ts = (last.get("ended_at") or last.get("started_at")) if last else None
    ntype = node.get("type") or "?"

    summary: dict[str, Any] = {
        "alias": node.get("alias") or "",
        "type": ntype,
        "indent": indent,
        "is_loop": ntype == "loop",
        "is_cursor": is_cursor,
        "description": node.get("description"),
        "status": _last_status_for_alias(entries) or ("running" if is_cursor else ""),
        "iter_count": len(entries),
        "total_duration_ms": total_ms,
        "last_ts": last_ts,
    }
    if ntype == "agent_call":
        summary["executor"] = node.get("executor")
        summary["output"] = node.get("output")
    elif ntype == "sleep":
        summary["seconds"] = node.get("seconds")
    elif ntype == "loop":
        summary["max_iterations"] = node.get("max_iterations")
        summary["condition"] = node.get("condition")
    return summary


def build_run_data(
    state: dict[str, Any],
    workflow: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """单 run 的纯 JSON 数据。供 ``data.js`` payload 用。"""
    history = state.get("history") or []
    history_by_alias = _group_history_by_alias(history)
    cursor_alias = _resolve_cursor_alias(state, workflow)
    flat_nodes = _flatten_nodes(workflow)

    nodes_data = [
        _node_summary(
            node,
            indent,
            history_by_alias.get(node.get("alias") or "", []),
            bool((node.get("alias") or "") and node.get("alias") == cursor_alias),
        )
        for node, indent in flat_nodes
    ]

    vars_view = {k: v for k, v in (state.get("vars") or {}).items() if k != "_secrets"}
    last_alias = history[-1].get("alias") if history else None

    history_durations = [
        e.get("duration_ms") for e in history if e.get("duration_ms") is not None
    ]
    avg_step_ms = (
        int(sum(history_durations) / len(history_durations))
        if history_durations
        else None
    )

    return {
        "run_id": state.get("run_id") or "",
        "workflow_name": workflow.get("name") or "workflow",
        "status": (state.get("status") or "").lower(),
        "caller": state.get("caller"),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
        "history_count": len(history),
        "event_count": len(events),
        "node_count_top": len(workflow.get("nodes") or []),
        "node_count_total": len(flat_nodes),
        "runtime_ms": _runtime_ms(state.get("created_at"), state.get("updated_at")),
        "avg_step_ms": avg_step_ms,
        "cursor_alias": cursor_alias,
        "last_alias": last_alias,
        "vars": vars_view,
        "last_payload": state.get("last_payload"),
        "error": state.get("error"),
        "nodes": nodes_data,
        "events": events,
    }


def _load_run_data(run_id: str) -> dict[str, Any] | None:
    try:
        run_dir = get_run_dir(run_id)
        state = read_state(run_dir)
    except WorkflowError:
        return None
    workflow_path = run_dir / "workflow.yaml"
    workflow: dict[str, Any] = {}
    if workflow_path.exists():
        try:
            import yaml
            workflow = yaml.safe_load(workflow_path.read_text("utf-8")) or {}
        except Exception:  # noqa: BLE001
            workflow = {}
    events = read_events(run_dir, limit=200)
    return build_run_data(state, workflow, events)


# ---------------------------------------------------------------------------
# 全量 payload + data.js 序列化
# ---------------------------------------------------------------------------


def build_data_payload(
    runs_meta: list[dict[str, Any]],
    *,
    project_root: str | None,
    extra_run_ids: list[str] | None = None,
) -> dict[str, Any]:
    """把 runs 完整 detail 数据汇总成 ``window.__AW_DATA__`` payload（纯 JSON）。

    runs_meta      : ``list_runs`` 返回的轻量 metadata 列表（确定顺序/范围）
    project_root   : project root（footer/cmdbar 展示）
    extra_run_ids  : 单 run 模式时若该 run 不在 runs_meta（被 limit 截断），
                     额外补充加载
    """
    target_ids: list[str] = []
    seen: set[str] = set()
    for r in runs_meta:
        rid = r.get("run_id")
        if rid and rid not in seen:
            seen.add(rid)
            target_ids.append(rid)
    for rid in extra_run_ids or []:
        if rid and rid not in seen:
            seen.add(rid)
            target_ids.append(rid)

    runs_data: list[dict[str, Any]] = []
    for rid in target_ids:
        data = _load_run_data(rid)
        if data is not None:
            runs_data.append(data)

    return {
        "generated_at": _utc_iso(),
        "project_root": project_root or "",
        "runs": runs_data,
    }


def _serialize_data_js(payload: dict[str, Any]) -> str:
    """把 payload 序列化为 ``window.__AW_DATA__ = {...};`` 形式（纯 JSON 数据）。"""
    body = json.dumps(payload, ensure_ascii=False, default=str)
    return (
        "// agent-workflow view data — generated by view command, do not edit by hand.\n"
        f"window.__AW_DATA__ = {body};\n"
    )


# ---------------------------------------------------------------------------
# 静态文件部署
# ---------------------------------------------------------------------------


def _install_static(views_dir: Path) -> None:
    """把 skill 内的 HTML/CSS/JS 模板拷贝到 ``views_dir``。每次都覆盖。"""
    src_dir = T.TEMPLATES_DIR
    for name in STATIC_HTML_FILES:
        src = src_dir / name
        if src.exists():
            shutil.copyfile(src, views_dir / name)

    assets_dir = views_dir / ASSETS_DIRNAME
    assets_dir.mkdir(parents=True, exist_ok=True)
    for name in STATIC_ASSET_FILES:
        src = src_dir / name
        if src.exists():
            shutil.copyfile(src, assets_dir / name)


def _write_data_js(views_dir: Path, payload: dict[str, Any]) -> Path:
    assets_dir = views_dir / ASSETS_DIRNAME
    assets_dir.mkdir(parents=True, exist_ok=True)
    out = assets_dir / "data.js"
    out.write_text(_serialize_data_js(payload), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# view_action（CLI 入口）
# ---------------------------------------------------------------------------


def view_action(params: dict[str, Any]) -> dict[str, Any]:
    """生成可视化输出。

    输出固定到 ``.agent-workflow/views/``（每次覆盖），结构:
        index.html
        workflow.html
        _assets/{base,overview,run}.css
        _assets/{theme,overview,workflow}.js
        _assets/data.js

    params:
        run_id : 可选，指定后打开 ``workflow.html#<run_id>``
        out    : 可选，指定输出根目录（默认 ``.agent-workflow/views/``）
        open   : 可选 bool，默认 true
        scope  : 'current'|'all'，默认 'current'
        limit  : int，默认 50
    """
    run_id = params.get("run_id")
    out_param = params.get("out")
    auto_open = params.get("open")
    auto_open = True if auto_open is None else bool(auto_open)
    limit = int(params.get("limit") or 50)

    views_dir = _resolve_views_dir(out_param)
    views_dir.mkdir(parents=True, exist_ok=True)

    runs_meta = list_runs(limit=limit)
    project_root = str(resolve_project_root().path)

    extra_ids = [run_id] if run_id else None
    payload = build_data_payload(
        runs_meta, project_root=project_root, extra_run_ids=extra_ids
    )

    _install_static(views_dir)
    data_path = _write_data_js(views_dir, payload)

    if run_id:
        target_path = views_dir / "workflow.html"
        url = f"file://{target_path.as_posix()}#{run_id}"
    else:
        target_path = views_dir / "index.html"
        url = f"file://{target_path.as_posix()}"

    opened = _open_url(url) if auto_open else False
    return {
        "mode": "run" if run_id else "overview",
        "run_id": run_id,
        "run_count": len(payload["runs"]),
        "views_dir": str(views_dir),
        "path": str(target_path),
        "data_path": str(data_path),
        "url": url,
        "opened": opened,
    }


def _resolve_views_dir(out_param: Any) -> Path:
    if out_param:
        p = Path(str(out_param)).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        return p
    return _safe_runs_root().parent / "views"


def _safe_runs_root() -> Path:
    try:
        return runs_root()
    except Exception:  # noqa: BLE001
        return GLOBAL_BASE / RUNS_SUBDIR


__all__ = [
    "build_run_data",
    "build_data_payload",
    "view_action",
]
