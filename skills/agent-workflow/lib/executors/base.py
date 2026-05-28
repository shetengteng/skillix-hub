"""Executor 基类 + subprocess 实现 + stall watchdog。

执行结果统一封装为 ExecutionOutcome：
    - kind="completed"     output（str），节点产出可直接写 vars
    - kind="needs_caller"  payload（dict），engine 将其原样回传给 caller agent
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lib.errors import ErrorCode, WorkflowError

STDOUT_DECODE_ERRORS = "replace"
STDERR_TAIL_MAX = 2048


@dataclass
class ExecutionOutcome:
    kind: str
    output: str | None = None
    payload: dict[str, Any] | None = None
    duration_ms: int = 0
    stdout_size: int = 0
    stderr_tail: str | None = None
    exit_code: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class BaseExecutor:
    """所有 executor 的基类。子类至少实现 `.execute()`。"""

    name: str = "base"

    def __init__(self, name: str, **opts: Any) -> None:
        self.name = name
        self.opts = opts

    def execute(
        self,
        *,
        prompt: str,
        node: dict[str, Any],
        vars_: dict[str, Any],
        run_context: dict[str, Any],
        agent: dict[str, Any] | None = None,
    ) -> ExecutionOutcome:  # pragma: no cover - abstract
        raise NotImplementedError(f"executor {self.name!r} must implement execute()")


def _read_stream(stream, sink: list[bytes], activity: dict[str, float]) -> None:
    while True:
        chunk = stream.read(1024)
        if not chunk:
            break
        sink.append(chunk)
        activity["last"] = time.monotonic()
    try:
        stream.close()
    except Exception:  # noqa: BLE001
        pass


def _resolve_context_files(prompt: str, context_files: list[str] | None, cwd: Path) -> str:
    if not context_files:
        return prompt
    blocks: list[str] = []
    for raw in context_files:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = cwd / path
        if not path.exists():
            blocks.append(f"<context file missing: {raw}>")
            continue
        try:
            text = path.read_text("utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            blocks.append(f"<failed to read {raw}: {exc}>")
            continue
        blocks.append(f"=== {raw} ===\n{text}")
    return "\n\n".join([*blocks, prompt]) if blocks else prompt


def _apply_agent_prefix(prompt: str, agent: dict[str, Any] | None) -> str:
    """SpawnExecutor 专用：把 agent.role + agent.skills 拼成 system prompt 前缀。

    输出格式（segment 之间空行分隔）：
        === Role ===
        <role 文本>

        === Skills (advisory) ===
        - skill_a
        - skill_b

        === Task ===
        <原 prompt>

    role/skills 都没有 → 直接返回原 prompt。
    skills 为空列表 → 跳过该段，仅拼 role。
    """
    if not agent:
        return prompt
    parts: list[str] = []
    role = agent.get("role")
    if isinstance(role, str) and role.strip():
        parts.append(f"=== Role ===\n{role.strip()}")
    skills = agent.get("skills") or []
    if isinstance(skills, list) and skills:
        joined = "\n".join(f"- {s}" for s in skills if isinstance(s, str) and s)
        if joined:
            parts.append(f"=== Skills (advisory) ===\n{joined}")
    if not parts:
        return prompt
    parts.append(f"=== Task ===\n{prompt}")
    return "\n\n".join(parts)


def _terminate_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
    except (ProcessLookupError, OSError):
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, OSError):
            pass


class SpawnExecutor(BaseExecutor):
    """通用 subprocess executor — 用于 claude / codex / opencode / custom。"""

    def __init__(
        self,
        name: str,
        *,
        cmd: list[str],
        input_mode: str = "stdin",
        output_parser: str = "text",
        stall_timeout_ms: int = 300_000,
        total_timeout_ms: int = 600_000,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        super().__init__(name)
        if not cmd:
            raise WorkflowError(
                ErrorCode.EXECUTOR_NOT_FOUND,
                f"executor {name!r} has empty cmd",
            )
        if input_mode not in ("stdin", "arg"):
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"executor {name!r}: input_mode must be stdin|arg, got {input_mode!r}",
            )
        if output_parser not in ("text", "json"):
            raise WorkflowError(
                ErrorCode.PARAMS_INVALID,
                f"executor {name!r}: output_parser must be text|json, got {output_parser!r}",
            )
        self.cmd = cmd
        self.input_mode = input_mode
        self.output_parser = output_parser
        self.stall_timeout_ms = max(int(stall_timeout_ms), 1000)
        self.total_timeout_ms = max(int(total_timeout_ms), 1000)
        self.env = env
        self.cwd = cwd

    def execute(
        self,
        *,
        prompt: str,
        node: dict[str, Any],
        vars_: dict[str, Any],
        run_context: dict[str, Any],
        agent: dict[str, Any] | None = None,
    ) -> ExecutionOutcome:
        cwd = self.cwd or Path(run_context.get("project_root") or Path.cwd())
        full_prompt = _resolve_context_files(prompt, node.get("context_files"), cwd)
        full_prompt = _apply_agent_prefix(full_prompt, agent)
        cmd = list(self.cmd)
        stdin_bytes: bytes | None = None
        if self.input_mode == "stdin":
            stdin_bytes = full_prompt.encode("utf-8")
        else:
            cmd.append(full_prompt)

        node_timeout = node.get("timeout")
        total_timeout_ms = (
            int(node_timeout) * 1000 if isinstance(node_timeout, (int, float)) else self.total_timeout_ms
        )

        start = time.monotonic()
        env = os.environ.copy()
        if self.env:
            env.update(self.env)

        try:
            proc = subprocess.Popen(  # noqa: S603 - cmd 来自校验过的配置
                cmd,
                stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(cwd),
                start_new_session=(os.name == "posix"),
            )
        except FileNotFoundError as exc:
            raise WorkflowError(
                ErrorCode.EXECUTOR_NOT_FOUND,
                f"executor {self.name!r} not found: {cmd[0]}",
                location={"executor": self.name, "cmd": cmd[0]},
            ) from exc

        if stdin_bytes is not None and proc.stdin is not None:
            try:
                proc.stdin.write(stdin_bytes)
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []
        activity = {"last": time.monotonic()}

        t_out = threading.Thread(
            target=_read_stream,
            args=(proc.stdout, stdout_chunks, activity),
            daemon=True,
            name=f"{self.name}-stdout",
        )
        t_err = threading.Thread(
            target=_read_stream,
            args=(proc.stderr, stderr_chunks, activity),
            daemon=True,
            name=f"{self.name}-stderr",
        )
        t_out.start()
        t_err.start()

        stalled = False
        timed_out = False
        while True:
            if proc.poll() is not None:
                break
            now = time.monotonic()
            elapsed_ms = (now - start) * 1000
            stall_ms = (now - activity["last"]) * 1000
            if elapsed_ms > total_timeout_ms:
                timed_out = True
                _terminate_process(proc)
                break
            if stall_ms > self.stall_timeout_ms:
                stalled = True
                _terminate_process(proc)
                break
            time.sleep(0.25)

        t_out.join(timeout=2)
        t_err.join(timeout=2)

        stdout = b"".join(stdout_chunks).decode("utf-8", STDOUT_DECODE_ERRORS)
        stderr = b"".join(stderr_chunks).decode("utf-8", STDOUT_DECODE_ERRORS)
        duration_ms = int((time.monotonic() - start) * 1000)
        exit_code = proc.returncode if proc.returncode is not None else -1
        stderr_tail = stderr[-STDERR_TAIL_MAX:]

        if stalled:
            raise WorkflowError(
                ErrorCode.EXECUTOR_STALLED,
                f"executor {self.name!r} produced no stdout for {self.stall_timeout_ms}ms",
                location={"executor": self.name, "cmd": cmd[0]},
                stderr_tail=stderr_tail,
                duration_ms=duration_ms,
            )
        if timed_out:
            raise WorkflowError(
                ErrorCode.NODE_TIMEOUT,
                f"executor {self.name!r} exceeded total_timeout={total_timeout_ms}ms",
                location={"executor": self.name, "cmd": cmd[0]},
                stderr_tail=stderr_tail,
                duration_ms=duration_ms,
            )
        if exit_code != 0:
            raise WorkflowError(
                ErrorCode.EXECUTOR_NONZERO_EXIT,
                f"executor {self.name!r} exited with code {exit_code}",
                location={"executor": self.name, "cmd": cmd[0], "exit_code": exit_code},
                stderr_tail=stderr_tail,
                duration_ms=duration_ms,
            )

        text = stdout.strip()
        if not text:
            raise WorkflowError(
                ErrorCode.NODE_EMPTY_OUTPUT,
                f"executor {self.name!r} produced empty stdout",
                location={"executor": self.name},
                stderr_tail=stderr_tail,
                duration_ms=duration_ms,
            )
        output: str
        if self.output_parser == "json":
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise WorkflowError(
                    ErrorCode.NODE_EMPTY_OUTPUT,
                    f"executor {self.name!r} stdout is not valid JSON: {exc.msg}",
                    location={"executor": self.name},
                    stderr_tail=stderr_tail,
                ) from exc
            output = json.dumps(parsed, ensure_ascii=False)
        else:
            output = text

        return ExecutionOutcome(
            kind="completed",
            output=output,
            duration_ms=duration_ms,
            stdout_size=len(stdout.encode("utf-8")),
            stderr_tail=stderr_tail if stderr_tail else None,
            exit_code=exit_code,
            extra={"executor": self.name, "cmd": cmd[0]},
        )
