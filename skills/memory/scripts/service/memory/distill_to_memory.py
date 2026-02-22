#!/usr/bin/env python3
"""
自动提炼：从 daily/*.jsonl 中筛选高价值事实，追加写入 MEMORY.md 核心记忆。

在 sessionEnd Hook 中调用，确保 Agent 写入完成后再提炼。
只追加不修改已有内容，幂等执行（去重检测）。
"""
import sys
import os
import re
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import MEMORY_MD, get_memory_dir, get_daily_dir
from storage.jsonl import read_daily_facts
from core.utils import utcnow, parse_iso
from service.logger import get_logger, redirect_to_project
from datetime import timedelta

log = get_logger("distill")

DISTILL_DEFAULTS = {
    "enabled": True,
    "min_confidence": 0.85,
    "min_age_days": 1,
    "max_items_per_run": 5,
    "keywords_rules": {
        "项目规范": ["原则", "规范", "规则", "必须", "不能", "禁止", "不允许", "约定"],
        "重要决策": ["决定", "选择", "使用", "采用", "方案", "替代", "改为", "切换"],
    },
}


def _parse_memory_md(path):
    """解析 MEMORY.md，返回 {章节名: [条目文本列表]}"""
    sections = {}
    current = None
    if not os.path.isfile(path):
        return sections
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("## "):
                current = line[3:].strip()
                sections.setdefault(current, [])
            elif current and line.startswith("- "):
                sections[current].append(line[2:].strip())
    return sections


def _flatten_existing(sections):
    """将所有章节的条目合并为一个集合（用于去重）"""
    items = set()
    for entries in sections.values():
        for e in entries:
            items.add(e.strip().lower())
    return items


def _is_duplicate(content, existing_set):
    """检查内容是否与已有条目重复（精确匹配 + 子串包含）"""
    normalized = content.strip().lower()
    if normalized in existing_set:
        return True
    for existing in existing_set:
        if len(existing) > 20 and (normalized in existing or existing in normalized):
            return True
    return False


def _classify(fact, keywords_rules):
    """根据 memory_type 和关键词将事实分类到 MEMORY.md 章节"""
    mtype = fact.get("memory_type", "W")
    content = fact.get("content", "")

    if mtype == "O":
        return "用户偏好"
    if mtype == "B":
        return "项目背景"

    for section, keywords in keywords_rules.items():
        if any(kw in content for kw in keywords):
            return section

    return "项目背景"


def select_candidates(daily_dir, existing_set, config):
    """从 daily 中筛选符合提炼条件的事实"""
    all_facts = read_daily_facts(daily_dir)
    if not all_facts:
        return []

    now = utcnow()
    min_age = timedelta(days=config["min_age_days"])
    min_conf = config["min_confidence"]
    candidates = []

    for fact in all_facts:
        if fact.get("type") not in ("fact", None):
            continue
        if not fact.get("content"):
            continue
        if fact.get("memory_type") == "S":
            continue

        conf = fact.get("confidence", 0)
        if conf < min_conf:
            continue

        ts = parse_iso(fact.get("timestamp", ""))
        if (now - ts) < min_age:
            continue

        if _is_duplicate(fact["content"], existing_set):
            continue

        candidates.append(fact)

    candidates.sort(key=lambda x: (
        0 if x.get("memory_type") == "O" else 1,
        -x.get("confidence", 0),
    ))

    return candidates[:config["max_items_per_run"]]


def write_to_memory_md(path, section_items):
    """将提炼的事实追加到 MEMORY.md 对应章节末尾"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    section_positions = {}
    for i, line in enumerate(lines):
        if line.startswith("## "):
            name = line[3:].strip()
            section_positions[name] = i

    new_sections = {}
    for section, items in section_items.items():
        if section not in section_positions:
            new_sections[section] = items

    insertions = []
    for section, items in section_items.items():
        if section in section_positions:
            pos = section_positions[section]
            insert_at = pos + 1
            while insert_at < len(lines):
                if lines[insert_at].startswith("## "):
                    break
                insert_at += 1
            while insert_at > 0 and lines[insert_at - 1].strip() == "":
                insert_at -= 1
            new_lines = ["- " + item + "\n" for item in items]
            insertions.append((insert_at, new_lines))

    for pos, new_lines in sorted(insertions, reverse=True):
        for nl in reversed(new_lines):
            lines.insert(pos, nl)

    if new_sections:
        lines.append("\n")
        for section, items in new_sections.items():
            lines.append(f"## {section}\n\n")
            for item in items:
                lines.append(f"- {item}\n")
            lines.append("\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def distill(project_path, config=None):
    """主入口：从 daily 提炼高价值事实到 MEMORY.md"""
    if config is None:
        config = DISTILL_DEFAULTS

    if not config.get("enabled", True):
        log.info("自动提炼已禁用")
        return 0

    memory_dir = get_memory_dir(project_path)
    daily_dir = get_daily_dir(project_path)
    memory_md_path = os.path.join(memory_dir, MEMORY_MD)

    if not os.path.isfile(memory_md_path):
        log.info("MEMORY.md 不存在，跳过提炼")
        return 0

    sections = _parse_memory_md(memory_md_path)
    existing_set = _flatten_existing(sections)

    candidates = select_candidates(daily_dir, existing_set, config)
    if not candidates:
        log.info("无新事实需要提炼")
        return 0

    section_items = {}
    for fact in candidates:
        section = _classify(fact, config.get("keywords_rules", DISTILL_DEFAULTS["keywords_rules"]))
        section_items.setdefault(section, []).append(fact["content"])

    write_to_memory_md(memory_md_path, section_items)

    total = sum(len(v) for v in section_items.values())
    sections_str = ", ".join(f"{k}({len(v)})" for k, v in section_items.items())
    log.info("提炼完成: %d 条事实 → %s", total, sections_str)
    return total


def main():
    parser = argparse.ArgumentParser(description="Distill facts to MEMORY.md")
    parser.add_argument("--project-path", default=os.getcwd())
    parser.add_argument("--dry-run", action="store_true", help="Only show candidates, don't write")
    args = parser.parse_args()

    redirect_to_project(args.project_path)

    if args.dry_run:
        memory_dir = get_memory_dir(args.project_path)
        daily_dir = get_daily_dir(args.project_path)
        memory_md_path = os.path.join(memory_dir, MEMORY_MD)
        sections = _parse_memory_md(memory_md_path)
        existing_set = _flatten_existing(sections)
        candidates = select_candidates(daily_dir, existing_set, DISTILL_DEFAULTS)
        if candidates:
            print(f"候选事实 ({len(candidates)} 条):")
            for c in candidates:
                section = _classify(c, DISTILL_DEFAULTS["keywords_rules"])
                print(f"  [{c.get('memory_type', '?')}] → {section}: {c['content'][:80]}")
        else:
            print("无候选事实")
        return

    count = distill(args.project_path)
    print(f"提炼完成: {count} 条")


if __name__ == "__main__":
    main()
