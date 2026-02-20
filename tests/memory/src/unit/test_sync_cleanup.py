#!/usr/bin/env python3
"""sync_and_cleanup.py 纯函数单元测试：check_summary_saved、log_session_end、clean_old_logs"""
import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.hooks.sync_and_cleanup import check_summary_saved, log_session_end, clean_old_logs
from service.config import SESSIONS_FILE
from core.utils import today_str, iso_now


class TestCheckSummarySaved(IsolatedWorkspaceCase):

    def _read_daily_entries(self):
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if not daily_file.exists():
            return []
        return [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]

    def test_writes_warning_when_no_summary(self):
        event = {
            "conversation_id": "conv-no-summary",
            "reason": "completed",
        }
        check_summary_saved(str(self.memory_dir), event)

        entries = self._read_daily_entries()
        warnings = [e for e in entries if e.get("type") == "warning"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("未保存摘要", warnings[0]["content"])
        self.assertEqual(warnings[0]["session_id"], "conv-no-summary")

    def test_no_warning_when_summary_matches(self):
        sessions_path = self.memory_dir / SESSIONS_FILE
        summary = {
            "id": "sum-match",
            "session_id": "conv-with-summary",
            "topic": "测试",
            "summary": "摘要",
            "timestamp": iso_now(),
        }
        sessions_path.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")

        event = {
            "conversation_id": "conv-with-summary",
            "reason": "completed",
        }
        check_summary_saved(str(self.memory_dir), event)

        entries = self._read_daily_entries()
        warnings = [e for e in entries if e.get("type") == "warning"]
        self.assertEqual(len(warnings), 0)

    def test_skips_when_no_conv_id(self):
        event = {"conversation_id": "", "reason": "completed"}
        check_summary_saved(str(self.memory_dir), event)
        entries = self._read_daily_entries()
        self.assertEqual(len(entries), 0)

    def test_skips_when_reason_is_error(self):
        event = {"conversation_id": "conv-error", "reason": "error"}
        check_summary_saved(str(self.memory_dir), event)
        entries = self._read_daily_entries()
        self.assertEqual(len(entries), 0)

    def test_warning_when_summary_session_id_mismatch(self):
        sessions_path = self.memory_dir / SESSIONS_FILE
        summary = {
            "id": "sum-other",
            "session_id": "conv-different",
            "topic": "其他会话",
            "summary": "其他摘要",
            "timestamp": iso_now(),
        }
        sessions_path.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")

        event = {
            "conversation_id": "conv-current",
            "reason": "completed",
        }
        check_summary_saved(str(self.memory_dir), event)

        entries = self._read_daily_entries()
        warnings = [e for e in entries if e.get("type") == "warning"]
        self.assertEqual(len(warnings), 1)

    def test_user_close_reason_triggers_check(self):
        event = {
            "conversation_id": "conv-user-close",
            "reason": "user_close",
        }
        check_summary_saved(str(self.memory_dir), event)
        entries = self._read_daily_entries()
        warnings = [e for e in entries if e.get("type") == "warning"]
        self.assertEqual(len(warnings), 1)


class TestLogSessionEnd(IsolatedWorkspaceCase):

    def _read_daily_entries(self):
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if not daily_file.exists():
            return []
        return [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]

    def test_writes_session_end_entry(self):
        event = {
            "conversation_id": "conv-end-001",
            "reason": "completed",
            "duration_ms": 12345,
        }
        log_session_end(str(self.memory_dir), event)

        entries = self._read_daily_entries()
        ends = [e for e in entries if e.get("type") == "session_end"]
        self.assertEqual(len(ends), 1)
        self.assertEqual(ends[0]["reason"], "completed")
        self.assertEqual(ends[0]["duration_ms"], 12345)
        self.assertEqual(ends[0]["session_id"], "conv-end-001")

    def test_includes_error_message(self):
        event = {
            "conversation_id": "conv-err",
            "reason": "error",
            "error_message": "something broke",
        }
        log_session_end(str(self.memory_dir), event)

        entries = self._read_daily_entries()
        ends = [e for e in entries if e.get("type") == "session_end"]
        self.assertEqual(ends[0]["error"], "something broke")

    def test_no_error_key_when_no_error(self):
        event = {
            "conversation_id": "conv-ok",
            "reason": "completed",
        }
        log_session_end(str(self.memory_dir), event)

        entries = self._read_daily_entries()
        ends = [e for e in entries if e.get("type") == "session_end"]
        self.assertNotIn("error", ends[0])

    def test_defaults_for_missing_fields(self):
        log_session_end(str(self.memory_dir), {})

        entries = self._read_daily_entries()
        ends = [e for e in entries if e.get("type") == "session_end"]
        self.assertEqual(len(ends), 1)
        self.assertEqual(ends[0]["reason"], "unknown")
        self.assertEqual(ends[0]["session_id"], "")
        self.assertIsNone(ends[0]["duration_ms"])


class TestCleanOldLogs(IsolatedWorkspaceCase):

    def _get_log_dir(self):
        log_dir = Path(self.workspace) / ".cursor" / "skills" / "memory-data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def test_removes_old_log_files(self):
        log_dir = self._get_log_dir()
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        (log_dir / f"{old_date}.log").write_text("old log")
        (log_dir / f"{today}.log").write_text("today log")

        clean_old_logs(self.workspace)

        remaining = [f.name for f in log_dir.iterdir()]
        self.assertNotIn(f"{old_date}.log", remaining)
        self.assertIn(f"{today}.log", remaining)

    def test_ignores_non_date_filenames(self):
        log_dir = self._get_log_dir()
        (log_dir / "random.log").write_text("random")

        clean_old_logs(self.workspace)

        self.assertTrue((log_dir / "random.log").exists())

    def test_noop_when_no_log_dir(self):
        clean_old_logs(self.workspace)

    def test_keeps_recent_logs(self):
        log_dir = self._get_log_dir()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        (log_dir / f"{yesterday}.log").write_text("yesterday")

        clean_old_logs(self.workspace)

        self.assertTrue((log_dir / f"{yesterday}.log").exists())


if __name__ == "__main__":
    unittest.main()
