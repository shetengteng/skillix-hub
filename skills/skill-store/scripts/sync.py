#!/usr/bin/env python3
"""Sync: clone or pull Git repositories."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    load_config, save_config, ensure_data_dir, output_result, REPOS_DIR
)
from lib.git_ops import clone, pull, is_git_repo


def sync_one(alias: str) -> dict:
    config = load_config()
    registry = None
    for reg in config["registries"]:
        if reg["alias"] == alias:
            registry = reg
            break

    if not registry:
        return {"alias": alias, "success": False, "message": f"Registry '{alias}' not found."}

    repo_dir = REPOS_DIR / alias

    if not repo_dir.exists() or not is_git_repo(repo_dir):
        depth = config.get("settings", {}).get("clone_depth", 1)
        branch = registry.get("branch", "main")
        success, msg = clone(registry["url"], repo_dir, depth=depth, branch=branch)
    else:
        success, msg = pull(repo_dir)

    if success:
        registry["last_synced"] = datetime.now(timezone.utc).isoformat()
        save_config(config)

    return {"alias": alias, "success": success, "message": msg}


def sync_all():
    ensure_data_dir()
    config = load_config()
    registries = config.get("registries", [])

    if not registries:
        output_result({"synced": 0, "results": [], "message": "No registries configured."})
        return

    results = []
    for reg in registries:
        result = sync_one(reg["alias"])
        results.append(result)

    succeeded = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])

    output_result({
        "synced": succeeded,
        "failed": failed,
        "results": results
    })


def main():
    parser = argparse.ArgumentParser(description="Skill Store Sync")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("all")

    one_p = sub.add_parser("one")
    one_p.add_argument("--alias", required=True)

    args = parser.parse_args()

    if args.action == "all":
        sync_all()
    elif args.action == "one":
        result = sync_one(args.alias)
        output_result(result)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        output_result(error=str(e))
