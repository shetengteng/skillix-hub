#!/usr/bin/env python3
"""USER_MEMORY.md 加载测试"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.hooks.load_memory import load_context
from service.config import MEMORY_MD, USER_MEMORY_MD


class TestUserMemoryLoad(IsolatedWorkspaceCase):

    def test_loads_user_memory_when_exists(self):
        user_md = self.memory_dir / USER_MEMORY_MD
        user_md.write_text(
            "# 用户笔记\n\n- 项目截止日期 2026-03-15\n- 联系人张三\n",
            encoding="utf-8",
        )
        context = load_context(self.workspace)
        self.assertIn("用户自定义记忆", context)
        self.assertIn("项目截止日期", context)
        self.assertIn("联系人张三", context)

    def test_no_user_memory_when_file_missing(self):
        context = load_context(self.workspace)
        self.assertNotIn("用户自定义记忆", context)

    def test_no_user_memory_when_file_empty(self):
        user_md = self.memory_dir / USER_MEMORY_MD
        user_md.write_text("", encoding="utf-8")
        context = load_context(self.workspace)
        self.assertNotIn("用户自定义记忆", context)

    def test_both_memory_files_loaded(self):
        user_md = self.memory_dir / USER_MEMORY_MD
        user_md.write_text("- 用户自定义内容\n", encoding="utf-8")
        context = load_context(self.workspace)
        self.assertIn("核心记忆", context)
        self.assertIn("用户自定义记忆", context)
        self.assertIn("用户自定义内容", context)
        self.assertIn("语言：中文", context)

    def test_user_memory_constant_value(self):
        self.assertEqual(USER_MEMORY_MD, "USER_MEMORY.md")


class TestUpdateSessionState(IsolatedWorkspaceCase):

    def test_update_creates_new_state(self):
        from service.memory.session_state import update_session_state, read_session_state

        update_session_state(str(self.memory_dir), "new-sess", {"distilled": True})
        state = read_session_state(str(self.memory_dir), "new-sess")
        self.assertTrue(state["distilled"])
        self.assertEqual(state["session_id"], "new-sess")

    def test_update_merges_with_existing(self):
        from service.memory.session_state import update_session_state, read_session_state, update_fact_count

        update_fact_count(str(self.memory_dir), "merge-sess", "W")
        update_session_state(str(self.memory_dir), "merge-sess", {"distilled": True})

        state = read_session_state(str(self.memory_dir), "merge-sess")
        self.assertTrue(state["distilled"])
        self.assertEqual(state["fact_count"], 1)

    def test_update_noop_for_empty_session_id(self):
        from service.memory.session_state import update_session_state
        update_session_state(str(self.memory_dir), "", {"distilled": True})
        state_dir = self.memory_dir / "session_state"
        if state_dir.exists():
            json_files = list(state_dir.glob("*.json"))
            self.assertEqual(len(json_files), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
