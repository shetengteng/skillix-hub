"""4 级校验 + UUID 主键分配 + validate 命令入口。

L1 YAML 语法（PyYAML）
L2 JSON Schema 校验（jsonschema, draft-2020-12）
L3 引用/数据流分析（同层 alias 唯一 / output 唯一 / 模板引用可达性）
L4 executor PATH 检测（shutil.which）
"""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from lib.errors import ErrorCode, WorkflowError
from lib.template import VAR_PATTERN

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "workflow.schema.json"

# v1 内置 executor 名（caller 永远存在；claude/codex 需检查 PATH）
BUILTIN_EXECUTORS: dict[str, str | None] = {
    "caller": None,
    "claude": "claude",
    "codex": "codex",
}


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text("utf-8"))


def parse_yaml(text: str) -> Any:
    """L1：YAML → dict；失败抛 WorkflowError(YAML_PARSE_ERROR)。"""
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location: dict[str, int] = {}
        if mark is not None:
            location = {"line": mark.line + 1, "column": mark.column + 1}
        problem = getattr(exc, "problem", None) or str(exc)
        raise WorkflowError(
            ErrorCode.YAML_PARSE_ERROR,
            f"YAML parse error: {problem}",
            location=location or None,
        ) from exc


def load_workflow(raw: str | dict[str, Any]) -> dict[str, Any]:
    """统一入口：支持 dict / 文件路径 / workflow name / 内联 YAML 字符串。

    解析优先级：
        1. dict → 直接返回
        2. 路径字符串（含 / 或 .yaml/.yml 后缀）→ 按路径加载
        3. 短字符串（无换行、无 / 、无 .yaml）→ 尝试按 name 从全局目录查找
        4. 多行字符串 → 当作内联 YAML 解析
    """
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise WorkflowError(
            ErrorCode.PARAMS_INVALID, "workflow must be dict or string"
        )

    looks_like_path = (
        ("\n" not in raw)
        and (raw.endswith(".yaml") or raw.endswith(".yml") or "/" in raw)
    )

    if looks_like_path:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"workflow file not found: {path}",
                location={"path": str(path)},
            )
        text = path.read_text("utf-8")
    elif "\n" not in raw and not raw.strip().startswith("{"):
        from lib.store import resolve_workflow_by_name
        resolved = resolve_workflow_by_name(raw.strip())
        if resolved is not None:
            text = resolved.read_text("utf-8")
        else:
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"workflow not found by name: {raw!r}. Use 'flows' to list available workflows.",
                suggestion="agent-workflow flows '{}'",
            )
    else:
        text = raw

    data = parse_yaml(text)
    if not isinstance(data, dict):
        raise WorkflowError(
            ErrorCode.WORKFLOW_INVALID,
            "workflow root must be a mapping/object",
        )
    return data


def _violation_code(err) -> tuple[str, str | None]:
    """从 jsonschema error 推断业务错误码 + 缺失字段名（若可识别）。"""
    if err.validator == "required":
        tokens = err.message.split("'")
        if len(tokens) >= 2:
            field = tokens[1]
            if field == "output":
                return ErrorCode.NODE_OUTPUT_REQUIRED, field
            return ErrorCode.SCHEMA_VIOLATION, field
    if err.validator in ("oneOf", "anyOf"):
        for sub in err.context or []:
            code, field = _violation_code(sub)
            if code == ErrorCode.NODE_OUTPUT_REQUIRED:
                return code, field
    return ErrorCode.SCHEMA_VIOLATION, None


def _validate_schema(data: dict[str, Any]) -> list[dict[str, Any]]:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    violations: list[dict[str, Any]] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = "$." + ".".join(str(p) for p in err.absolute_path) if err.absolute_path else "$"
        code, missing_field = _violation_code(err)
        message = err.message
        if code == ErrorCode.NODE_OUTPUT_REQUIRED:
            message = f"agent_call node missing required field 'output' at {path}"
        violations.append(
            {
                "level": "L2",
                "code": code,
                "message": message,
                "location": {"path": path},
            }
        )
    return violations


