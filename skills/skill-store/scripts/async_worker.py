#!/usr/bin/env python3
"""Async background worker: sync repos, rebuild index, check versions."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    load_config, load_status, save_status, ensure_data_dir,
    REPOS_DIR, WORKER_PID_FILE
)
from lib.git_ops import pull, clone, is_git_repo
from lib.version import check_updates, check_orphaned, clean_orphaned


def _write_pid():
    WORKER_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKER_PID_FILE.write_text(str(os.getpid()))


def _remove_pid():
    WORKER_PID_FILE.unlink(missing_ok=True)


def _is_another_worker_running() -> bool:
    if not WORKER_PID_FILE.exists():
        return False
    try:
        pid = int(WORKER_PID_FILE.read_text().strip())
        if pid == os.getpid():
            return False
        os.kill(pid, 0)
        return True
    except (ValueError, OSError, ProcessLookupError):
        WORKER_PID_FILE.unlink(missing_ok=True)
        return False


def _sync_all_repos() -> list[str]:
    config = load_config()
    errors = []

    for reg in config.get("registries", []):
        alias = reg["alias"]
        repo_dir = REPOS_DIR / alias

        try:
            if not repo_dir.exists() or not is_git_repo(repo_dir):
                depth = config.get("settings", {}).get("clone_depth", 1)
                branch = reg.get("branch", "main")
                success, msg = clone(reg["url"], repo_dir, depth=depth, branch=branch)
            else:
                success, msg = pull(repo_dir)

            if not success:
                errors.append(f"{alias}: {msg}")
        except Exception as e:
            errors.append(f"{alias}: {str(e)}")

    return errors


def _rebuild_index_silent():
    from lib.config import load_config, save_index
    from scripts.index import scan_registry

    config = load_config()
    all_skills = []
    for reg in config.get("registries", []):
        skills = scan_registry(reg["alias"], reg.get("skill_paths", ["skills/"]))
        all_skills.extend(skills)

    save_index({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "skills": all_skills
    })


def main():
    if _is_another_worker_running():
        return

    ensure_data_dir()
    _write_pid()

    try:
        sync_errors = _sync_all_repos()
        _rebuild_index_silent()
        pending_updates = check_updates()
        orphaned_skills = check_orphaned()

        if orphaned_skills:
            clean_orphaned()

        status = load_status()
        status["last_sync"] = datetime.now(timezone.utc).isoformat()
        status["sync_in_progress"] = False
        status["pending_updates"] = pending_updates
        status["orphaned_skills"] = orphaned_skills
        status["sync_errors"] = sync_errors
        save_status(status)

    finally:
        _remove_pid()


if __name__ == "__main__":
    main()
