#!/usr/bin/env python3
"""Install, update, uninstall Skills from the local index."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    load_config, load_index, load_installed, save_installed,
    ensure_data_dir, output_result, REPOS_DIR, EXCLUDE_PATTERNS
)
from lib.git_ops import get_latest_commit, pull
from lib.dependency import resolve_dependencies
from scripts.index import parse_skill_md


def _find_skill_in_index(name: str, registry_alias: str | None = None) -> dict | None:
    index = load_index()
    candidates = [s for s in index.get("skills", []) if s["name"] == name]
    if not candidates:
        return None
    if registry_alias:
        for c in candidates:
            if c["registry_alias"] == registry_alias:
                return c
    return candidates[0]


def _copy_skill(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name in EXCLUDE_PATTERNS:
            continue
        if item.suffix == ".pyc":
            continue
        if item.is_dir():
            shutil.copytree(item, dst / item.name, ignore=shutil.ignore_patterns(
                *EXCLUDE_PATTERNS, "*.pyc"
            ))
        else:
            shutil.copy2(item, dst / item.name)


def _install_dependencies(dst: Path):
    pkg_json = dst / "package.json"
    if pkg_json.exists():
        subprocess.run(["npm", "install", "--production"], cwd=str(dst),
                       capture_output=True, timeout=120)

    req_txt = dst / "requirements.txt"
    if req_txt.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_txt)],
                       capture_output=True, timeout=120)


def _run_skill_install(dst: Path, target: str):
    tool_js = dst / "tool.js"
    if tool_js.exists():
        import json
        subprocess.run(
            ["node", str(tool_js), "install", json.dumps({"target": target})],
            cwd=str(dst), capture_output=True, timeout=120
        )
        return

    main_py = dst / "main.py"
    if main_py.exists():
        subprocess.run(
            [sys.executable, str(main_py), "install", "--target", target],
            cwd=str(dst), capture_output=True, timeout=120
        )


def _resolve_target(name: str, scope: str, project_path: str | None = None) -> Path:
    if scope == "project":
        if not project_path:
            project_path = os.getcwd()
        return Path(project_path) / ".cursor" / "skills" / name
    return Path.home() / ".cursor" / "skills" / name


def install_skill(name: str, registry_alias: str | None = None,
                  scope: str = "global", project_path: str | None = None,
                  skip_deps: bool = False):
    ensure_data_dir()

    skill_info = _find_skill_in_index(name, registry_alias)
    if not skill_info:
        output_result(error=f"Skill '{name}' not found in index. Run 'index.py rebuild' first.")
        return

    reg_alias = skill_info["registry_alias"]
    rel_path = skill_info["relative_path"]
    src = REPOS_DIR / reg_alias / rel_path

    if not src.exists():
        output_result(error=f"Source directory not found: {src}")
        return

    dep_results = []
    if not skip_deps:
        deps, warnings = resolve_dependencies(name, reg_alias)
        deps_to_install = [d for d in deps if d["name"] != name]
        for dep in deps_to_install:
            dep_target = _resolve_target(dep["name"], scope, project_path)
            if dep_target.exists():
                continue
            dep_src = REPOS_DIR / dep["registry_alias"] / dep["relative_path"]
            if dep_src.exists():
                _copy_skill(dep_src, dep_target)
                _install_dependencies(dep_target)
                _record_installation(dep, dep_target, scope)
                dep_results.append({"name": dep["name"], "installed": True})
        if warnings:
            dep_results.append({"warnings": warnings})

    target = _resolve_target(name, scope, project_path)
    _copy_skill(src, target)
    _install_dependencies(target)
    _run_skill_install(target, str(target))
    _record_installation(skill_info, target, scope)

    output_result({
        "action": "installed",
        "name": name,
        "registry": reg_alias,
        "target": str(target),
        "scope": scope,
        "dependencies": dep_results
    })


def _record_installation(skill_info: dict, target: Path, scope: str):
    installed = load_installed()
    installed["installations"] = [
        inst for inst in installed["installations"]
        if not (inst["name"] == skill_info["name"] and inst["scope"] == scope)
    ]
    installed["installations"].append({
        "name": skill_info["name"],
        "registry_alias": skill_info["registry_alias"],
        "source_commit": skill_info.get("commit_hash"),
        "source_path": skill_info.get("relative_path"),
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "target_path": str(target),
        "scope": scope
    })
    save_installed(installed)


def update_skill(name: str):
    installed = load_installed()
    inst = next((i for i in installed["installations"] if i["name"] == name), None)
    if not inst:
        output_result(error=f"Skill '{name}' is not installed.")
        return

    reg_alias = inst["registry_alias"]
    repo_dir = REPOS_DIR / reg_alias
    if repo_dir.exists():
        pull(repo_dir)

    from scripts.index import rebuild_index as _rebuild
    _rebuild_silent()

    skill_info = _find_skill_in_index(name, reg_alias)
    if not skill_info:
        output_result(error=f"Skill '{name}' no longer found in index after sync.")
        return

    src = REPOS_DIR / reg_alias / skill_info["relative_path"]
    target = Path(inst["target_path"]).expanduser()

    data_dir = target / "data"
    data_backup = None
    if data_dir.exists():
        data_backup = target.parent / f".{target.name}-data-backup"
        if data_backup.exists():
            shutil.rmtree(data_backup)
        shutil.copytree(data_dir, data_backup)

    _copy_skill(src, target)

    if data_backup and data_backup.exists():
        shutil.copytree(data_backup, data_dir)
        shutil.rmtree(data_backup)

    _install_dependencies(target)
    _run_skill_install(target, str(target))
    _record_installation(skill_info, target, inst["scope"])

    output_result({
        "action": "updated",
        "name": name,
        "old_commit": inst.get("source_commit"),
        "new_commit": skill_info.get("commit_hash"),
        "target": str(target)
    })


def _rebuild_silent():
    """Rebuild index without printing output."""
    from lib.config import load_config, save_index, REPOS_DIR
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


def update_all():
    installed = load_installed()
    results = []
    for inst in installed.get("installations", []):
        try:
            update_skill(inst["name"])
            results.append({"name": inst["name"], "success": True})
        except Exception as e:
            results.append({"name": inst["name"], "success": False, "error": str(e)})

    output_result({
        "action": "update_all",
        "total": len(results),
        "succeeded": sum(1 for r in results if r.get("success")),
        "results": results
    })


def uninstall_skill(name: str, scope: str = "global", keep_data: bool = False):
    installed = load_installed()
    inst = next(
        (i for i in installed["installations"]
         if i["name"] == name and i.get("scope", "global") == scope),
        None
    )
    if not inst:
        output_result(error=f"Skill '{name}' (scope={scope}) is not installed.")
        return

    target = Path(inst["target_path"]).expanduser()

    if target.exists():
        if keep_data:
            data_dir = target / "data"
            data_backup = target.parent / f"{target.name}-data"
            if data_dir.exists():
                if data_backup.exists():
                    shutil.rmtree(data_backup)
                shutil.copytree(data_dir, data_backup)
        shutil.rmtree(target, ignore_errors=True)

    installed["installations"] = [
        i for i in installed["installations"]
        if not (i["name"] == name and i.get("scope", "global") == scope)
    ]
    save_installed(installed)

    output_result({
        "action": "uninstalled",
        "name": name,
        "scope": scope,
        "target": str(target),
        "data_kept": keep_data
    })


def list_installed():
    installed = load_installed()
    installations = installed.get("installations", [])
    output_result({
        "total": len(installations),
        "installations": installations
    })


def main():
    parser = argparse.ArgumentParser(description="Skill Store Install")
    sub = parser.add_subparsers(dest="action", required=True)

    inst_p = sub.add_parser("install")
    inst_p.add_argument("--name", required=True)
    inst_p.add_argument("--registry")
    inst_p.add_argument("--scope", default="global", choices=["global", "project"])
    inst_p.add_argument("--project-path")
    inst_p.add_argument("--skip-deps", action="store_true")

    upd_p = sub.add_parser("update")
    upd_p.add_argument("--name", required=True)

    sub.add_parser("update-all")

    uninst_p = sub.add_parser("uninstall")
    uninst_p.add_argument("--name", required=True)
    uninst_p.add_argument("--scope", default="global", choices=["global", "project"])
    uninst_p.add_argument("--keep-data", action="store_true")

    sub.add_parser("list")

    args = parser.parse_args()

    if args.action == "install":
        install_skill(args.name, args.registry, args.scope, args.project_path, args.skip_deps)
    elif args.action == "update":
        update_skill(args.name)
    elif args.action == "update-all":
        update_all()
    elif args.action == "uninstall":
        uninstall_skill(args.name, args.scope, args.keep_data)
    elif args.action == "list":
        list_installed()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        output_result(error=str(e))
