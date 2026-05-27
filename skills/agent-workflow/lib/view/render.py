"""view 命令：把 run 状态渲染为自包含 HTML。

两种模式：
    1. 总览（未传 run_id）：所有 run 的卡片网格，点击跳转单 run 详情
    2. 单 run（传 run_id）：展示节点拓扑 + 状态色块 + history 时间线 + 最近 events 流

所有产物为 self-contained HTML（vanilla CSS + 最小 JS，零外部依赖）。
"""
from __future__ import annotations

import html
import json
import os
import platform
import shutil
import subprocess
import sys
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

STATUS_COLORS: dict[str, str] = {
    "running": "#1f6feb",
    "awaiting_agent": "#9a6700",
    "waiting_user": "#bf8700",
    "completed": "#1a7f37",
    "failed": "#cf222e",
    "aborted": "#656d76",
}


def _e(value: Any) -> str:
    """HTML escape，None → 空字符串。"""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in value)


def _open_in_browser(path: Path) -> bool:
    """跨平台自动打开 HTML。失败返回 False，不抛错。"""
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.system() == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            opener = shutil.which("xdg-open") or shutil.which("sensible-browser")
            if not opener:
                return False
            subprocess.Popen([opener, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (FileNotFoundError, OSError):
        return False


# ---------------------------------------------------------------------------
# CSS / JS（共用）
# ---------------------------------------------------------------------------


_BASE_CSS = """
*,*::before,*::after { box-sizing: border-box; }
body {
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  margin: 0; padding: 24px; background: #f6f8fa; color: #1f2328;
}
h1, h2, h3 { margin: 0 0 12px; font-weight: 600; }
h1 { font-size: 24px; }
h2 { font-size: 18px; margin-top: 28px; }
h3 { font-size: 15px; margin-top: 18px; color: #57606a; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
.muted { color: #57606a; }
code { font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, monospace; font-size: 12.5px; background: #eaeef2; padding: 1px 5px; border-radius: 3px; }
pre { background: #0d1117; color: #e6edf3; padding: 12px 16px; border-radius: 6px; overflow-x: auto; font-size: 12.5px; line-height: 1.45; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; color: #fff; font-size: 12px; font-weight: 500; }
.card { background: #fff; border: 1px solid #d0d7de; border-radius: 6px; padding: 16px 20px; margin-bottom: 16px; }
.kv { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; font-size: 13px; }
.kv dt { color: #57606a; }
.kv dd { margin: 0; }
table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eaeef2; font-size: 13px; }
th { background: #f6f8fa; font-weight: 600; color: #57606a; }
tr:last-child td { border-bottom: 0; }
tr:hover { background: #f6f8fa; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.toolbar input { padding: 6px 10px; border: 1px solid #d0d7de; border-radius: 6px; font: inherit; min-width: 240px; }
.toolbar select { padding: 6px 10px; border: 1px solid #d0d7de; border-radius: 6px; font: inherit; background: #fff; }
"""


_RUN_DETAIL_CSS = """
.node-list { display: flex; flex-direction: column; gap: 8px; }
.node { display: grid; grid-template-columns: 32px 1fr auto; gap: 12px; align-items: center; padding: 10px 14px; border: 1px solid #d0d7de; border-radius: 6px; background: #fff; }
.node.is-cursor { border-color: #0969da; box-shadow: 0 0 0 2px rgba(9,105,218,0.12); }
.node.is-loop { background: #fff8e1; }
.node-status-dot { width: 14px; height: 14px; border-radius: 50%; background: #d0d7de; }
.node-status-dot.completed { background: #1a7f37; }
.node-status-dot.failed    { background: #cf222e; }
.node-status-dot.awaiting_agent { background: #9a6700; }
.node-status-dot.waiting_user { background: #bf8700; }
.node-status-dot.running   { background: #1f6feb; }
.node-meta { color: #57606a; font-size: 12.5px; margin-top: 2px; }
.node-alias { font-weight: 600; }
.node-type  { color: #57606a; }
.node.indented-1 { margin-left: 24px; border-left: 3px solid #d4a72c; }
.node.indented-2 { margin-left: 48px; border-left: 3px solid #d4a72c; }

.event-list { font-family: ui-monospace, SFMono-Regular, "SF Mono", monospace; font-size: 12.5px; max-height: 480px; overflow-y: auto; border: 1px solid #d0d7de; border-radius: 6px; background: #fff; }
.event-list .event-row { padding: 6px 12px; border-bottom: 1px solid #f0f3f6; }
.event-list .event-row:last-child { border-bottom: 0; }
.event-list .event-ts { color: #57606a; margin-right: 8px; }
.event-list .event-type { color: #0969da; font-weight: 500; margin-right: 8px; }
.event-list .event-row.error .event-type { color: #cf222e; }
.event-list .event-fields { color: #1f2328; }
"""


_OVERVIEW_JS = """
(function () {
  const input = document.getElementById('q');
  const statusSel = document.getElementById('status-filter');
  const rows = Array.from(document.querySelectorAll('tbody tr[data-row]'));
  function applyFilter() {
    const q = (input.value || '').toLowerCase();
    const st = statusSel.value;
    let visible = 0;
    rows.forEach((row) => {
      const text = row.getAttribute('data-search') || '';
      const status = row.getAttribute('data-status') || '';
      const matchQ = !q || text.toLowerCase().includes(q);
      const matchS = !st || status === st;
      row.style.display = (matchQ && matchS) ? '' : 'none';
      if (matchQ && matchS) visible += 1;
    });
    const count = document.getElementById('match-count');
    if (count) count.textContent = visible + ' / ' + rows.length;
  }
  input.addEventListener('input', applyFilter);
  statusSel.addEventListener('change', applyFilter);
  applyFilter();
})();
"""


# ---------------------------------------------------------------------------
# 单 run 详情
# ---------------------------------------------------------------------------


def _node_status_for_alias(history: list[dict[str, Any]], alias: str) -> str | None:
    """从 history 倒序找该 alias 的状态，返回 None 表示未执行。"""
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


def _render_node_row(
    node: dict[str, Any],
    indent: int,
    history: list[dict[str, Any]],
    cursor_alias: str | None,
) -> str:
    alias = node.get("alias") or ""
    ntype = node.get("type") or "?"
    executor = node.get("executor") or "-"
    status = _node_status_for_alias(history, alias) or ("running" if alias == cursor_alias else "")
    classes = ["node"]
    if indent > 0:
        classes.append(f"indented-{min(indent, 2)}")
    if alias == cursor_alias:
        classes.append("is-cursor")
    if ntype == "loop":
        classes.append("is-loop")
    extra: list[str] = []
    if ntype == "agent_call":
        extra.append(f"executor: <code>{_e(executor)}</code>")
    if ntype == "sleep" and node.get("seconds") is not None:
        extra.append(f"seconds: <code>{_e(node.get('seconds'))}</code>")
    if ntype == "loop":
        if node.get("max_iterations") is not None:
            extra.append(f"max_iter: <code>{_e(node.get('max_iterations'))}</code>")
        if node.get("condition"):
            extra.append(f"cond: <code>{_e(node.get('condition'))}</code>")
    if node.get("description"):
        extra.append(_e(node.get("description")))
    meta = " · ".join(extra) if extra else "&nbsp;"
    badge_attr = f"data-status={_e(status)}" if status else ""
    duration_html = ""
    for entry in reversed(history):
        if entry.get("alias") == alias and entry.get("duration_ms") is not None:
            duration_html = f"<span class='muted'>{entry['duration_ms']} ms</span>"
            break
    return (
        f"<div class='{' '.join(classes)}' {badge_attr}>"
        f"<span class='node-status-dot {_e(status)}'></span>"
        f"<div>"
        f"<div><span class='node-alias'>{_e(alias)}</span> "
        f"<span class='node-type'>· {_e(ntype)}</span></div>"
        f"<div class='node-meta'>{meta}</div>"
        f"</div>"
        f"<div>{duration_html}</div>"
        f"</div>"
    )


def _render_history_row(entry: dict[str, Any]) -> str:
    alias = entry.get("alias") or "?"
    ntype = entry.get("type") or "?"
    status = entry.get("status") or "?"
    color = STATUS_COLORS.get(status, "#656d76")
    duration = entry.get("duration_ms")
    duration_str = f"{duration} ms" if duration is not None else "-"
    started = entry.get("started_at") or ""
    ended = entry.get("ended_at") or ""
    return (
        f"<tr><td><code>{_e(alias)}</code></td>"
        f"<td>{_e(ntype)}</td>"
        f"<td><span class='badge' style='background:{color}'>{_e(status)}</span></td>"
        f"<td class='muted'>{_e(started)}</td>"
        f"<td class='muted'>{_e(ended)}</td>"
        f"<td>{_e(duration_str)}</td></tr>"
    )


def _render_event_row(event: dict[str, Any]) -> str:
    ts = event.get("ts") or ""
    etype = event.get("type") or "?"
    extra_keys = {k: v for k, v in event.items() if k not in ("ts", "type")}
    body = " ".join(f"{_e(k)}=<code>{_e(v if not isinstance(v, (dict, list)) else json.dumps(v, ensure_ascii=False))}</code>" for k, v in extra_keys.items())
    css = "event-row"
    if etype == "error" or "error_code" in extra_keys:
        css += " error"
    return (
        f"<div class='{css}'>"
        f"<span class='event-ts'>{_e(ts)}</span>"
        f"<span class='event-type'>{_e(etype)}</span>"
        f"<span class='event-fields'>{body}</span>"
        f"</div>"
    )


def render_run_detail_html(
    state: dict[str, Any],
    workflow: dict[str, Any],
    events: list[dict[str, Any]],
) -> str:
    run_id = state.get("run_id") or ""
    status = state.get("status") or "?"
    status_color = STATUS_COLORS.get(status, "#656d76")
    history = state.get("history") or []

    cursor = state.get("cursor") or {}
    cursor_alias: str | None = None
    cursor_path = cursor.get("path") if isinstance(cursor, dict) else None
    if isinstance(cursor_path, list) and cursor_path:
        try:
            nodes = workflow.get("nodes") or []
            cur = nodes[cursor_path[0]] if 0 <= cursor_path[0] < len(nodes) else None
            for idx in cursor_path[1:]:
                if cur and isinstance(cur.get("body"), list) and 0 <= idx < len(cur["body"]):
                    cur = cur["body"][idx]
                else:
                    cur = None
                    break
            if cur:
                cursor_alias = cur.get("alias")
        except Exception:  # noqa: BLE001
            cursor_alias = None

    node_rows = "\n".join(_render_node_row(node, lvl, history, cursor_alias) for node, lvl in _flatten_nodes(workflow))
    history_rows = "\n".join(_render_history_row(entry) for entry in history) or "<tr><td colspan='6' class='muted'>no history yet</td></tr>"
    event_rows = "\n".join(_render_event_row(e) for e in events) or "<div class='event-row muted'>no events</div>"

    vars_view = {k: v for k, v in (state.get("vars") or {}).items() if k != "_secrets"}
    vars_pretty = json.dumps(vars_view, ensure_ascii=False, indent=2, default=str)
    last_payload = state.get("last_payload")
    last_payload_block = ""
    if last_payload:
        last_payload_block = (
            f"<div class='card'><h3>Last payload (caller handoff)</h3>"
            f"<pre>{_e(json.dumps(last_payload, ensure_ascii=False, indent=2))}</pre></div>"
        )

    error_block = ""
    if state.get("error"):
        error_block = (
            f"<div class='card' style='border-color:#cf222e;background:#fff5f5;'>"
            f"<h3 style='color:#cf222e'>Error</h3>"
            f"<pre>{_e(json.dumps(state.get('error'), ensure_ascii=False, indent=2))}</pre></div>"
        )

    title = f"agent-workflow · {run_id}"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title>
<style>{_BASE_CSS}{_RUN_DETAIL_CSS}</style>
</head>
<body>
<h1>{_e(workflow.get('name') or 'workflow')} <span class='muted'>· {_e(run_id)}</span></h1>
<div class='toolbar'>
  <span class='badge' style='background:{status_color}'>{_e(status)}</span>
  <span class='muted'>caller: <code>{_e(state.get('caller'))}</code></span>
  <span class='muted'>created: {_e(state.get('created_at'))}</span>
  <span class='muted'>updated: {_e(state.get('updated_at'))}</span>
</div>

<div class='card'>
<h2>Nodes</h2>
<div class='node-list'>
{node_rows}
</div>
</div>

{last_payload_block}
{error_block}

<div class='card'>
<h2>History ({len(history)})</h2>
<table>
<thead><tr><th>alias</th><th>type</th><th>status</th><th>started</th><th>ended</th><th>duration</th></tr></thead>
<tbody>
{history_rows}
</tbody>
</table>
</div>

<div class='card'>
<h2>Events ({len(events)})</h2>
<div class='event-list'>
{event_rows}
</div>
</div>

<div class='card'>
<h2>vars</h2>
<pre>{_e(vars_pretty)}</pre>
</div>

<p class='muted'>generated at {_e(_utc_iso())}</p>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 总览
# ---------------------------------------------------------------------------


def render_overview_html(runs: list[dict[str, Any]], *, project_root: str | None) -> str:
    statuses_present = sorted({r.get("status") or "?" for r in runs})
    status_options = "".join(f"<option value='{_e(s)}'>{_e(s)}</option>" for s in statuses_present)
    rows = []
    for r in runs:
        color = STATUS_COLORS.get(r.get("status") or "", "#656d76")
        search_blob = " ".join(str(r.get(k) or "") for k in ("run_id", "workflow_name", "caller", "last_alias"))
        link = f"./{_slugify(r.get('run_id') or '')}.html"
        rows.append(
            f"<tr data-row data-status='{_e(r.get('status'))}' data-search='{_e(search_blob)}'>"
            f"<td><a href='{_e(link)}'><code>{_e(r.get('run_id'))}</code></a></td>"
            f"<td>{_e(r.get('workflow_name'))}</td>"
            f"<td><span class='badge' style='background:{color}'>{_e(r.get('status'))}</span></td>"
            f"<td>{_e(r.get('history_count'))}</td>"
            f"<td><code>{_e(r.get('last_alias') or '-')}</code></td>"
            f"<td class='muted'>{_e(r.get('updated_at'))}</td>"
            f"</tr>"
        )
    if not rows:
        rows = ["<tr><td colspan='6' class='muted'>no runs found</td></tr>"]

    title = "agent-workflow · runs"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title>
<style>{_BASE_CSS}</style>
</head>
<body>
<h1>agent-workflow runs <span class='muted'>· {_e(project_root or '.')}</span></h1>
<div class='toolbar'>
  <input id='q' type='search' placeholder='搜索 run_id / workflow / caller / alias'>
  <select id='status-filter'>
    <option value=''>all status</option>
    {status_options}
  </select>
  <span class='muted'>matches: <code id='match-count'>{len(runs)} / {len(runs)}</code></span>
</div>
<table>
<thead><tr><th>run_id</th><th>workflow</th><th>status</th><th>steps</th><th>last alias</th><th>updated</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
<p class='muted'>generated at {_e(_utc_iso())} · 单 run 详情见同目录下 <code>&lt;run_id&gt;.html</code></p>
<script>{_OVERVIEW_JS}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# view_action（CLI 入口）
# ---------------------------------------------------------------------------


def view_action(params: dict[str, Any]) -> dict[str, Any]:
    """生成可视化 HTML。

    params:
        run_id: 可选；若不传则生成总览 + 每个 run 一份详情页
        out:    可选；输出路径；不传则放在 <runs_root>/views/ 下
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
        import yaml  # 延迟 import
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

    # 生成总览 + 每个 run 单独一份
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
            workflow = yaml.safe_load(workflow_path.read_text("utf-8")) if workflow_path.exists() else {}
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


# 兼容 store.runs_root 在测试环境拿不到 default value 时 fallback
def _safe_runs_root() -> Path:
    try:
        return runs_root()
    except Exception:  # noqa: BLE001
        return Path.cwd() / DEFAULT_RUNS_DIRNAME / RUNS_SUBDIR


__all__ = ["render_overview_html", "render_run_detail_html", "view_action"]
