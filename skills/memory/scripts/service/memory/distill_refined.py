#!/usr/bin/env python3
"""
CLI 工具：接收 Agent 精炼后的记忆内容，全量重写 MEMORY.md。

由 stop hook 的 DISTILL_SECTION 指令引导 Agent 调用。
Agent 读取当前 MEMORY.md + daily facts，用自身模型能力精炼后，
将结构化 JSON 传入本脚本写入。

写入前备份旧文件到 MEMORY.md.bak。
写入后在 session_state 中标记 distilled=true，
使 sessionEnd 中的 distill_to_memory.py 跳过重复精炼。
"""
import sys
import os
import json
import shutil
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import MEMORY_MD, get_memory_dir
from service.config import require_memory_enabled
from service.memory.session_state import update_session_state
from service.logger import get_logger, redirect_to_project

log = get_logger("distill_refined")

SECTION_ORDER = ["用户偏好", "项目背景", "项目规范", "重要决策", "常用工具"]


def build_memory_md(sections: dict) -> str:
    """将章节字典构建为 MEMORY.md 格式的字符串。"""
    lines = ["# 核心记忆\n"]

    for section in SECTION_ORDER:
        items = sections.get(section, [])
        lines.append(f"\n## {section}\n")
        for item in items:
            item = item.strip()
            if item:
                lines.append(f"- {item}")
        lines.append("")

    for section, items in sections.items():
        if section not in SECTION_ORDER and items:
            lines.append(f"\n## {section}\n")
            for item in items:
                item = item.strip()
                if item:
                    lines.append(f"- {item}")
            lines.append("")

    return "\n".join(lines) + "\n"


@require_memory_enabled
def main():
    parser = argparse.ArgumentParser(description="Write refined memory to MEMORY.md")
    parser.add_argument("--content", required=True,
                        help='JSON object: {"章节名": ["条目1", "条目2"], ...}')
    parser.add_argument("--session", default="")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    redirect_to_project(args.project_path)

    try:
        sections = json.loads(args.content)
    except json.JSONDecodeError as e:
        log.error("JSON 解析失败: %s", e)
        print(json.dumps({"status": "error", "reason": f"invalid JSON: {e}"}))
        return

    if not isinstance(sections, dict):
        log.error("content 必须是 JSON 对象，收到: %s", type(sections).__name__)
        print(json.dumps({"status": "error", "reason": "content must be a JSON object"}))
        return

    total_items = sum(len(v) for v in sections.values() if isinstance(v, list))
    if total_items == 0:
        log.warning("精炼结果为空，跳过写入")
        print(json.dumps({"status": "skipped", "reason": "empty content"}))
        return

    memory_dir = get_memory_dir(args.project_path)
    memory_md_path = os.path.join(memory_dir, MEMORY_MD)

    if os.path.isfile(memory_md_path):
        bak_path = memory_md_path + ".bak"
        shutil.copy2(memory_md_path, bak_path)
        log.info("备份旧 MEMORY.md → %s", os.path.basename(bak_path))

    content = build_memory_md(sections)
    with open(memory_md_path, "w", encoding="utf-8") as f:
        f.write(content)

    sections_str = ", ".join(f"{k}({len(v)})" for k, v in sections.items() if isinstance(v, list))
    log.info("精炼写入完成: %d 条 → %s", total_items, sections_str)

    if args.session:
        update_session_state(memory_dir, args.session, {"distilled": True})

    print(json.dumps({
        "status": "ok",
        "total_items": total_items,
        "sections": {k: len(v) for k, v in sections.items() if isinstance(v, list)},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
