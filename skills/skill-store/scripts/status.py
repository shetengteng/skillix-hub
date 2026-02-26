#!/usr/bin/env python3
"""Status: query installed Skills, pending updates, and sync state."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import load_status, load_installed, output_result
from lib.version import check_updates, check_orphaned


def show_status():
    status = load_status()
    installed = load_installed()

    output_result({
        "last_sync": status.get("last_sync"),
        "sync_in_progress": status.get("sync_in_progress", False),
        "installed_count": len(installed.get("installations", [])),
        "pending_updates": status.get("pending_updates", []),
        "orphaned_skills": status.get("orphaned_skills", []),
        "sync_errors": status.get("sync_errors", [])
    })


def show_updates():
    pending = check_updates()
    orphaned = check_orphaned()

    output_result({
        "pending_updates": pending,
        "orphaned_skills": orphaned
    })


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill Store Status")
    parser.add_argument("action", nargs="?", default="full", choices=["full", "updates"])
    args = parser.parse_args()

    if args.action == "updates":
        show_updates()
    else:
        show_status()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        output_result(error=str(e))
