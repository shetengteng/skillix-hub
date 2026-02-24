#!/usr/bin/env python3
"""
卸载 Memory Skill：移除代码、hooks、rules，保留记忆数据。

支持 --global（卸载全局安装）和 --project-path（卸载项目级安装）。
记忆数据目录（memory-data）不会被删除，可随时重新安装恢复功能。
"""
import sys
import os
import json
import shutil
import argparse

_INIT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_INIT_DIR, "..", ".."))


def remove_skill_code(skill_dir):
    """删除 skill 代码目录。"""
    if os.path.isdir(skill_dir):
        shutil.rmtree(skill_dir)
        return True
    return False


def remove_hooks(hooks_path, skill_prefix):
    """从 hooks.json 中移除 memory skill 的所有 hook 条目。"""
    if not os.path.exists(hooks_path):
        return False

    with open(hooks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    hooks = data.get("hooks", {})
    changed = False
    empty_types = []

    for hook_type, cmds in hooks.items():
        filtered = [c for c in cmds if not c.get("command", "").startswith(skill_prefix)]
        if len(filtered) != len(cmds):
            changed = True
            hooks[hook_type] = filtered
            if not filtered:
                empty_types.append(hook_type)

    for t in empty_types:
        del hooks[t]

    if changed:
        with open(hooks_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return changed


def remove_rules(rules_path):
    """删除 memory-rules.mdc 文件。"""
    if os.path.exists(rules_path):
        os.remove(rules_path)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Uninstall Memory Skill (code only, data preserved)")
    parser.add_argument("--global", dest="global_mode", action="store_true",
                        help="Uninstall from global ~/.cursor/")
    parser.add_argument("--project-path", default=os.getcwd())
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be removed without actually removing")
    args = parser.parse_args()

    if args.global_mode:
        cursor_dir = os.path.expanduser("~/.cursor")
        skill_dir = os.path.join(cursor_dir, "skills", "memory")
    else:
        cursor_dir = os.path.join(args.project_path, ".cursor")
        skill_dir = os.path.join(cursor_dir, "skills", "memory")

    hooks_path = os.path.join(cursor_dir, "hooks.json")
    rules_path = os.path.join(cursor_dir, "rules", "memory-rules.mdc")
    skill_prefix = f"python3 {skill_dir}/"

    mode = "全局" if args.global_mode else "项目"
    print(f"Memory Skill 卸载（{mode}模式）")
    if args.dry_run:
        print("  [DRY RUN] 仅显示将要执行的操作\n")
    print()

    actions = []

    if os.path.isdir(skill_dir):
        actions.append(("代码目录", skill_dir, "删除"))
    else:
        actions.append(("代码目录", skill_dir, "不存在，跳过"))

    if os.path.exists(hooks_path):
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        hook_count = sum(
            1 for cmds in data.get("hooks", {}).values()
            for c in cmds if c.get("command", "").startswith(skill_prefix)
        )
        if hook_count > 0:
            actions.append(("hooks.json", hooks_path, f"移除 {hook_count} 条 hook"))
        else:
            actions.append(("hooks.json", hooks_path, "无 memory hook，跳过"))
    else:
        actions.append(("hooks.json", hooks_path, "不存在，跳过"))

    if os.path.exists(rules_path):
        actions.append(("规则文件", rules_path, "删除"))
    else:
        actions.append(("规则文件", rules_path, "不存在，跳过"))

    for name, path, action in actions:
        print(f"  {name}: {path}")
        print(f"    → {action}")

    data_dir_hint = os.path.join(
        "~/.cursor" if args.global_mode else args.project_path,
        ".cursor", "skills", "memory-data"
    ) if not args.global_mode else "<各项目>/.cursor/skills/memory-data/"
    print(f"\n  记忆数据: {data_dir_hint}")
    print(f"    → 保留不删除")
    print()

    if args.dry_run:
        print("[DRY RUN] 未执行任何操作。去掉 --dry-run 以实际卸载。")
        return

    results = []

    if os.path.isdir(skill_dir):
        if remove_skill_code(skill_dir):
            results.append("代码目录已删除")

    if os.path.exists(hooks_path):
        if remove_hooks(hooks_path, skill_prefix):
            results.append("hooks.json 已清理")

    if os.path.exists(rules_path):
        if remove_rules(rules_path):
            results.append("规则文件已删除")

    print("=" * 50)
    if results:
        print("  ✅ Memory Skill 已卸载")
        for r in results:
            print(f"    • {r}")
    else:
        print("  ℹ 无需卸载（未找到已安装的组件）")
    print("=" * 50)
    print()
    print("记忆数据已保留，重新安装后可恢复：")
    print(f"  python3 <repo>/skills/memory/scripts/service/init/index.py {'--global' if args.global_mode else '--project-path ' + args.project_path}")


if __name__ == "__main__":
    main()
