#!/usr/bin/env python3
"""Hook 增强功能的单元测试：stop status 放宽、sessionEnd 兜底检测、load 日志增强"""
import json
import os
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, run_script, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))


class TestStopHookStatusFilter(IsolatedWorkspaceCase):
    """验证 stop Hook 放宽 status 过滤：completed 和 aborted 都应触发"""

    def _run_stop_hook(self, status):
        event = {
            "status": status,
            "conversation_id": "test-conv-123",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/prompt_session_save.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        return result

    def test_completed_triggers_save(self):
        result = self._run_stop_hook("completed")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("followup_message", output)
        self.assertIn("[Session Save]", output["followup_message"])

    def test_aborted_triggers_save(self):
        result = self._run_stop_hook("aborted")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("followup_message", output)
        self.assertIn("[Session Save]", output["followup_message"])

    def test_error_does_not_trigger(self):
        result = self._run_stop_hook("error")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("followup_message", output)

    def test_empty_status_does_not_trigger(self):
        result = self._run_stop_hook("")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("followup_message", output)


class TestSessionSaveTemplate(IsolatedWorkspaceCase):
    """验证 Session Save 模板包含逐条提取事实的指令"""

    def test_template_requires_fact_extraction(self):
        event = {
            "status": "completed",
            "conversation_id": "test-conv-456",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/prompt_session_save.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        output = json.loads(result.stdout)
        msg = output["followup_message"]
        self.assertIn("逐条提取关键事实", msg)
        self.assertIn("必须执行", msg)
        self.assertIn("save_fact", msg)


class TestSessionEndSummaryCheck(IsolatedWorkspaceCase):
    """验证 sessionEnd 兜底检测：未保存摘要时写入 warning"""

    def test_warning_when_no_summary(self):
        from service.config import SESSIONS_FILE
        from core.utils import today_str

        event = {
            "conversation_id": "test-conv-no-summary",
            "reason": "completed",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/sync_and_cleanup.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = []
            for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    entries.append(json.loads(line))
            warnings = [e for e in entries if e.get("type") == "warning"]
            self.assertTrue(len(warnings) > 0, "Should have warning entry for missing summary")
            self.assertIn("未保存摘要", warnings[0]["content"])

    def test_no_warning_when_summary_exists(self):
        from service.config import SESSIONS_FILE
        from core.utils import today_str, iso_now

        sessions_path = self.memory_dir / SESSIONS_FILE
        summary = {
            "id": "sum-test",
            "session_id": "test-conv-with-summary",
            "topic": "测试会话",
            "summary": "测试摘要",
            "timestamp": iso_now(),
        }
        sessions_path.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")

        event = {
            "conversation_id": "test-conv-with-summary",
            "reason": "completed",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/sync_and_cleanup.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = []
            for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    entries.append(json.loads(line))
            warnings = [e for e in entries if e.get("type") == "warning"]
            self.assertEqual(len(warnings), 0, "Should have no warning when summary exists")


if __name__ == "__main__":
    unittest.main()
