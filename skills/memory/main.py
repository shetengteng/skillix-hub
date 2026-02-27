#!/usr/bin/env python3
"""
Memory Skill 命令分发入口。

支持命令：
  install  - 完整初始化（首次安装）
  update   - 更新代码、hooks、rules，保留数据目录和已下载模型
"""
import sys
import os
import argparse

_MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_MAIN_DIR, "scripts"))
sys.path.insert(0, _MAIN_DIR)

from scripts.service.init.helpers import (
    SKILL_ROOT,
    TEMPLATES_DIR,
    merge_hooks,
    install_rules,
    install_skill_code,
    install_dependencies,
)


def _build_replacements(skill_install_dir, project_path, global_mode):
    if global_mode:
        skill_rel = skill_install_dir
        memory_data_rel = os.path.join("~/.cursor", "skills", "memory-data")
    else:
        try:
            skill_rel = os.path.relpath(skill_install_dir, project_path)
        except ValueError:
            skill_rel = skill_install_dir
        memory_data_rel = os.path.join(".cursor", "skills", "memory-data")

    script_path = os.path.join(skill_rel, "scripts")
    return skill_rel, {
        "{{SCRIPT_PATH}}": script_path,
        "{{SKILL_PATH}}": skill_rel,
        "{{MEMORY_DATA_PATH}}": memory_data_rel,
    }


def cmd_install(args):
    """转发到 init/index.py 执行完整安装。"""
    init_script = os.path.join(_MAIN_DIR, "scripts", "service", "init", "index.py")
    forward_args = [sys.executable, init_script]
    if args.global_mode:
        forward_args.append("--global")
    if args.skip_model:
        forward_args.append("--skip-model")
    if args.project_path:
        forward_args += ["--project-path", args.project_path]
    import subprocess
    sys.exit(subprocess.call(forward_args))


def _resolve_project_path(args):
    """从 --project-path 或 --target 推导项目路径。

    skill-store 调用时传 --target（安装目录），需要从中推导 project_path。
    """
    if args.project_path:
        return args.project_path

    if args.target:
        target = os.path.abspath(args.target)
        home_prefix = os.path.join(os.path.expanduser("~"), ".cursor", "skills", "memory")
        if target == home_prefix:
            args.global_mode = True
            return os.getcwd()
        suffix = os.path.join(".cursor", "skills", "memory")
        if target.endswith(suffix):
            return target[:-len(suffix)].rstrip(os.sep)

    return os.getcwd()


def cmd_update(args):
    """更新代码、hooks、rules，保留数据目录和已下载模型。"""
    project_path = _resolve_project_path(args)
    skill_root = os.path.abspath(SKILL_ROOT)

    if args.global_mode:
        cursor_dir = os.path.expanduser("~/.cursor")
        skill_install_dir = os.path.join(cursor_dir, "skills", "memory")
    else:
        cursor_dir = os.path.join(project_path, ".cursor")
        skill_install_dir = os.path.join(cursor_dir, "skills", "memory")

    skill_rel, replacements = _build_replacements(skill_install_dir, project_path, args.global_mode)

    print("正在更新 Memory Skill...")
    print(f"  模式: {'全局安装' if args.global_mode else '项目安装'}")
    print(f"  Skill 路径: {skill_install_dir}")
    print()

    code_path = install_skill_code(skill_root, skill_install_dir, replacements)
    print(f"  Skill 代码: {code_path}")

    hooks_template = os.path.join(TEMPLATES_DIR, "hooks.json")
    hooks_target = os.path.join(cursor_dir, "hooks.json")
    hooks_path = merge_hooks(hooks_target, hooks_template, skill_rel)
    print(f"  hooks.json: {hooks_path}")

    rules_template = os.path.join(TEMPLATES_DIR, "memory-rules.mdc")
    rules_dir = os.path.join(cursor_dir, "rules")
    rules_path = install_rules(rules_dir, rules_template, replacements)
    print(f"  规则文件: {rules_path}")

    try:
        install_dependencies()
    except Exception as e:
        print(f"  ⚠ 依赖安装失败: {e}")

    print()
    print("=" * 50)
    print("  ✅ Memory Skill 更新成功！")
    print("=" * 50)
    print()
    print("已更新：代码、hooks、rules、依赖")
    print("已保留：数据目录、记忆文件、嵌入模型")


def main():
    parser = argparse.ArgumentParser(description="Memory Skill 命令入口")
    parser.add_argument("command", choices=["install", "update"], help="执行的命令")
    parser.add_argument("--global", dest="global_mode", action="store_true")
    parser.add_argument("--skip-model", action="store_true")
    parser.add_argument("--project-path", default=None)
    parser.add_argument("--target", default=None,
                        help="skill-store compatibility: install dir path")
    args = parser.parse_args()

    if args.command == "install":
        cmd_install(args)
    elif args.command == "update":
        cmd_update(args)


if __name__ == "__main__":
    main()
