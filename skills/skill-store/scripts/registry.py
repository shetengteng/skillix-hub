#!/usr/bin/env python3
"""Registry management: add, list, remove Git repository sources."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    load_config, save_config, load_index, save_index,
    ensure_data_dir, output_result, REPOS_DIR
)
from lib.git_ops import clone, is_git_repo, pull


def _auto_sync(config: dict) -> dict:
    results = []
    for reg in config.get("registries", []):
        repo_dir = REPOS_DIR / reg["alias"]
        if repo_dir.exists():
            success, msg = pull(repo_dir)
        else:
            success, msg = clone(reg["url"], repo_dir,
                                 depth=config.get("settings", {}).get("clone_depth", 1),
                                 branch=reg.get("branch", "main"))
        if success:
            reg["last_synced"] = datetime.now(timezone.utc).isoformat()
        results.append({"alias": reg["alias"], "success": success})
    save_config(config)
    return {"synced": sum(1 for r in results if r["success"]), "total": len(results)}


def _auto_rebuild_index() -> dict:
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
    return {"total_skills": len(all_skills)}


def add_registry(url: str, alias: str | None = None, branch: str = "main",
                 skill_paths: list[str] | None = None, clone_depth: int = 1):
    ensure_data_dir()
    config = load_config()

    if not alias:
        alias = url.rstrip("/").split("/")[-1].replace(".git", "")

    for reg in config["registries"]:
        if reg["alias"] == alias:
            output_result(error=f"Registry '{alias}' already exists. Use a different alias.")
            return
        if reg["url"] == url:
            output_result(error=f"URL '{url}' already registered as '{reg['alias']}'.")
            return

    repo_dir = REPOS_DIR / alias
    if repo_dir.exists() and is_git_repo(repo_dir):
        output_result(error=f"Directory {repo_dir} already exists.")
        return

    success, msg = clone(url, repo_dir, depth=clone_depth, branch=branch)
    if not success:
        output_result(error=f"Clone failed: {msg}")
        return

    registry = {
        "url": url,
        "alias": alias,
        "branch": branch,
        "skill_paths": skill_paths or ["skills/"],
        "added_at": datetime.now(timezone.utc).isoformat(),
        "last_synced": datetime.now(timezone.utc).isoformat()
    }
    config["registries"].append(registry)
    save_config(config)

    sync_result = _auto_sync(config)
    index_result = _auto_rebuild_index()

    output_result({
        "action": "added",
        "alias": alias,
        "url": url,
        "repo_dir": str(repo_dir),
        "sync": sync_result,
        "index": index_result
    })


def list_registries():
    config = load_config()
    registries = config.get("registries", [])
    output_result({
        "count": len(registries),
        "registries": registries
    })


def remove_registry(alias: str, keep_repo: bool = False):
    config = load_config()
    found = None
    for i, reg in enumerate(config["registries"]):
        if reg["alias"] == alias:
            found = i
            break

    if found is None:
        output_result(error=f"Registry '{alias}' not found.")
        return

    removed = config["registries"].pop(found)
    save_config(config)

    repo_dir = REPOS_DIR / alias
    if not keep_repo and repo_dir.exists():
        import shutil
        shutil.rmtree(repo_dir, ignore_errors=True)

    output_result({
        "action": "removed",
        "alias": alias,
        "url": removed["url"],
        "repo_deleted": not keep_repo and not repo_dir.exists()
    })


def main():
    parser = argparse.ArgumentParser(description="Skill Store Registry Management")
    sub = parser.add_subparsers(dest="action", required=True)

    add_p = sub.add_parser("add")
    add_p.add_argument("--url", required=True)
    add_p.add_argument("--alias")
    add_p.add_argument("--branch", default="main")
    add_p.add_argument("--skill-paths", nargs="+", default=None)
    add_p.add_argument("--clone-depth", type=int, default=1)

    sub.add_parser("list")

    rm_p = sub.add_parser("remove")
    rm_p.add_argument("--alias", required=True)
    rm_p.add_argument("--keep-repo", action="store_true")

    args = parser.parse_args()

    if args.action == "add":
        add_registry(args.url, args.alias, args.branch, args.skill_paths, args.clone_depth)
    elif args.action == "list":
        list_registries()
    elif args.action == "remove":
        remove_registry(args.alias, args.keep_repo)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        output_result(error=str(e))
