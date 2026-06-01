"""create 命令实现：list_templates / from_template / scaffold。

template_action 支持以下子动作（与 SKILL.md 对齐）：

    {"action": "list_templates"}
        → {"templates": [{"name": "...", "description": "...", "node_count": N}]}

    {"action": "from_template", "template": "<name>", "out": "<path>", "overwrite": false}
        → 拷贝模板到 out 路径，返回 {"path": "<absolute>"}

    {"action": "scaffold", "name": "<workflow_name>", "out": "<path>",
     "nodes": [{"type":"agent_call","alias":"...","prompt":"...","output":"..."}]}
        → 生成最小骨架；自动加 description 占位。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lib.errors import ErrorCode, WorkflowError
from lib.parser import load_workflow, validate_action
from lib.store import workflows_root

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"


def _list_templates() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not TEMPLATES_DIR.exists():
        return out
    for path in sorted(TEMPLATES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text("utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        out.append(
            {
                "name": data.get("name") or path.stem,
                "file": path.name,
                "description": (data.get("description") or "").strip().split("\n")[0],
                "node_count": _count_nodes(data.get("nodes") or []),
            }
        )
    return out


def _count_nodes(nodes: list[dict[str, Any]]) -> int:
    total = 0
    for node in nodes:
        total += 1
        if node.get("type") == "loop":
            total += _count_nodes(node.get("body") or [])
    return total


def _resolve_out(out: str) -> Path:
    path = Path(out).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _from_template(params: dict[str, Any]) -> dict[str, Any]:
    template = params.get("template")
    if not template:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "template is required for from_template")
    candidates = list(TEMPLATES_DIR.glob(f"{template}.yaml")) + list(
        TEMPLATES_DIR.glob(f"{template}*.yaml")
    )
    if not candidates:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"template not found: {template}",
            location={"template": template, "templates_dir": str(TEMPLATES_DIR)},
        )
    src = candidates[0]
    default_out = str(workflows_root() / src.name)
    out_path = _resolve_out(params.get("out") or default_out)
    overwrite = bool(params.get("overwrite", False))
    if out_path.exists() and not overwrite:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"output path already exists; pass overwrite=true to replace: {out_path}",
            location={"path": str(out_path)},
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(src.read_text("utf-8"), encoding="utf-8")
    validate_action({"workflow": str(out_path), "allow_missing_executors": True})
    return {"path": str(out_path), "template": src.stem}


def _scaffold(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    if not name:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "name is required for scaffold")
    raw_nodes = params.get("nodes") or []
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "nodes must be a non-empty list")
    cleaned_nodes: list[dict[str, Any]] = []
    for idx, node in enumerate(raw_nodes):
        if not isinstance(node, dict):
            raise WorkflowError(ErrorCode.PARAMS_INVALID, f"nodes[{idx}] must be an object")
        ntype = node.get("type")
        if ntype not in ("agent_call", "wait_user", "loop", "sleep"):
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"nodes[{idx}].type must be one of agent_call/wait_user/loop/sleep",
            )
        cleaned_nodes.append(node)
    workflow: dict[str, Any] = {
        "name": name,
        "description": params.get("description") or f"scaffolded workflow {name}",
        "vars": params.get("vars") or {},
        "nodes": cleaned_nodes,
    }
    default_out = str(workflows_root() / f"{name}.yaml")
    out_path = _resolve_out(params.get("out") or default_out)
    overwrite = bool(params.get("overwrite", False))
    if out_path.exists() and not overwrite:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            f"output path already exists; pass overwrite=true to replace: {out_path}",
            location={"path": str(out_path)},
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(workflow, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    validate_action({"workflow": str(out_path), "allow_missing_executors": True})
    return {"path": str(out_path), "name": name, "node_count": _count_nodes(cleaned_nodes)}


def create_action(params: dict[str, Any]) -> dict[str, Any]:
    action = (params.get("action") or "").strip()
    if not action:
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID,
            "create requires an action: list_templates | from_template | scaffold",
        )
    if action == "list_templates":
        return {"templates": _list_templates(), "templates_dir": str(TEMPLATES_DIR)}
    if action == "from_template":
        return _from_template(params)
    if action == "scaffold":
        return _scaffold(params)
    raise WorkflowError(
        ErrorCode.PARAMS_INVALID,
        f"unknown create action: {action!r}",
        suggestion="use one of: list_templates | from_template | scaffold",
    )
