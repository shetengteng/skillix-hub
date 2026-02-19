#!/usr/bin/env python3
"""
一键初始化 Memory Skill：安装代码、hooks、rules、数据目录，可选下载嵌入模型。

使用场景：首次使用或迁移项目时执行。支持 --global 安装到 ~/.cursor，
--skip-model 跳过模型下载以加快安装。
"""
import sys
import os
import json
import argparse

_INIT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_INIT_DIR, "..", ".."))
sys.path.insert(0, _INIT_DIR)

from service.config import _DEFAULTS
from helpers import (
    SKILL_ROOT,
    TEMPLATES_DIR,
    merge_hooks,
    install_rules,
    init_memory_dir,
    install_skill_code,
    install_dependencies,
    download_model,
)


def main():
    """CLI 入口：解析 --global、--skip-model、--project-path，执行完整安装流程。"""
    parser = argparse.ArgumentParser(description="Initialize Memory Skill")
    parser.add_argument("--global", dest="global_mode", action="store_true",
                        help="Install to global ~/.cursor/ instead of project .cursor/")
    parser.add_argument("--skip-model", action="store_true",
                        help="Skip embedding model download")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    project_path = args.project_path
    skill_root = os.path.abspath(SKILL_ROOT)

    if args.global_mode:
        cursor_dir = os.path.expanduser("~/.cursor")
        skill_install_dir = os.path.join(cursor_dir, "skills", "memory")
        memory_data_rel = os.path.join("~/.cursor", "skills", "memory-data")
    else:
        cursor_dir = os.path.join(project_path, ".cursor")
        skill_install_dir = os.path.join(cursor_dir, "skills", "memory")
        memory_data_rel = os.path.join(".cursor", "skills", "memory-data")

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

    print("Memory Skill Initializing...")
    print(f"  Mode: {'global' if args.global_mode else 'local'}")
    print(f"  Skill path: {skill_install_dir}")
    print()

    code_path = install_skill_code(skill_root, skill_install_dir, replacements)
    print(f"  skill code: {code_path}")

    hooks_template = os.path.join(TEMPLATES_DIR, "hooks.json")
    hooks_target = os.path.join(cursor_dir, "hooks.json")
    hooks_path = merge_hooks(hooks_target, hooks_template, skill_rel)
    print(f"  hooks.json: {hooks_path}")

    rules_template = os.path.join(TEMPLATES_DIR, "memory-rules.mdc")
    rules_dir = os.path.join(cursor_dir, "rules")
    rules_path = install_rules(rules_dir, rules_template, replacements)
    print(f"  rules: {rules_path}")

    memory_dir = init_memory_dir(project_path)
    print(f"  data dir: {memory_dir}")

    config_json = os.path.join(memory_dir, "config.json")
    if not os.path.exists(config_json):
        from service.config import _DEFAULTS
        import copy
        default_config = copy.deepcopy(_DEFAULTS)
        default_config["version"] = 1
        with open(config_json, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  config: {config_json}")
    else:
        print(f"  config: {config_json} (already exists)")

    if not args.skip_model:
        try:
            install_dependencies()
            download_model(_DEFAULTS["embedding"]["model"])
        except Exception as e:
            print(f"  ⚠ Model download failed: {e}")
            print("  (You can install manually later: pip install sentence-transformers)")

    print()
    print("=" * 50)
    print("  Memory Skill initialized!")
    print("=" * 50)
    print()
    print("Installed components:")
    print(f"  hooks.json   → sessionStart / preCompact / stop / sessionEnd")
    print(f"  rules        → memory-rules.mdc")
    print(f"  data dir     → {memory_data_rel}")
    print()
    print("What you can say to Cursor:")
    print('  "记住这个：项目使用 PostgreSQL"')
    print('  "搜索一下关于数据库的记忆"')
    print('  "帮我看一下记忆统计"')
    print('  "删除关于 MySQL 的记忆"')
    print()
    print("Auto behaviors (no action needed):")
    print("  New session  → loads MEMORY.md + recent facts + last summary")
    print("  Long chat    → saves key facts before context compression")
    print("  Task done    → saves session summary automatically")


if __name__ == "__main__":
    main()
