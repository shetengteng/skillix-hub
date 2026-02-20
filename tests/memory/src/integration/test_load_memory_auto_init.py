#!/usr/bin/env python3
"""load_memory.py 自动初始化测试：验证新项目首次会话时自动创建 MEMORY.md。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from test_common import RUNTIME_ROOT, run_script


class AutoInitMemoryMdCase(unittest.TestCase):
    """使用不含 MEMORY.md 的空工作区，验证 load_memory.py 的自动初始化行为。"""

    def setUp(self):
        self.workspace = tempfile.mkdtemp(
            prefix=f"auto-init-{uuid.uuid4().hex[:8]}-",
            dir=str(RUNTIME_ROOT),
        )
        self.memory_dir = Path(self.workspace) / ".cursor" / "skills" / "memory-data"

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    def _run_load(self, conv_id="auto-init-1"):
        event = json.dumps(
            {"type": "sessionStart", "conversation_id": conv_id, "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        return run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)

    def test_auto_creates_memory_md_when_missing(self):
        """新项目首次会话时应自动创建 MEMORY.md。"""
        self.assertFalse((self.memory_dir / "MEMORY.md").exists())

        proc = self._run_load()
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        memory_md = self.memory_dir / "MEMORY.md"
        self.assertTrue(memory_md.exists(), "MEMORY.md should be auto-created")
        content = memory_md.read_text(encoding="utf-8")
        self.assertIn("# 核心记忆", content)
        self.assertIn("## 用户偏好", content)
        self.assertIn("## 项目背景", content)
        self.assertIn("## 重要决策", content)

    def test_auto_created_memory_md_loaded_in_context(self):
        """自动创建的 MEMORY.md 应出现在返回的上下文中。"""
        proc = self._run_load()
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        out = json.loads(proc.stdout)
        self.assertIn("核心记忆", out.get("additional_context", ""))

    def test_does_not_overwrite_existing_memory_md(self):
        """已存在的 MEMORY.md 不应被覆盖。"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        custom_content = "# 核心记忆\n\n## 用户偏好\n- 自定义内容\n"
        (self.memory_dir / "MEMORY.md").write_text(custom_content, encoding="utf-8")

        proc = self._run_load()
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        actual = (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8")
        self.assertEqual(actual, custom_content)

    def test_auto_creates_daily_dir(self):
        """新项目首次会话时应自动创建 daily/ 目录。"""
        proc = self._run_load()
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        daily_dir = self.memory_dir / "daily"
        self.assertTrue(daily_dir.is_dir(), "daily/ directory should be auto-created")

    def test_session_start_logged_in_new_project(self):
        """新项目首次会话应在 daily/ 中记录 session_start。"""
        proc = self._run_load(conv_id="new-proj-1")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        daily_dir = self.memory_dir / "daily"
        daily_files = list(daily_dir.glob("*.jsonl"))
        self.assertTrue(len(daily_files) > 0, "Should have at least one daily file")

        entries = []
        for f in daily_files:
            for line in f.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    entries.append(json.loads(line))
        session_starts = [e for e in entries if e.get("type") == "session_start"]
        self.assertTrue(len(session_starts) > 0, "Should log session_start")


if __name__ == "__main__":
    unittest.main(verbosity=2)
