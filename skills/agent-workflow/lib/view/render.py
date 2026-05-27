"""view 命令：把 run 状态渲染为自包含 HTML。

两种模式：
    1. 总览（未传 run_id）：所有 run 的可搜索 / 可过滤表格，每个 run 同目录生成一份详情页
    2. 单 run（传 run_id）：节点拓扑 + cursor 高亮 + history 时间线 + events 流 + vars

视觉风格：shadcn / new-york 主题（zero-dependency vanilla CSS + dark/light 切换）。
本文件只负责"准备数据 + 调模板"；CSS / HTML / JS 全部在 ``templates/`` 目录。
"""
from __future__ import annotations

import html
import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.errors import ErrorCode, WorkflowError
from lib.logger import read_events
from lib.store import (
    DEFAULT_RUNS_DIRNAME,
    RUNS_SUBDIR,
    detect_project_root,
    get_run_dir,
    list_runs,
    read_state,
    runs_root,
)

from . import templates as T

# ---------------------------------------------------------------------------
# 状态 → shadcn badge variant 映射
# ---------------------------------------------------------------------------

STATUS_BADGE: dict[str, str] = {
    "running":        "badge-info",
    "awaiting_agent": "badge-info",
    "waiting_user":   "badge-warning",
    "completed":      "badge-success",
    "failed":         "badge-destructive",
    "aborted":        "badge-muted",
}


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------


def _e(value: Any) -> str:
    """HTML escape，None → 空字符串。"""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in value)


def _badge_class(status: str | None) -> str:
    return STATUS_BADGE.get(status or "", "badge-muted")


