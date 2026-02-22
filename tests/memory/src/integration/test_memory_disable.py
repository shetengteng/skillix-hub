#!/usr/bin/env python3
"""项目级禁用 Memory 功能测试：验证 .memory-disable 标记文件的作用。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from test_common import RUNTIME_ROOT, run_script


class MemoryDisableCase(unittest.TestCase):
    """验证 .cursor/skills/.memory-disable 标记文件能正确禁用所有 Hook。"""

    def setUp(self):
        self.workspace = tempfile.mkdtemp(
            prefix=f"disable-{uuid.uuid4().hex[:8]}-",
            dir=str(RUNTIME_ROOT),
        )
        self.memory_dir = Path(self.workspace) / ".cursor" / "skills" / "memory-data"
        (self.memory_dir / "daily").mkdir(parents=True, exist_ok=True)
        (self.memory_dir / "MEMORY.md").write_text(
            "# 核心记忆\n\n## 用户偏好\n- 语言：中文\n",
            encoding="utf-8",
        )
        self.skills_dir = Path(self.workspace) / ".cursor" / "skills"
        self.disable_file = self.skills_dir / ".memory-disable"

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    def _create_disable_file(self):
        self.disable_file.touch()

    def _remove_disable_file(self):
        if self.disable_file.exists():
            self.disable_file.unlink()

    # ---- is_memory_enabled 单元测试 ----

    def test_is_memory_enabled_returns_true_by_default(self):
        from service.config import is_memory_enabled
        self.assertTrue(is_memory_enabled(self.workspace))

    def test_is_memory_enabled_returns_false_when_disable_file_exists(self):
        from service.config import is_memory_enabled
        self._create_disable_file()
        self.assertFalse(is_memory_enabled(self.workspace))

    def test_is_memory_enabled_returns_true_after_removing_disable_file(self):
        from service.config import is_memory_enabled
        self._create_disable_file()
        self.assertFalse(is_memory_enabled(self.workspace))
        self._remove_disable_file()
        self.assertTrue(is_memory_enabled(self.workspace))

    # ---- load_memory.py 禁用测试 ----

    def test_load_memory_returns_empty_context_when_disabled(self):
        self._create_disable_file()
        event = json.dumps(
            {"type": "sessionStart", "conversation_id": "dis-1", "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out.get("additional_context", ""), "")

    def test_load_memory_does_not_create_daily_when_disabled(self):
        daily_dir = self.memory_dir / "daily"
        if daily_dir.exists():
            shutil.rmtree(str(daily_dir))
        self._create_disable_file()

        event = json.dumps(
            {"type": "sessionStart", "conversation_id": "dis-2", "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)

        daily_files = list(daily_dir.glob("*.jsonl")) if daily_dir.exists() else []
        self.assertEqual(len(daily_files), 0,
                         "No daily JSONL files should be created when disabled")

    # ---- flush_memory.py 禁用测试 ----

    def test_flush_memory_returns_empty_when_disabled(self):
        self._create_disable_file()
        event = json.dumps(
            {
                "type": "preCompact",
                "conversation_id": "dis-3",
                "workspace_roots": [self.workspace],
                "context_usage_percent": 90,
                "message_count": 50,
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/flush_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out, {})

    # ---- prompt_session_save.py 禁用测试 ----

    def test_prompt_session_save_returns_empty_when_disabled(self):
        self._create_disable_file()
        event = json.dumps(
            {
                "type": "stop",
                "conversation_id": "dis-4",
                "workspace_roots": [self.workspace],
                "status": "completed",
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/prompt_session_save.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out, {})

    # ---- sync_and_cleanup.py 禁用测试 ----

    def test_sync_and_cleanup_returns_empty_when_disabled(self):
        self._create_disable_file()
        event = json.dumps(
            {
                "type": "sessionEnd",
                "conversation_id": "dis-5",
                "workspace_roots": [self.workspace],
                "reason": "completed",
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/sync_and_cleanup.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out, {})

    # ---- save_fact.py 禁用测试 ----

    def test_save_fact_skipped_when_disabled(self):
        self._create_disable_file()
        proc = run_script(
            "service/memory/save_fact.py", self.workspace,
            args=["--content", "should not save", "--type", "W",
                  "--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out["reason"], "memory_disabled")

    def test_save_fact_no_file_created_when_disabled(self):
        self._create_disable_file()
        daily_dir = self.memory_dir / "daily"
        before = set(daily_dir.glob("*.jsonl")) if daily_dir.exists() else set()
        run_script(
            "service/memory/save_fact.py", self.workspace,
            args=["--content", "blocked fact", "--project-path", self.workspace],
        )
        after = set(daily_dir.glob("*.jsonl")) if daily_dir.exists() else set()
        self.assertEqual(before, after, "No new daily file should be created when disabled")

    def test_save_fact_works_when_enabled(self):
        proc = run_script(
            "service/memory/save_fact.py", self.workspace,
            args=["--content", "enabled fact", "--type", "W",
                  "--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")

    # ---- save_summary.py 禁用测试 ----

    def test_save_summary_skipped_when_disabled(self):
        self._create_disable_file()
        proc = run_script(
            "service/memory/save_summary.py", self.workspace,
            args=["--topic", "test", "--summary", "should not save",
                  "--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "skipped")
        self.assertEqual(out["reason"], "memory_disabled")

    def test_save_summary_no_file_written_when_disabled(self):
        self._create_disable_file()
        sessions_file = self.memory_dir / "sessions.jsonl"
        before_size = sessions_file.stat().st_size if sessions_file.exists() else 0
        run_script(
            "service/memory/save_summary.py", self.workspace,
            args=["--topic", "blocked", "--summary", "blocked summary",
                  "--project-path", self.workspace],
        )
        after_size = sessions_file.stat().st_size if sessions_file.exists() else 0
        self.assertEqual(before_size, after_size,
                         "sessions.jsonl should not grow when disabled")

    def test_save_summary_works_when_enabled(self):
        proc = run_script(
            "service/memory/save_summary.py", self.workspace,
            args=["--topic", "enabled test", "--summary", "enabled summary",
                  "--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")

    # ---- require_memory_enabled 装饰器单元测试 ----

    def test_decorator_preserves_function_name(self):
        from service.config import require_memory_enabled

        @require_memory_enabled
        def my_func():
            pass

        self.assertEqual(my_func.__name__, "my_func")

    def test_decorator_passes_through_when_enabled(self):
        from service.config import require_memory_enabled
        call_log = []

        @require_memory_enabled
        def tracked():
            call_log.append("called")
            return "result"

        original_argv = sys.argv
        try:
            sys.argv = ["test", "--project-path", self.workspace]
            result = tracked()
            self.assertEqual(call_log, ["called"])
            self.assertEqual(result, "result")
        finally:
            sys.argv = original_argv

    def test_decorator_blocks_when_disabled(self):
        from service.config import require_memory_enabled
        self._create_disable_file()
        call_log = []

        @require_memory_enabled
        def tracked():
            call_log.append("called")

        original_argv = sys.argv
        try:
            sys.argv = ["test", "--project-path", self.workspace]
            from io import StringIO
            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            result = tracked()
            sys.stdout = old_stdout
            self.assertEqual(call_log, [])
            self.assertIsNone(result)
            output = json.loads(captured.getvalue())
            self.assertEqual(output["status"], "skipped")
        finally:
            sys.argv = original_argv

    # ---- 启用后恢复正常 ----

    def test_hooks_work_normally_after_removing_disable_file(self):
        self._create_disable_file()

        event = json.dumps(
            {"type": "sessionStart", "conversation_id": "dis-6", "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        proc1 = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        out1 = json.loads(proc1.stdout)
        self.assertEqual(out1.get("additional_context", ""), "")

        self._remove_disable_file()

        proc2 = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        out2 = json.loads(proc2.stdout)
        self.assertIn("核心记忆", out2.get("additional_context", ""))

    def test_save_fact_resumes_after_reenabling(self):
        self._create_disable_file()
        proc1 = run_script(
            "service/memory/save_fact.py", self.workspace,
            args=["--content", "blocked", "--project-path", self.workspace],
        )
        self.assertEqual(json.loads(proc1.stdout)["status"], "skipped")

        self._remove_disable_file()
        proc2 = run_script(
            "service/memory/save_fact.py", self.workspace,
            args=["--content", "resumed", "--project-path", self.workspace],
        )
        self.assertEqual(json.loads(proc2.stdout)["status"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
