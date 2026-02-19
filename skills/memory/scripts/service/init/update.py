#!/usr/bin/env python3
"""
更新 Memory Skill：从源码目录更新已安装的 skill 代码、hooks、rules。

与 init 的区别：
- init：首次安装，创建数据目录、默认配置、下载模型
- update：更新已安装的代码，不触碰数据目录和配置，不下载模型

使用方式：
  python3 update.py --source <skillix-hub>/skills/memory --project-path <项目路径>
  python3 update.py --source <skillix-hub>/skills/memory --global
"""
import sys
import os
import json
import argparse

_INIT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_INIT_DIR, "..", ".."))
sys.path.insert(0, _INIT_DIR)

from helpers import (
    merge_hooks,
    install_rules,
    install_skill_code,
)


def main():
    parser = argparse.ArgumentParser(description="Update Memory Skill")
    parser.add_argument("--source", required=True,
                        help="Path to the new skill source directory (e.g. skillix-hub/skills/memory)")
    parser.add_argument("--global", dest="global_mode", action="store_true",
                        help="Update global ~/.cursor/ installation")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    source_dir = os.path.abspath(args.source)
    if not os.path.isdir(source_dir):
        print(f"Error: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    project_path = args.project_path

    if args.global_mode:
        cursor_dir = os.path.expanduser("~/.cursor")
        skill_install_dir = os.path.join(cursor_dir, "skills", "memory")
        memory_data_rel = os.path.join("~/.cursor", "skills", "memory-data")
    else:
        cursor_dir = os.path.join(project_path, ".cursor")
        skill_install_dir = os.path.join(cursor_dir, "skills", "memory")
        memory_data_rel = os.path.join(".cursor", "skills", "memory-data")

    if not os.path.isdir(skill_install_dir):
        print(f"Error: skill not installed at {skill_install_dir}", file=sys.stderr)
        print("Please run init.py first to install Memory Skill.", file=sys.stderr)
        sys.exit(1)

    if args.global_mode:
        skill_rel = skill_install_dir
    else:
        try:
            skill_rel = os.path.relpath(skill_install_dir, project_path)
        except ValueError:
            skill_rel = skill_install_dir
    script_path = os.path.join(skill_rel, "scripts")

    replacements = {
        "{{SCRIPT_PATH}}": script_path,
        "{{SKILL_PATH}}": skill_rel,
        "{{MEMORY_DATA_PATH}}": memory_data_rel,
    }

    templates_dir = os.path.join(source_dir, "templates")

    print("Memory Skill Updating...")
    print(f"  Mode: {'global' if args.global_mode else 'local'}")
    print(f"  Source: {source_dir}")
    print(f"  Target: {skill_install_dir}")
    print()

    code_path = install_skill_code(source_dir, skill_install_dir, replacements)
    print(f"  skill code: {code_path} (updated)")

    hooks_template = os.path.join(templates_dir, "hooks.json")
    if os.path.isfile(hooks_template):
        hooks_target = os.path.join(cursor_dir, "hooks.json")
        hooks_path = merge_hooks(hooks_target, hooks_template, skill_rel)
        print(f"  hooks.json: {hooks_path} (merged)")

    rules_template = os.path.join(templates_dir, "memory-rules.mdc")
    if os.path.isfile(rules_template):
        rules_dir = os.path.join(cursor_dir, "rules")
        rules_path = install_rules(rules_dir, rules_template, replacements)
        print(f"  rules: {rules_path} (updated)")

    print()
    print("=" * 50)
    print("  Memory Skill updated!")
    print("=" * 50)
    print()
    print("Preserved (not modified):")
    print(f"  data dir     → {memory_data_rel}")
    print(f"  config.json  → (unchanged)")
    print(f"  MEMORY.md    → (unchanged)")
    print(f"  *.jsonl      → (unchanged)")


if __name__ == "__main__":
    main()