def _collect_template_refs(value: Any) -> set[str]:
    """从模板字符串中提取 {{a.b.c}} 引用的首段。"""
    if not isinstance(value, str):
        return set()
    return {m.group(1).split(".")[0] for m in VAR_PATTERN.finditer(value)}


def _collect_producible_vars(nodes: list[dict[str, Any]]) -> set[str]:
    """收集这串 nodes（含 loop 嵌套）会写入 vars 的所有 key。"""
    out: set[str] = set()
    for node in nodes:
        ntype = node.get("type")
        if ntype == "agent_call" and node.get("output"):
            out.add(node["output"])
        elif ntype == "wait_user":
            key = node.get("output") or node.get("alias")
            if key:
                out.add(key)
        elif ntype == "loop":
            out |= _collect_producible_vars(node.get("body") or [])
    return out


def _validate_references(data: dict[str, Any]) -> list[dict[str, Any]]:
    initial_vars = set((data.get("vars") or {}).keys())
    violations: list[dict[str, Any]] = []

    def walk(nodes: list[dict[str, Any]], parent_scope: set[str], path_prefix: str) -> None:
        aliases_in_scope: set[str] = set()
        visible: set[str] = set(initial_vars) | set(parent_scope)
        for idx, node in enumerate(nodes):
            ntype = node.get("type")
            alias = node.get("alias")
            output = node.get("output")
            loc = f"{path_prefix}[{idx}]" + (f".{alias}" if alias else "")

            if alias and alias in aliases_in_scope:
                violations.append(
                    {
                        "level": "L3",
                        "code": ErrorCode.WORKFLOW_INVALID,
                        "message": f"duplicate alias {alias!r} in same scope",
                        "location": {"path": loc, "alias": alias},
                    }
                )
            if alias:
                aliases_in_scope.add(alias)

            template_fields: list[tuple[str, Any]] = []
            template_visible = visible
            if ntype == "agent_call":
                template_fields.append(("prompt", node.get("prompt")))
            elif ntype == "loop":
                # condition / max_iterations 评估时刻在 body 执行之后，
                # 所以 body 会产生的变量也算可见。
                template_visible = visible | _collect_producible_vars(node.get("body") or [])
                template_fields.append(("condition", node.get("condition")))
                mi = node.get("max_iterations")
                if isinstance(mi, str):
                    template_fields.append(("max_iterations", mi))
            elif ntype == "sleep":
                seconds = node.get("seconds")
                if isinstance(seconds, str):
                    template_fields.append(("seconds", seconds))

            for fname, tmpl in template_fields:
                for ref in _collect_template_refs(tmpl):
                    if ref not in template_visible:
                        violations.append(
                            {
                                "level": "L3",
                                "code": ErrorCode.VAR_NOT_IN_SCOPE,
                                "message": f"reference {{{{{ref}.*}}}} not in scope (field={fname})",
                                "location": {
                                    "path": loc,
                                    "field": fname,
                                    "ref": ref,
                                },
                                "suggestion": (
                                    f"declare {ref!r} as workflow.vars, "
                                    "or move a producer node before this one"
                                ),
                            }
                        )

            if ntype == "agent_call" and output:
                visible.add(output)
            if ntype == "wait_user":
                key = node.get("output") or alias
                if key:
                    visible.add(key)
            if ntype == "loop":
                child_scope = set(visible)
                if alias:
                    child_scope.add(alias)
                walk(node.get("body") or [], child_scope, f"{loc}.body")
                # body 中产生的 var 在 loop 退出后对后续节点可见
                visible |= _collect_producible_vars(node.get("body") or [])

    walk(data.get("nodes") or [], parent_scope=set(), path_prefix="$.nodes")
    return violations


def _collect_executors_used(data: dict[str, Any]) -> set[str]:
    used: set[str] = set()

    def walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            if node.get("type") == "agent_call":
                used.add(node.get("executor") or "caller")
            elif node.get("type") == "loop":
                walk(node.get("body") or [])

    walk(data.get("nodes") or [])
    return used


