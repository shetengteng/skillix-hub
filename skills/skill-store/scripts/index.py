#!/usr/bin/env python3
"""Index: build and search the local Skill index."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import (
    load_config, load_index, save_index, ensure_data_dir, output_result, REPOS_DIR
)
from lib.git_ops import get_latest_commit, get_commit_date


def parse_skill_md(skill_md_path: Path) -> dict | None:
    if not skill_md_path.exists():
        return None
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError:
        return None

    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None

    frontmatter = fm_match.group(1)
    result = {}

    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip().strip("'\"")

    desc_match = re.search(r"^description:\s*\|?\s*\n((?:\s+.+\n?)+)", frontmatter, re.MULTILINE)
    if desc_match:
        result["description"] = " ".join(
            line.strip() for line in desc_match.group(1).strip().splitlines()
        )
    else:
        desc_single = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
        if desc_single:
            result["description"] = desc_single.group(1).strip().strip("'\"")

    deps_match = re.search(r"^dependencies:\s*\n((?:\s+-\s+.+\n?)+)", frontmatter, re.MULTILINE)
    if deps_match:
        result["dependencies"] = [
            line.strip().lstrip("- ").strip()
            for line in deps_match.group(1).strip().splitlines()
        ]

    if "name" not in result or "description" not in result:
        return None

    return result


def scan_registry(alias: str, skill_paths: list[str]) -> list[dict]:
    repo_dir = REPOS_DIR / alias
    if not repo_dir.exists():
        return []

    skills = []
    for sp in skill_paths:
        scan_dir = repo_dir / sp
        if not scan_dir.is_dir():
            continue

        for entry in scan_dir.iterdir():
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            parsed = parse_skill_md(skill_md)
            if not parsed:
                continue

            relative_path = str(entry.relative_to(repo_dir))
            commit_hash = get_latest_commit(repo_dir, relative_path)
            commit_date = get_commit_date(repo_dir, relative_path)

            skills.append({
                "name": parsed["name"],
                "description": parsed.get("description", ""),
                "dependencies": parsed.get("dependencies", []),
                "registry_alias": alias,
                "relative_path": relative_path,
                "commit_hash": commit_hash,
                "commit_date": commit_date,
                "has_skill_md": True
            })

    return skills


def rebuild_index():
    ensure_data_dir()
    config = load_config()
    all_skills = []

    for reg in config.get("registries", []):
        alias = reg["alias"]
        skill_paths = reg.get("skill_paths", ["skills/"])
        skills = scan_registry(alias, skill_paths)
        all_skills.extend(skills)

    index = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "skills": all_skills
    }
    save_index(index)

    output_result({
        "action": "rebuild",
        "total_skills": len(all_skills),
        "by_registry": {
            alias: sum(1 for s in all_skills if s["registry_alias"] == alias)
            for alias in set(s["registry_alias"] for s in all_skills)
        }
    })


def search_index(query: str):
    index = load_index()
    query_lower = query.lower()
    keywords = query_lower.split()

    scored = []
    for skill in index.get("skills", []):
        name = skill.get("name", "").lower()
        desc = skill.get("description", "").lower()
        text = f"{name} {desc}"

        score = 0
        for kw in keywords:
            if kw in name:
                score += 3
            if kw in desc:
                score += 1

        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)

    output_result({
        "query": query,
        "total_matches": len(scored),
        "results": [s for _, s in scored[:20]]
    })


def list_skills():
    index = load_index()
    skills = index.get("skills", [])
    output_result({
        "total": len(skills),
        "updated_at": index.get("updated_at"),
        "skills": skills
    })


def main():
    parser = argparse.ArgumentParser(description="Skill Store Index")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("rebuild")

    search_p = sub.add_parser("search")
    search_p.add_argument("--query", required=True)

    sub.add_parser("list")

    args = parser.parse_args()

    if args.action == "rebuild":
        rebuild_index()
    elif args.action == "search":
        search_index(args.query)
    elif args.action == "list":
        list_skills()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        output_result(error=str(e))