def _open_in_browser(path: Path) -> bool:
    """跨平台自动打开 HTML。失败返回 False，不抛错。"""
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(
                ["open", str(path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif platform.system() == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            opener = shutil.which("xdg-open") or shutil.which("sensible-browser")
            if not opener:
                return False
            subprocess.Popen(
                [opener, str(path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        return True
    except (FileNotFoundError, OSError):
        return False


# ---------------------------------------------------------------------------
# 节点 / history / events 行渲染
# ---------------------------------------------------------------------------


def _node_status_for_alias(history: list[dict[str, Any]], alias: str) -> str | None:
    for entry in reversed(history):
        if entry.get("alias") == alias:
            return entry.get("status")
    return None


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


def _build_node_meta(node: dict[str, Any]) -> str:
    parts: list[str] = []
    ntype = node.get("type")
    if ntype == "agent_call":
        parts.append(f"executor: <code>{_e(node.get('executor') or '-')}</code>")
        if node.get("output"):
            parts.append(f"output: <code>{_e(node.get('output'))}</code>")
    if ntype == "sleep" and node.get("seconds") is not None:
        parts.append(f"seconds: <code>{_e(node.get('seconds'))}</code>")
    if ntype == "loop":
        if node.get("max_iterations") is not None:
            parts.append(f"max_iter: <code>{_e(node.get('max_iterations'))}</code>")
        if node.get("condition"):
            parts.append(f"cond: <code>{_e(node.get('condition'))}</code>")
    if node.get("description"):
        parts.append(_e(node.get("description")))
    if not parts:
        return "&nbsp;"
    return '<span class="sep">·</span>'.join(parts)


def _node_classes(indent: int, is_cursor: bool, is_loop: bool) -> str:
    classes: list[str] = []
    if indent > 0:
        classes.append(f"indented-{min(indent, 2)}")
    if is_cursor:
        classes.append("is-cursor")
    if is_loop:
        classes.append("is-loop")
    return " ".join(classes)


def _render_node_row(
    node: dict[str, Any],
    indent: int,
    history: list[dict[str, Any]],
    cursor_alias: str | None,
) -> str:
    alias = node.get("alias") or ""
    ntype = node.get("type") or "?"
    is_cursor = bool(alias and alias == cursor_alias)
    status = _node_status_for_alias(history, alias) or ("running" if is_cursor else "")

    duration_html = ""
    for entry in reversed(history):
        if entry.get("alias") == alias and entry.get("duration_ms") is not None:
            duration_html = f"{entry['duration_ms']} ms"
            break

    cursor_tag = '<span class="badge badge-outline">current</span>' if is_cursor else ""

    return T.render_fragment(
        "node_row.html",
        node_classes=_node_classes(indent, is_cursor, ntype == "loop"),
        status=_e(status),
        alias=_e(alias),
        ntype=_e(ntype),
        cursor_tag=cursor_tag,
        meta=_build_node_meta(node),
        duration=_e(duration_html),
    )


def _render_history_row(entry: dict[str, Any]) -> str:
    return T.render_fragment(
        "history_row.html",
        alias=_e(entry.get("alias") or "?"),
        ntype=_e(entry.get("type") or "?"),
        status=_e(entry.get("status") or "?"),
        status_badge_class=_badge_class(entry.get("status")),
        started=_e(entry.get("started_at") or ""),
        ended=_e(entry.get("ended_at") or ""),
        duration=_e(f"{entry['duration_ms']} ms" if entry.get("duration_ms") is not None else "-"),
    )


def _render_event_row(event: dict[str, Any]) -> str:
    etype = event.get("type") or "?"
    extra = {k: v for k, v in event.items() if k not in ("ts", "type")}
    fields = " ".join(
        f"{_e(k)}=<code>{_e(v if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False))}</code>"
        for k, v in extra.items()
    )
    css = ""
    if etype == "error" or "error_code" in extra:
        css = "error"
    elif etype.endswith("_end") and extra.get("status") == "failed":
        css = "error"
    elif etype == "run_end" and extra.get("status") == "completed":
        css = "success"
    return T.render_fragment(
        "event_row.html",
        event_class=css,
        ts=_e(event.get("ts") or ""),
        etype=_e(etype),
        fields=fields,
    )


# ---------------------------------------------------------------------------
# 主渲染
# ---------------------------------------------------------------------------


def _shared_assets() -> dict[str, str]:
    """共享的 CSS/JS 资产，每个模板都需要。"""
    return {
        "base_css": T.load("base.css"),
        "theme_js": T.load("theme.js"),
        "theme_toggle": T.load("fragments/theme_toggle.html"),
    }


def render_run_detail_html(
    state: dict[str, Any],
    workflow: dict[str, Any],
    events: list[dict[str, Any]],
) -> str:
    history = state.get("history") or []
    cursor_alias = _resolve_cursor_alias(state, workflow)

    node_rows = "\n".join(
        _render_node_row(node, lvl, history, cursor_alias)
        for node, lvl in _flatten_nodes(workflow)
    )
    history_rows = (
        "\n".join(_render_history_row(e) for e in history)
        or '<tr><td colspan="6" class="muted">no history yet</td></tr>'
    )
    event_rows = (
        "\n".join(_render_event_row(e) for e in events)
        or '<div class="event-row muted">no events</div>'
    )

    vars_view = {k: v for k, v in (state.get("vars") or {}).items() if k != "_secrets"}
    vars_pretty = json.dumps(vars_view, ensure_ascii=False, indent=2, default=str)

    last_payload_block = ""
    if state.get("last_payload"):
        last_payload_block = (
            '<div class="card">'
            '<div class="card-header"><h2>Last payload</h2>'
            '<span class="count">caller handoff</span></div>'
            '<div class="card-content">'
            f'<pre>{_e(json.dumps(state["last_payload"], ensure_ascii=False, indent=2))}</pre>'
            "</div></div>"
        )

    error_block = ""
    if state.get("error"):
        error_block = (
            '<div class="card" style="border-color:var(--destructive);">'
            '<div class="card-header" style="border-bottom-color:var(--destructive);">'
            '<h2 style="color:var(--destructive);">Error</h2>'
            f'<span class="badge badge-destructive">{_e(state["error"].get("code") or "ERROR")}</span></div>'
            '<div class="card-content">'
            f'<pre>{_e(json.dumps(state["error"], ensure_ascii=False, indent=2))}</pre>'
            "</div></div>"
        )

    return T.render(
        "run.html",
        **_shared_assets(),
        run_css=T.load("run.css"),
        title=f"agent-workflow · {state.get('run_id') or ''}",
        workflow_name=_e(workflow.get("name") or "workflow"),
        run_id=_e(state.get("run_id")),
        status=_e(state.get("status") or "?"),
        status_badge_class=_badge_class(state.get("status")),
        caller=_e(state.get("caller") or "-"),
        created_at=_e(state.get("created_at") or "-"),
        updated_at=_e(state.get("updated_at") or "-"),
        node_count=len(workflow.get("nodes") or []),
        node_rows=node_rows,
        history_count=len(history),
        history_rows=history_rows,
        event_count=len(events),
        event_rows=event_rows,
        vars_pretty=_e(vars_pretty),
        last_payload_block=last_payload_block,
        error_block=error_block,
        generated_at=_utc_iso(),
    )


def render_overview_html(runs: list[dict[str, Any]], *, project_root: str | None) -> str:
    statuses_present = sorted({r.get("status") or "?" for r in runs})
    status_options = "".join(
        f'<option value="{_e(s)}">{_e(s)}</option>' for s in statuses_present
    )

    run_rows_parts: list[str] = []
    for r in runs:
        rid = r.get("run_id") or ""
        search_blob = " ".join(
            str(r.get(k) or "") for k in ("run_id", "workflow_name", "caller", "last_alias")
        )
        run_rows_parts.append(
            T.render_fragment(
                "run_row.html",
                status=_e(r.get("status")),
                status_badge_class=_badge_class(r.get("status")),
                search=_e(search_blob),
                link=_e(f"./{_slugify(rid)}.html"),
                run_id=_e(rid),
                workflow_name=_e(r.get("workflow_name") or "-"),
                history_count=_e(r.get("history_count") or 0),
                last_alias=_e(r.get("last_alias") or "-"),
                updated_at=_e(r.get("updated_at") or "-"),
            )
        )
    run_rows = (
        "\n".join(run_rows_parts)
        or '<tr><td colspan="6" class="muted" style="text-align:center;padding:2rem;">no runs found</td></tr>'
    )

    return T.render(
        "overview.html",
        **_shared_assets(),
        overview_js=T.load("overview.js"),
        title="agent-workflow · runs",
        project_root=_e(project_root or "."),
        total=len(runs),
        status_options=status_options,
        run_rows=run_rows,
        generated_at=_utc_iso(),
    )


# ---------------------------------------------------------------------------
# view_action（CLI 入口）
# ---------------------------------------------------------------------------


def view_action(params: dict[str, Any]) -> dict[str, Any]:
    """生成可视化 HTML。

    params:
        run_id: 可选；若不传则生成总览 + 每个 run 一份详情页
        out:    可选；输出路径；不传则放在 .agent-workflow/views/ 下
        open:   可选 bool，默认 true；是否自动用系统命令打开生成的 HTML
        scope:  可选 'current'|'all'，仅 overview 模式使用，默认 'current'
        limit:  可选 int，仅 overview 模式使用，默认 50
    """
    run_id = params.get("run_id")
    out_param = params.get("out")
    auto_open = params.get("open")
    auto_open = True if auto_open is None else bool(auto_open)

    if run_id:
        run_dir = get_run_dir(run_id)
        state = read_state(run_dir)
        workflow_path = run_dir / "workflow.yaml"
        if not workflow_path.exists():
            raise WorkflowError(
                ErrorCode.WORKFLOW_SNAPSHOT_CORRUPTED,
                f"workflow snapshot missing for run {run_id}",
                location={"run_id": run_id, "expected": str(workflow_path)},
            )
        import yaml
        workflow = yaml.safe_load(workflow_path.read_text("utf-8")) or {}
        events = read_events(run_dir, limit=200)
        html_text = render_run_detail_html(state, workflow, events)
        out_path = _resolve_out_path(out_param, default=run_dir / "view.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_text, encoding="utf-8")
        opened = _open_in_browser(out_path) if auto_open else False
        return {
            "mode": "run",
            "run_id": run_id,
            "path": str(out_path),
            "opened": opened,
        }

    scope = params.get("scope") or "current"
    limit = int(params.get("limit") or 50)
    runs = list_runs(scope=scope, limit=limit)
    project_root = str(detect_project_root() or "")

    default_dir = runs_root().parent / "views" / time.strftime("view-%Y%m%d-%H%M%S")
    out_path = _resolve_out_path(out_param, default=default_dir / "index.html")
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    detail_files: list[str] = []
    for r in runs:
        rid = r.get("run_id")
        if not rid:
            continue
        try:
            run_dir = get_run_dir(rid)
            state = read_state(run_dir)
            workflow_path = run_dir / "workflow.yaml"
            import yaml
            workflow = (
                yaml.safe_load(workflow_path.read_text("utf-8")) if workflow_path.exists() else {}
            )
            events = read_events(run_dir, limit=200)
            html_text = render_run_detail_html(state, workflow or {}, events)
            detail_path = out_dir / f"{_slugify(rid)}.html"
            detail_path.write_text(html_text, encoding="utf-8")
            detail_files.append(detail_path.name)
        except WorkflowError:
            continue

    overview = render_overview_html(runs, project_root=project_root)
    out_path.write_text(overview, encoding="utf-8")
    opened = _open_in_browser(out_path) if auto_open else False
    return {
        "mode": "overview",
        "run_count": len(runs),
        "path": str(out_path),
        "detail_count": len(detail_files),
        "opened": opened,
    }


def _resolve_out_path(out_param: Any, *, default: Path) -> Path:
    if out_param:
        p = Path(out_param).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        return p
    return default


def _safe_runs_root() -> Path:
    """兼容测试环境 runs_root() 失败的场景。"""
    try:
        return runs_root()
    except Exception:  # noqa: BLE001
        return Path.cwd() / DEFAULT_RUNS_DIRNAME / RUNS_SUBDIR


__all__ = ["render_overview_html", "render_run_detail_html", "view_action"]
