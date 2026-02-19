#!/usr/bin/env python3
"""init 一键初始化测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import shutil
import tempfile
from pathlib import Path

from test_common import IsolatedWorkspaceCase, run_script


class DetailInitTests(IsolatedWorkspaceCase):
    def test_init_creates_hooks_rules_data_and_is_idempotent(self):
        init_workspace = tempfile.mkdtemp(prefix="detail-init-")
        try:
            first = run_script(
                "service/init/index.py",
                self.workspace,
                args=["--skip-model", "--project-path", init_workspace],
            )
            self.assertEqual(first.returncode, 0, msg=first.stderr)

            hooks_path = Path(init_workspace) / ".cursor" / "hooks.json"
            rules_path = Path(init_workspace) / ".cursor" / "rules" / "memory-rules.mdc"
            memory_dir = Path(init_workspace) / ".cursor" / "skills" / "memory-data"
            memory_md = memory_dir / "MEMORY.md"
            config_json = memory_dir / "config.json"

            self.assertTrue(hooks_path.exists())
            self.assertTrue(rules_path.exists())
            self.assertTrue(memory_dir.exists())
            self.assertTrue((memory_dir / "daily").exists())
            self.assertTrue(memory_md.exists())
            self.assertTrue(config_json.exists())

            hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertIn("hooks", hooks)
            for hook_name in ("sessionStart", "preCompact", "stop", "sessionEnd"):
                self.assertIn(hook_name, hooks["hooks"])

            memory_md.write_text(memory_md.read_text(encoding="utf-8") + "\n- Custom content\n", encoding="utf-8")
            second = run_script(
                "service/init/index.py",
                self.workspace,
                args=["--skip-model", "--project-path", init_workspace],
            )
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            self.assertIn("Custom content", memory_md.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(init_workspace, ignore_errors=True)


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
