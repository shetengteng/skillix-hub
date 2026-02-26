#!/usr/bin/env python3
"""Skill Store: install, update, uninstall the skill-store itself."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent

EXCLUDE_COPY = {
    "__pycache__", ".pyc", "node_modules", ".git",
    "data", ".DS_Store", ".env"
}

DEFAULT_DATA_FILES = {
    "config.json": {"registries": [], "settings": {"clone_depth": 1}},
    "index.json": {"updated_at": None, "skills": []},
    "installed.json": {"installations": []},
    "status.json": {
        "last_sync": None, "sync_in_progress": False,
        "pending_updates": [], "orphaned_skills": [], "sync_errors": []
    }
}


def _copy_source(src: Path, dst: Path):
    if dst.exists():
        for item in dst.iterdir():
            if item.name in ("data",):
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name in EXCLUDE_COPY or item.suffix == ".pyc":
            continue
        if item.is_dir():
            shutil.copytree(item, dst / item.name, ignore=shutil.ignore_patterns(
                *EXCLUDE_COPY, "*.pyc"
            ))
        else:
            shutil.copy2(item, dst / item.name)


def _install_rules(src: Path):
    rules_src = src / "rules"
    if not rules_src.is_dir():
        return []

    rules_dst = Path.home() / ".cursor" / "rules"
    rules_dst.mkdir(parents=True, exist_ok=True)

    installed = []
    for rule_file in rules_src.glob("*.mdc"):
        dst = rules_dst / rule_file.name
        shutil.copy2(rule_file, dst)
        installed.append(str(dst))

    return installed


def _init_data_dir(target: Path):
    data_dir = target.parent / "skill-store-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "repos").mkdir(exist_ok=True)

    for filename, default_data in DEFAULT_DATA_FILES.items():
        filepath = data_dir / filename
        if not filepath.exists():
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

    return data_dir


def _remove_rules():
    rules_dir = Path.home() / ".cursor" / "rules"
    removed = []
    rule_file = rules_dir / "skill-store-hook.mdc"
    if rule_file.exists():
        rule_file.unlink()
        removed.append(str(rule_file))
    return removed


def install(target: str):
    target_path = Path(target).expanduser().resolve()

    _copy_source(SKILL_DIR, target_path)

    rules = _install_rules(SKILL_DIR)
    data_dir = _init_data_dir(target_path)

    result = {
        "action": "installed",
        "target": str(target_path),
        "rules_installed": rules,
        "data_dir": str(data_dir)
    }
    print(json.dumps({"result": result, "error": None}, ensure_ascii=False, indent=2))


def update(target: str):
    target_path = Path(target).expanduser().resolve()

    if not target_path.exists():
        print(json.dumps({"result": None, "error": f"Target not found: {target_path}"}, indent=2))
        return

    data_dir = target_path.parent / "skill-store-data"
    data_backup = None
    if data_dir.exists():
        data_backup = target_path.parent / ".skill-store-data-backup"
        if data_backup.exists():
            shutil.rmtree(data_backup)
        shutil.copytree(data_dir, data_backup)

    _copy_source(SKILL_DIR, target_path)
    rules = _install_rules(SKILL_DIR)

    if data_backup and data_backup.exists():
        if data_dir.exists():
            shutil.rmtree(data_dir)
        shutil.copytree(data_backup, data_dir)
        shutil.rmtree(data_backup)

    result = {
        "action": "updated",
        "target": str(target_path),
        "rules_updated": rules,
        "data_preserved": data_backup is not None
    }
    print(json.dumps({"result": result, "error": None}, ensure_ascii=False, indent=2))


def uninstall(target: str, keep_data: bool = False):
    target_path = Path(target).expanduser().resolve()

    removed_rules = _remove_rules()

    data_dir = target_path.parent / "skill-store-data"
    data_removed = False
    if data_dir.exists() and not keep_data:
        shutil.rmtree(data_dir, ignore_errors=True)
        data_removed = True

    if target_path.exists():
        shutil.rmtree(target_path, ignore_errors=True)

    result = {
        "action": "uninstalled",
        "target": str(target_path),
        "rules_removed": removed_rules,
        "data_removed": data_removed,
        "data_kept": keep_data
    }
    print(json.dumps({"result": result, "error": None}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Skill Store Self-Management")
    sub = parser.add_subparsers(dest="action", required=True)

    inst_p = sub.add_parser("install")
    inst_p.add_argument("--target", required=True)

    upd_p = sub.add_parser("update")
    upd_p.add_argument("--target", required=True)

    uninst_p = sub.add_parser("uninstall")
    uninst_p.add_argument("--target", required=True)
    uninst_p.add_argument("--keep-data", action="store_true")

    args = parser.parse_args()

    if args.action == "install":
        install(args.target)
    elif args.action == "update":
        update(args.target)
    elif args.action == "uninstall":
        uninstall(args.target, getattr(args, "keep_data", False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"result": None, "error": str(e)}, indent=2))
