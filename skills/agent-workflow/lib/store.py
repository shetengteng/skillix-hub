"""持久化层：workflow 定义 + run 状态，统一存放于 .agent-workflow/ 下。

目录布局：
    <project_root>/.agent-workflow/
    ├── workflows/              # 用户自定义 workflow 定义（YAML）
    │   └── <name>.yaml
    └── runs/                   # 运行实例
        └── <run_id>/
            ├── state.json      # 唯一可变状态（带 filelock）
            ├── workflow.yaml   # 启动时快照（含分配的 _internal_id）
            ├── events.ndjson   # logger.py 维护
            ├── audit.log       # logger.py 维护
            └── outputs/
                └── <uuid>.txt  # 大 result 落盘

路径选择：
    1. 显式 override（绝对路径）覆盖一切
    2. 否则 <project_root>/.agent-workflow/{workflows,runs}/
    3. project_root 自动检测：从 cwd 向上找 .git / pyproject.toml / package.json / Cargo.toml / go.mod
       找不到 → 用 cwd
"""
from __future__ import annotations

import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock, Timeout

from lib.errors import ErrorCode, WorkflowError

DEFAULT_RUNS_DIRNAME = ".agent-workflow"
RUNS_SUBDIR = "runs"
WORKFLOWS_SUBDIR = "workflows"
LARGE_RESULT_BYTES = 10 * 1024  # >10KB 自动落盘到 outputs/
PROJECT_MARKERS = (".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def detect_project_root(start: Path | None = None) -> Path:
    """从 start 向上找项目根，找不到返回 start（默认 cwd）。"""
    cur = (start or Path.cwd()).resolve()
    seen: set[Path] = set()
    while True:
        if cur in seen:
            return start.resolve() if start else Path.cwd().resolve()
        seen.add(cur)
        for marker in PROJECT_MARKERS:
            if (cur / marker).exists():
                return cur
        if cur.parent == cur:
            return (start or Path.cwd()).resolve()
        cur = cur.parent


def runs_root(project_root: Path | None = None, *, override: Path | None = None) -> Path:
    if override is not None:
        return Path(override).expanduser().resolve()
    root = project_root or detect_project_root()
    return (root / DEFAULT_RUNS_DIRNAME / RUNS_SUBDIR).resolve()


def workflows_root(project_root: Path | None = None, *, override: Path | None = None) -> Path:
    """返回 workflow 定义文件的存储目录：<project_root>/.agent-workflow/workflows/"""
    if override is not None:
        return Path(override).expanduser().resolve()
    root = project_root or detect_project_root()
    return (root / DEFAULT_RUNS_DIRNAME / WORKFLOWS_SUBDIR).resolve()


def get_run_dir(run_id: str, *, runs_root_override: Path | None = None) -> Path:
    """解析 run_id 到磁盘路径；自动跨 project_root 搜索（list 接力场景）。"""
    if not run_id:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "run_id is required")
    if runs_root_override:
        path = runs_root_override / run_id
        if path.exists():
            return path
        raise WorkflowError(
            ErrorCode.RUN_NOT_FOUND, f"run_id not found: {run_id}",
            location={"runs_root": str(runs_root_override)},
        )
    here = runs_root()
    candidate = here / run_id
    if candidate.exists():
        return candidate
    raise WorkflowError(
        ErrorCode.RUN_NOT_FOUND,
        f"run_id not found under {here}",
        location={"runs_root": str(here), "run_id": run_id},
    )


def _new_run_id() -> str:
    return f"wf-{_utc_compact()}-{uuid.uuid4().hex[:6]}"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _lock_for(run_dir: Path, *, timeout: float = 0) -> FileLock:
    return FileLock(str(run_dir / "state.lock"), timeout=timeout)


