"""events.ndjson 与 audit.log 的最小写入工具。

写入位置：
    <runs_root>/<run_id>/events.ndjson   # append-only ND-JSON 事件流
    <runs_root>/<run_id>/audit.log       # 一行一条 audit（可读）

对外协议（与设计文档 §4.16 对齐）：
    write_event(run_dir, type, **fields)
    write_audit(run_dir, action, **fields)
"""
from __future__ import annotations

import contextvars
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 当前 chain 上下文中的 secret 值。engine._chain 入口通过 set_run_secrets() 设置。
_SECRETS_CTX: contextvars.ContextVar[list[str]] = contextvars.ContextVar("agent_workflow_secrets", default=[])


def set_run_secrets(secrets: list[str] | None) -> None:
    """供 engine 在进入 _chain 时调用，设置当前线程的 secret 列表。"""
    _SECRETS_CTX.set(list(secrets) if secrets else [])


def get_run_secrets() -> list[str]:
    return list(_SECRETS_CTX.get())


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_iso_ms() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


def _append(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def write_event(
    run_dir: Path | str,
    event_type: str,
    *,
    secrets: list[str] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """向 events.ndjson 追加一行事件。

    支持的 event_type（设计文档 §4.16）：
        run_start / node_start / spawn / sleep_start / sleep_end
        node_end / error / pause / resume / run_end / abort

    secrets：若提供则递归对 fields 做脱敏（仅落盘，不影响内存）。
    """
    run_dir_path = Path(run_dir)
    event: dict[str, Any] = {"ts": _utc_iso(), "type": event_type}
    effective_secrets = secrets if secrets is not None else _SECRETS_CTX.get()
    redact = _make_redactor(effective_secrets)
    for key, value in fields.items():
        if value is None:
            continue
        if key in ("ts", "type"):
            continue
        event[key] = redact(value)
    line = json.dumps(event, ensure_ascii=False, sort_keys=False) + "\n"
    _append(run_dir_path / "events.ndjson", line)
    return event


def write_audit(
    run_dir: Path | str,
    action: str,
    *,
    secrets: list[str] | None = None,
    **fields: Any,
) -> None:
    """audit.log 一行：`<ts>  <action>  k=v k=v ...`，仅供人读。

    secrets：若提供则对所有字段做脱敏，再 json 序列化。
    """
    run_dir_path = Path(run_dir)
    parts = [_utc_iso_ms(), action]
    effective_secrets = secrets if secrets is not None else _SECRETS_CTX.get()
    redact = _make_redactor(effective_secrets)
    for key, value in fields.items():
        if value is None:
            continue
        masked = redact(value)
        if isinstance(masked, str):
            v = masked.replace("\n", "\\n").replace("\r", "")
        else:
            v = json.dumps(masked, ensure_ascii=False, separators=(",", ":"))
        parts.append(f"{key}={v}")
    _append(run_dir_path / "audit.log", "  ".join(parts) + "\n")


def _make_redactor(secrets: list[str] | None):
    """生成一个对 str/list/dict 递归脱敏的函数。避免对 logger 引入循环 import。"""
    if not secrets:
        return lambda v: v
    mask = "***REDACTED***"

    def _redact(value: Any) -> Any:
        if isinstance(value, str):
            out = value
            for sv in secrets:
                if isinstance(sv, str) and sv:
                    out = out.replace(sv, mask)
            return out
        if isinstance(value, list):
            return [_redact(v) for v in value]
        if isinstance(value, dict):
            return {k: _redact(v) for k, v in value.items()}
        return value

    return _redact


def read_events(run_dir: Path | str, limit: int | None = None) -> list[dict[str, Any]]:
    """读取 events.ndjson 全部或最近 N 条事件（status 命令用）。"""
    path = Path(run_dir) / "events.ndjson"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit is not None and len(events) > limit:
        return events[-limit:]
    return events
