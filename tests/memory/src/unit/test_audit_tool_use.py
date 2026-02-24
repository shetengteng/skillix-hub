#!/usr/bin/env python3
"""audit_tool_use.py 核心逻辑的单元测试。

覆盖：
- should_skip: 跳过 memory 自身脚本调用
- detect_tool_action: 检测 git commit / push / dependency install
- require_hook_memory 装饰器：wrapper 签名为无参函数
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from test_common import IsolatedWorkspaceCase

sys.path.insert(0, str(Path(__file__).resolve().parents[2].parent.parent / "skills" / "memory" / "scripts"))

from service.hooks.audit_tool_use import should_skip, detect_tool_action, SKIP_PATTERNS, CAPTURE_PATTERNS


class TestShouldSkip(unittest.TestCase):
    """should_skip 应过滤 memory 自身脚本调用。"""

    def test_skip_save_fact(self):
        self.assertTrue(should_skip("python3 save_fact.py --content 'test'"))

    def test_skip_save_summary(self):
        self.assertTrue(should_skip("python3 save_summary.py --topic t"))

    def test_skip_distill_to_memory(self):
        self.assertTrue(should_skip("python3 distill_to_memory.py"))

    def test_skip_sync_index(self):
        self.assertTrue(should_skip("python3 sync_index.py"))

    def test_skip_userinput(self):
        self.assertTrue(should_skip("tt userinput.py"))

    def test_no_skip_git_commit(self):
        self.assertFalse(should_skip("git commit -m 'fix bug'"))

    def test_no_skip_npm_install(self):
        self.assertFalse(should_skip("npm install lodash"))

    def test_no_skip_regular_python(self):
        self.assertFalse(should_skip("python3 main.py"))


class TestDetectToolAction(unittest.TestCase):
    """detect_tool_action 应正确识别操作类型并提取信息。"""

    def test_git_commit_with_output(self):
        command = "git commit -m 'add feature'"
        output = "[main abc1234] add feature\n 2 files changed"
        action, extracted = detect_tool_action(command, output)
        self.assertEqual(action, "git_commit")
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted[0], "abc1234")
        self.assertEqual(extracted[1], "add feature")

    def test_git_commit_without_output(self):
        action, extracted = detect_tool_action("git commit -m 'msg'", "")
        self.assertEqual(action, "git_commit")
        self.assertIsNone(extracted)

    def test_git_push_with_output(self):
        command = "git push origin main"
        output = "aaa1111..bbb2222 main -> origin/main"
        action, extracted = detect_tool_action(command, output)
        self.assertEqual(action, "git_push")
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted[0], "aaa1111")
        self.assertEqual(extracted[1], "bbb2222")
        self.assertEqual(extracted[2], "origin/main")

    def test_npm_install_with_output(self):
        command = "npm install lodash"
        output = "added 5 packages in 2s"
        action, extracted = detect_tool_action(command, output)
        self.assertEqual(action, "dependency_install")
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted[0], "5")

    def test_pip_install_with_output(self):
        command = "pip install requests"
        output = "Successfully installed requests-2.31.0 urllib3-2.0.4"
        action, extracted = detect_tool_action(command, output)
        self.assertEqual(action, "dependency_install")
        self.assertIsNotNone(extracted)

    def test_yarn_install(self):
        action, _ = detect_tool_action("yarn install", "")
        self.assertEqual(action, "dependency_install")

    def test_unrecognized_command(self):
        action, extracted = detect_tool_action("ls -la", "total 100")
        self.assertIsNone(action)
        self.assertIsNone(extracted)

    def test_unrecognized_python_command(self):
        action, extracted = detect_tool_action("python3 app.py", "server started")
        self.assertIsNone(action)
        self.assertIsNone(extracted)


class TestRequireHookMemorySignature(unittest.TestCase):
    """require_hook_memory 装饰器应产生无参 wrapper。"""

    def test_wrapper_is_zero_arg(self):
        from service.config import require_hook_memory
        import inspect

        @require_hook_memory()
        def dummy(event, project_path):
            pass

        sig = inspect.signature(dummy)
        self.assertEqual(len(sig.parameters), 0, "wrapper 应为无参函数")

    def test_wrapper_preserves_name(self):
        from service.config import require_hook_memory

        @require_hook_memory()
        def my_hook_main(event, project_path):
            """Hook docstring."""
            pass

        self.assertEqual(my_hook_main.__name__, "my_hook_main")
        self.assertEqual(my_hook_main.__doc__, "Hook docstring.")

    def test_wrapper_no_wrapped_attr(self):
        """不设置 __wrapped__ 以避免 inspect.signature 穿透到原函数签名。"""
        from service.config import require_hook_memory

        @require_hook_memory()
        def another(event, project_path):
            pass

        self.assertFalse(hasattr(another, "__wrapped__"))


class TestAuditToolUseIntegration(IsolatedWorkspaceCase):
    """audit_tool_use 主流程集成测试（使用隔离工作区）。"""

    def _run_audit(self, event_data):
        from test_common import run_script
        return run_script(
            "service/hooks/audit_tool_use.py",
            self.workspace,
            stdin_data=json.dumps(event_data),
        )

    def test_non_shell_tool_skipped(self):
        result = self._run_audit({
            "projectPath": self.workspace,
            "tool_name": "Read",
            "tool_input": {"path": "/tmp/x"},
        })
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout.strip())
        self.assertEqual(out, {})

    def test_memory_script_skipped(self):
        result = self._run_audit({
            "projectPath": self.workspace,
            "tool_name": "Shell",
            "tool_input": json.dumps({"command": "python3 save_fact.py --content 'x'"}),
        })
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout.strip())
        self.assertEqual(out, {})

    def test_unrecognized_command_skipped(self):
        result = self._run_audit({
            "projectPath": self.workspace,
            "tool_name": "Shell",
            "tool_input": json.dumps({"command": "ls -la"}),
        })
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout.strip())
        self.assertEqual(out, {})

    def test_git_commit_captured(self):
        result = self._run_audit({
            "projectPath": self.workspace,
            "tool_name": "Shell",
            "tool_input": json.dumps({"command": "git commit -m 'init'"}),
            "tool_output": "[main abc1234] init\n 1 file changed",
        })
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout.strip())
        self.assertEqual(out, {})

        from core.utils import today_str
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        self.assertTrue(daily_file.exists(), "应创建 daily 日志文件")
        lines = daily_file.read_text(encoding="utf-8").strip().split("\n")
        entry = json.loads(lines[-1])
        self.assertEqual(entry["action"], "git_commit")
        self.assertIn("abc1234", entry.get("extracted", []))


if __name__ == "__main__":
    unittest.main()
