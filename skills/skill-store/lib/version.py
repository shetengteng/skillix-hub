"""Version comparison: detect updates for installed Skills."""

from __future__ import annotations

from pathlib import Path

from lib.config import load_installed, load_index, REPOS_DIR
from lib.git_ops import get_latest_commit


def check_updates() -> list[dict]:
    installed = load_installed()
    index = load_index()

    index_lookup = {}
    for skill in index.get("skills", []):
        key = (skill["registry_alias"], skill["name"])
        index_lookup[key] = skill

    pending = []
    for inst in installed.get("installations", []):
        key = (inst["registry_alias"], inst["name"])
        idx_skill = index_lookup.get(key)

        if not idx_skill:
            continue

        repo_dir = REPOS_DIR / inst["registry_alias"]
        if not repo_dir.exists():
            continue

        latest_commit = get_latest_commit(repo_dir, inst.get("source_path", ""))
        if latest_commit and latest_commit != inst.get("source_commit"):
            pending.append({
                "name": inst["name"],
                "registry_alias": inst["registry_alias"],
                "installed_commit": inst.get("source_commit", "unknown"),
                "latest_commit": latest_commit,
                "scope": inst.get("scope", "global"),
                "target_path": inst.get("target_path", "")
            })

    return pending


def check_orphaned() -> list[dict]:
    installed = load_installed()
    orphaned = []

    for inst in installed.get("installations", []):
        target = Path(inst["target_path"]).expanduser()
        if not target.exists():
            orphaned.append({
                "name": inst["name"],
                "registry_alias": inst["registry_alias"],
                "scope": inst.get("scope", "global"),
                "target_path": inst["target_path"]
            })

    return orphaned


def clean_orphaned():
    installed = load_installed()
    before = len(installed.get("installations", []))
    installed["installations"] = [
        inst for inst in installed["installations"]
        if Path(inst["target_path"]).expanduser().exists()
    ]
    after = len(installed["installations"])
    from lib.config import save_installed
    save_installed(installed)
    return before - after
