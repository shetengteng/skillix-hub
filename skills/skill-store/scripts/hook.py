#!/usr/bin/env python3
"""Session hook: display pending updates and trigger async sync."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_status, DATA_DIR, WORKER_PID_FILE, CONFIG_FILE


def _is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_pid() -> int | None:
    if not WORKER_PID_FILE.exists():
        return None
    try:
        pid = int(WORKER_PID_FILE.read_text().strip())
        if _is_process_alive(pid):
            return pid
        WORKER_PID_FILE.unlink(missing_ok=True)
        return None
    except (ValueError, OSError):
        WORKER_PID_FILE.unlink(missing_ok=True)
        return None


def _already_synced_today(status: dict) -> bool:
    last_sync = status.get("last_sync")
    if not last_sync:
        return False
    try:
        last_dt = datetime.fromisoformat(last_sync)
        today = datetime.now(timezone.utc).date()
        return last_dt.date() == today
    except (ValueError, TypeError):
        return False


def _display_status(status: dict):
    messages = []

    pending = status.get("pending_updates", [])
    if pending:
        lines = ["[skill-store] Skill updates available:"]
        for p in pending:
            short_old = p.get("installed_commit", "?")[:7]
            short_new = p.get("latest_commit", "?")[:7]
            scope = p.get("scope", "global")
            lines.append(f"  - {p['name']} ({scope}): {short_old} → {short_new}")
        lines.append('Say "update all skills" or "update <name>" to update.')
        messages.append("\n".join(lines))

    orphaned = status.get("orphaned_skills", [])
    if orphaned:
        lines = ["[skill-store] Deleted skills detected:"]
        for o in orphaned:
            lines.append(f"  - {o['name']} ({o.get('scope', 'global')}): {o['target_path']}")
        lines.append("These were manually deleted. Records will be cleaned automatically.")
        messages.append("\n".join(lines))

    errors = status.get("sync_errors", [])
    if errors:
        lines = ["[skill-store] Sync errors:"]
        for e in errors:
            lines.append(f"  - {e}")
        messages.append("\n".join(lines))

    if messages:
        print("\n\n".join(messages))


def _start_async_worker():
    worker_script = Path(__file__).parent / "async_worker.py"
    if not worker_script.exists():
        return

    subprocess.Popen(
        [sys.executable, str(worker_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )


def main():
    if not CONFIG_FILE.exists():
        return

    status = load_status()

    _display_status(status)

    if _already_synced_today(status):
        return

    if _read_pid() is not None:
        return

    _start_async_worker()


if __name__ == "__main__":
    main()
