"""wait_user 节点：渲染 message → 构造 payload；resume 时按 schema 校验输入。"""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from lib.errors import ErrorCode, WorkflowError
from lib.template import render


def build_payload(node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    message = render(
        node.get("message") or "",
        state.get("vars") or {},
        strict_vars=False,
    )
    return {
        "message": message,
        "alias": node.get("alias"),
        "internal_id": node.get("_internal_id"),
        "node_description": node.get("description") or "",
        "schema": node.get("schema") or {"type": "object"},
        "output_alias": node.get("output") or node.get("alias"),
    }


def _apply_defaults(schema: dict[str, Any], user_input: dict[str, Any]) -> dict[str, Any]:
    merged = dict(user_input or {})
    for field_name, field_spec in (schema.get("properties") or {}).items():
        if field_name not in merged and isinstance(field_spec, dict) and "default" in field_spec:
            merged[field_name] = field_spec["default"]
    return merged


def validate_user_input(
    node: dict[str, Any],
    user_input: Any,
) -> dict[str, Any]:
    schema = node.get("schema") or {"type": "object"}
    if not isinstance(user_input, dict):
        raise WorkflowError(
            ErrorCode.SCHEMA_VIOLATION,
            "wait_user input must be a JSON object",
            location={"alias": node.get("alias")},
        )
    merged = _apply_defaults(schema, user_input)
    if schema.get("type") == "object" and schema.get("properties"):
        schema = {**schema, "additionalProperties": schema.get("additionalProperties", False)}
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(merged))
    if errors:
        first = errors[0]
        raise WorkflowError(
            ErrorCode.SCHEMA_VIOLATION,
            f"wait_user input does not match schema: {first.message}",
            location={
                "alias": node.get("alias"),
                "path": list(first.absolute_path),
            },
            violations=[
                {
                    "path": "$." + ".".join(str(p) for p in err.absolute_path)
                    if err.absolute_path
                    else "$",
                    "message": err.message,
                }
                for err in errors
            ],
        )
    return merged
