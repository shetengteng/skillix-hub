#!/usr/bin/env python3
"""
stop Hook：构建会话保存指令，让 Agent 在任务完成时生成摘要并补充提取事实。

使用场景：当会话状态为 completed 或 aborted 时，Cursor 触发 stop Hook，
本脚本生成 [Session Save] 提示词注入 followup_message，引导 Agent 调用
save_summary.py 和 save_fact.py。
"""
import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import require_hook_memory
from service.config import get_memory_dir
from service.memory.session_state import read_session_state
from service.logger import get_logger

log = get_logger("stop_hook")

_MEMORY_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory"))
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
SAVE_SUMMARY_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'save_summary.py')}"
SAVE_FACT_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'save_fact.py')}"
DISTILL_REFINED_CMD = f"python3 {os.path.join(_MEMORY_DIR, 'distill_refined.py')}"


def _load_template(name: str) -> str:
    path = os.path.join(_PROMPTS_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().rstrip()


def has_session_data(memory_dir: str, conv_id: str) -> bool:
    """
    检查本会话是否已保存摘要。
    只检查 summary_saved 状态，fact_count 不作为跳过条件。
    这样当用户手动说"结束"触发 Session Save 后，stop Hook 会跳过；
    而仅有 facts 未保存 summary 时，stop Hook 仍作为兜底触发。
    """
    state = read_session_state(memory_dir, conv_id)
    if state and state.get("summary_saved"):
        return True
    return False


@require_hook_memory()
def main(event, project_path):
    """主入口：在 status=completed 或 aborted 时生成 [Session Save] 提示词。"""
    status = event.get("status", "")
    conv_id = event.get("conversation_id", "unknown")

    log.info("stop 触发 status=%s conv_id=%s", status, conv_id)

    if status not in ("completed", "aborted"):
        log.info("status=%s 非 completed/aborted，跳过摘要保存提示", status)
        print(json.dumps({}))
        return

    memory_dir = get_memory_dir(project_path)
    os.makedirs(memory_dir, exist_ok=True)

    if conv_id and conv_id != "unknown" and has_session_data(memory_dir, conv_id):
        log.info("会话已有数据，跳过 followup_message conv_id=%s", conv_id[:12])
        print(json.dumps({}))
        return

    memory_md_path = os.path.join(memory_dir, "MEMORY.md")
    distill_section = ""
    if os.path.isfile(memory_md_path):
        distill_section = _load_template("distill_section_template.txt").format(
            memory_md_path=memory_md_path,
            distill_cmd=DISTILL_REFINED_CMD,
            project_path=project_path,
            conv_id=conv_id,
        )

    prompt = _load_template("session_save_template.txt").format(
        save_summary_cmd=SAVE_SUMMARY_CMD,
        save_fact_cmd=SAVE_FACT_CMD,
        conv_id=conv_id,
        distill_section=distill_section,
    )

    log.info("[Layer4] 注入 [Session Save] 提示词（兜底）conv_id=%s", conv_id[:12])
    print(json.dumps({"followup_message": prompt}))


if __name__ == "__main__":
    main()