def _validate_executors(
    data: dict[str, Any], *, allow_missing: bool
) -> list[dict[str, Any]]:
    if allow_missing:
        return []
    # 延迟 import 避免循环依赖
    from lib.executors.registry import resolve_specs

    custom = data.get("executors") or {}
    specs = resolve_specs(custom)
    used = _collect_executors_used(data)
    violations: list[dict[str, Any]] = []
    for name in sorted(used):
        if name == "caller":
            continue
        spec = specs.get(name)
        if spec is None:
            violations.append(
                {
                    "level": "L4",
                    "code": ErrorCode.EXECUTOR_NOT_FOUND,
                    "message": f"executor {name!r} is not registered",
                    "location": {"executor": name},
                    "suggestion": (
                        "declare it under workflow.executors or ~/.agent-workflow/config.yaml"
                    ),
                }
            )
            continue
        kind = spec.get("kind", "spawn")
        if kind in ("caller", "mock"):
            continue
        cmd_list = spec.get("cmd") or []
        cmd = cmd_list[0] if cmd_list else name
        if shutil.which(cmd) is None:
            violations.append(
                {
                    "level": "L4",
                    "code": ErrorCode.EXECUTOR_NOT_FOUND,
                    "message": f"executor {name!r} not found in PATH (cmd={cmd!r})",
                    "location": {"executor": name, "cmd": cmd},
                    "suggestion": (
                        f"install {cmd!r} or pass allow_missing_executors=true to defer the check"
                    ),
                }
            )
    return violations


def _count_nodes(data: dict[str, Any]) -> int:
    total = 0

    def walk(nodes: list[dict[str, Any]]) -> None:
        nonlocal total
        for node in nodes:
            total += 1
            if node.get("type") == "loop":
                walk(node.get("body") or [])

    walk(data.get("nodes") or [])
    return total


def assign_internal_ids(data: dict[str, Any]) -> dict[str, Any]:
    """给每个节点写 `_internal_id`（8 字符 hex UUID）；已有则保留。"""

    def walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            if "_internal_id" not in node:
                node["_internal_id"] = uuid.uuid4().hex[:8]
            if node.get("type") == "loop":
                walk(node.get("body") or [])

    walk(data.get("nodes") or [])
    return data


def validate_action(params: dict[str, Any]) -> dict[str, Any]:
    """validate 命令入口。

    入参（与 SKILL.md 对齐）：
        workflow                : str | dict — 路径 / 内联 YAML / 已解析对象
        levels                  : list[str]  — 默认 ["L1","L2","L3","L4"]
        allow_missing_executors : bool       — 跳过 L4，默认 False
    """
    raw = params.get("workflow")
    if raw is None:
        raise WorkflowError(ErrorCode.PARAMS_INVALID, "workflow is required")
    levels = params.get("levels") or ["L1", "L2", "L3", "L4"]
    allow_missing = bool(params.get("allow_missing_executors", False))

    data = load_workflow(raw)

    violations: list[dict[str, Any]] = []
    levels_checked: list[str] = ["L1"]

    if "L2" in levels:
        violations.extend(_validate_schema(data))
        levels_checked.append("L2")

    if "L3" in levels and not violations:
        violations.extend(_validate_references(data))
        levels_checked.append("L3")

    if "L4" in levels and not violations:
        violations.extend(_validate_executors(data, allow_missing=allow_missing))
        levels_checked.append("L4")

    executors_used = sorted(_collect_executors_used(data))
    summary = {
        "name": data.get("name", "<unknown>"),
        "node_count": _count_nodes(data),
        "executors_used": executors_used,
        "levels_checked": levels_checked,
    }

    if violations:
        raise WorkflowError(
            ErrorCode.WORKFLOW_INVALID,
            f"workflow validation failed ({len(violations)} violation(s))",
            violations=violations,
            summary=summary,
        )

    return {"summary": summary, "violations": []}