def create_run(
    *,
    workflow: dict[str, Any],
    workflow_source: str | None,
    initial_vars: dict[str, Any],
    caller: str | None,
    project_root: Path | None = None,
    runs_root_override: Path | None = None,
) -> tuple[str, Path]:
    """创建 run 目录 + state.json + workflow.yaml 快照。返回 (run_id, run_dir)。"""
    project = (project_root or detect_project_root()).resolve()
    root = runs_root(project, override=runs_root_override)
    root.mkdir(parents=True, exist_ok=True)
    run_id = _new_run_id()
    run_dir = root / run_id
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)

    snapshot_path = run_dir / "workflow.yaml"
    snapshot_path.write_text(
        yaml.safe_dump(workflow, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    state: dict[str, Any] = {
        "run_id": run_id,
        "workflow_name": workflow.get("name", "<unknown>"),
        "workflow_source": workflow_source or "",
        "project_root": str(project),
        "caller": caller or "",
        "status": "awaiting_agent",
        "cursor": {"path": [0], "iteration_counts": {}},
        "vars": dict(initial_vars or {}),
        "history": [],
        "last_payload": None,
        "error": None,
        "created_at": _utc_iso(),
        "updated_at": _utc_iso(),
    }
    _atomic_write_json(run_dir / "state.json", state)
    return run_id, run_dir


def load_workflow_snapshot(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "workflow.yaml"
    if not path.exists():
        raise WorkflowError(
            ErrorCode.WORKFLOW_SNAPSHOT_CORRUPTED,
            f"workflow.yaml snapshot missing in {run_dir}",
        )
    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except yaml.YAMLError as exc:
        raise WorkflowError(
            ErrorCode.WORKFLOW_SNAPSHOT_CORRUPTED,
            f"workflow.yaml snapshot corrupted: {exc}",
        ) from exc
    if not isinstance(data, dict):
        raise WorkflowError(
            ErrorCode.WORKFLOW_SNAPSHOT_CORRUPTED,
            "workflow.yaml snapshot root must be a mapping",
        )
    return data


def read_state(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "state.json"
    if not path.exists():
        raise WorkflowError(
            ErrorCode.RUN_NOT_FOUND, f"state.json missing in {run_dir}"
        )
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(
            ErrorCode.WORKFLOW_SNAPSHOT_CORRUPTED,
            f"state.json corrupted: {exc}",
        ) from exc


def write_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = _utc_iso()
    _atomic_write_json(run_dir / "state.json", state)


class StateTransaction:
    """`with StateTransaction(run_dir) as state: ...` —— 自动加锁、读写。"""

    def __init__(self, run_dir: Path, *, timeout: float = 0) -> None:
        self.run_dir = run_dir
        self.lock = _lock_for(run_dir, timeout=timeout)
        self.state: dict[str, Any] = {}

    def __enter__(self) -> dict[str, Any]:
        try:
            self.lock.acquire(timeout=0)
        except Timeout as exc:
            raise WorkflowError(
                ErrorCode.RUN_BUSY,
                f"state.json is locked by another process: {self.run_dir.name}",
            ) from exc
        self.state = read_state(self.run_dir)
        return self.state

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                write_state(self.run_dir, self.state)
        finally:
            try:
                self.lock.release()
            except Exception:  # noqa: BLE001
                pass


def append_history(
    state: dict[str, Any],
    entry: dict[str, Any],
    *,
    run_dir: Path,
    secrets: list[str] | None = None,
) -> dict[str, Any]:
    """追加一条 history；result 超 10KB 自动落盘到 outputs/ 并打 result_truncated。

    secrets：若提供，则对 result / result_head / 落盘文件内容 做脱敏。
    未传时自动从 state["_secrets_values"] 中读取。
    """
    # 延迟 import 避免循环依赖
    from lib.template import redact_in_obj, redact_secrets

    if secrets is None:
        secrets = state.get("_secrets_values") or []
    if secrets:
        entry = redact_in_obj(entry, secrets)
    result = entry.get("result")
    if isinstance(result, str) and len(result.encode("utf-8")) > LARGE_RESULT_BYTES:
        out_name = f"{uuid.uuid4().hex}.txt"
        outputs_dir = run_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        content_to_write = redact_secrets(result, secrets) if secrets else result
        (outputs_dir / out_name).write_text(content_to_write, encoding="utf-8")
        head = content_to_write[:512]
        entry = {
            **entry,
            "result_truncated": True,
            "result_file": f"outputs/{out_name}",
            "result_size_bytes": len(content_to_write.encode("utf-8")),
            "result_head": head,
        }
        entry.pop("result", None)
    state.setdefault("history", []).append(entry)
    return entry


def _gather_run_dirs(scope: str = "current") -> list[Path]:
    """收集 run 目录。

    scope:
        "current"  — 当前 project_root 下
        "all"      — 当前用户能看到的所有项目（v1：先扫当前 + 父目录）
    """
    roots: list[Path] = []
    here = runs_root()
    if here.exists():
        roots.append(here)
    if scope == "all":
        cur = Path.cwd().resolve()
        for ancestor in [cur, *cur.parents]:
            candidate = ancestor / DEFAULT_RUNS_DIRNAME / RUNS_SUBDIR
            if candidate.exists() and candidate not in roots:
                roots.append(candidate)
    run_dirs: list[Path] = []
    for root in roots:
        for child in root.iterdir():
            if child.is_dir() and (child / "state.json").exists():
                run_dirs.append(child)
    return sorted(run_dirs, key=lambda p: p.stat().st_mtime, reverse=True)


def list_runs(
    *,
    status: list[str] | None = None,
    workflow_name: str | None = None,
    scope: str = "current",
    limit: int = 50,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for run_dir in _gather_run_dirs(scope):
        try:
            state = read_state(run_dir)
        except WorkflowError:
            continue
        if status and state.get("status") not in status:
            continue
        if workflow_name and state.get("workflow_name") != workflow_name:
            continue
        history = state.get("history") or []
        runs.append(
            {
                "run_id": state.get("run_id"),
                "workflow_name": state.get("workflow_name"),
                "status": state.get("status"),
                "caller": state.get("caller"),
                "project_root": state.get("project_root"),
                "created_at": state.get("created_at"),
                "updated_at": state.get("updated_at"),
                "history_count": len(history),
                "last_alias": history[-1].get("alias") if history else None,
            }
        )
        if len(runs) >= limit:
            break
    return runs


_TABLE_COLUMNS: list[tuple[str, str, int]] = [
    ("run_id", "RUN_ID", 28),
    ("workflow_name", "WORKFLOW", 22),
    ("status", "STATUS", 18),
    ("history_count", "STEPS", 5),
    ("last_alias", "LAST", 16),
    ("updated_at", "UPDATED", 20),
]


def _truncate(value: Any, width: int) -> str:
    s = "" if value is None else str(value)
    if len(s) <= width:
        return s.ljust(width)
    return s[: max(width - 1, 1)] + "…"


def render_runs_table(runs: list[dict[str, Any]]) -> str:
    header = "  ".join(name.ljust(width) for _, name, width in _TABLE_COLUMNS)
    sep = "  ".join("-" * width for _, _, width in _TABLE_COLUMNS)
    lines = [header, sep]
    for row in runs:
        line = "  ".join(_truncate(row.get(key), width) for key, _, width in _TABLE_COLUMNS)
        lines.append(line)
    if not runs:
        lines.append("(no runs found)")
    return "\n".join(lines)


def purge_run(run_dir: Path) -> None:
    """删除整个 run 目录（abort 后清理用，v1 暂不开放给 CLI）。"""
    if run_dir.exists():
        shutil.rmtree(run_dir)


def write_state_force(run_dir: Path, state: dict[str, Any]) -> None:
    """绕过 StateTransaction 直写（仅在 create_run 后 / 故障恢复时使用）。"""
    write_state(run_dir, state)


__all__ = [
    "DEFAULT_RUNS_DIRNAME",
    "RUNS_SUBDIR",
    "WORKFLOWS_SUBDIR",
    "LARGE_RESULT_BYTES",
    "StateTransaction",
    "append_history",
    "create_run",
    "detect_project_root",
    "get_run_dir",
    "list_runs",
    "load_workflow_snapshot",
    "read_state",
    "render_runs_table",
    "runs_root",
    "workflows_root",
    "write_state",
    "write_state_force",
]


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps({"runs_root": str(runs_root())}, ensure_ascii=False))
    sys.exit(0)
