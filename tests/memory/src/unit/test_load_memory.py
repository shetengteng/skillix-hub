#!/usr/bin/env python3
"""load_memory.py 纯函数单元测试：load_context、_ensure_memory_md、log_session_start"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.hooks.load_memory import load_context, _ensure_memory_md, log_session_start
from service.config import MEMORY_MD, SESSIONS_FILE
from core.utils import today_str, iso_now


class TestEnsureMemoryMd(IsolatedWorkspaceCase):

    def test_creates_when_missing(self):
        md_path = self.memory_dir / MEMORY_MD
        md_path.unlink()
        self.assertFalse(md_path.exists())

        _ensure_memory_md(str(self.memory_dir))

        self.assertTrue(md_path.exists())
        content = md_path.read_text(encoding="utf-8")
        self.assertIn("# 核心记忆", content)
        self.assertIn("## 用户偏好", content)

    def test_noop_when_exists(self):
        md_path = self.memory_dir / MEMORY_MD
        original = md_path.read_text(encoding="utf-8")

        _ensure_memory_md(str(self.memory_dir))

        self.assertEqual(md_path.read_text(encoding="utf-8"), original)

    def test_creates_directory_if_needed(self):
        new_dir = Path(self.workspace) / "new_memory_dir"
        _ensure_memory_md(str(new_dir))
        self.assertTrue((new_dir / MEMORY_MD).exists())


class TestLoadContext(IsolatedWorkspaceCase):

    def test_loads_memory_md(self):
        ctx = load_context(self.workspace)
        self.assertIn("核心记忆", ctx)
        self.assertIn("语言：中文", ctx)

    def test_loads_recent_facts(self):
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        fact = {
            "id": "fact-001",
            "type": "fact",
            "content": "测试事实内容",
            "memory_type": "W",
            "confidence": 0.9,
            "timestamp": iso_now(),
        }
        daily_file.write_text(json.dumps(fact, ensure_ascii=False) + "\n", encoding="utf-8")

        ctx = load_context(self.workspace)
        self.assertIn("测试事实内容", ctx)
        self.assertIn("近期事实", ctx)

    def test_loads_last_session(self):
        sessions_path = self.memory_dir / SESSIONS_FILE
        session = {
            "id": "sum-001",
            "session_id": "conv-001",
            "topic": "测试会话主题",
            "summary": "这是测试摘要",
            "timestamp": iso_now(),
        }
        sessions_path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")

        ctx = load_context(self.workspace)
        self.assertIn("上次会话", ctx)
        self.assertIn("测试会话主题", ctx)
        self.assertIn("这是测试摘要", ctx)

    def test_empty_workspace_returns_memory_md_only(self):
        ctx = load_context(self.workspace)
        self.assertIn("核心记忆", ctx)
        self.assertNotIn("近期事实", ctx)

    def test_skips_non_fact_entries(self):
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        entries = [
            {"id": "log-001", "type": "session_start", "timestamp": iso_now()},
            {"id": "log-002", "type": "audit", "signals": ["test"], "timestamp": iso_now()},
            {"id": "fact-001", "type": "fact", "content": "真正的事实", "memory_type": "W", "confidence": 0.9, "timestamp": iso_now()},
        ]
        with open(daily_file, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

        ctx = load_context(self.workspace)
        self.assertIn("真正的事实", ctx)


class TestLogSessionStart(IsolatedWorkspaceCase):

    def test_writes_session_start_entry(self):
        log_session_start(str(self.memory_dir), self.workspace, "conv-test-123")

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        self.assertTrue(daily_file.exists())

        entries = [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]
        starts = [e for e in entries if e.get("type") == "session_start"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0]["session_id"], "conv-test-123")
        self.assertEqual(starts[0]["workspace"], self.workspace)

    def test_appends_to_existing_daily(self):
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        existing = {"id": "existing-001", "type": "fact", "content": "已有条目", "timestamp": iso_now()}
        daily_file.write_text(json.dumps(existing, ensure_ascii=False) + "\n", encoding="utf-8")

        log_session_start(str(self.memory_dir), self.workspace, "conv-append")

        entries = [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["type"], "fact")
        self.assertEqual(entries[1]["type"], "session_start")

    def test_creates_daily_dir_if_missing(self):
        import shutil
        daily_dir = self.memory_dir / "daily"
        shutil.rmtree(daily_dir)
        self.assertFalse(daily_dir.exists())

        log_session_start(str(self.memory_dir), self.workspace, "conv-new-dir")
        self.assertTrue(daily_dir.exists())


if __name__ == "__main__":
    unittest.main()
