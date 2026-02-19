#!/usr/bin/env python3
"""Hook 输入输出契约测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json

from test_common import IsolatedWorkspaceCase, run_script


class HookContractTests(IsolatedWorkspaceCase):
    def test_load_memory_returns_additional_context_json(self):
        event = json.dumps(
            {
                "type": "sessionStart",
                "conversation_id": "hook-001",
                "workspace_roots": [self.workspace],
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertIn("additional_context", out)
        self.assertIn("核心记忆", out["additional_context"])

    def test_flush_memory_returns_user_message_contract(self):
        event = json.dumps(
            {
                "type": "preCompact",
                "conversation_id": "hook-002",
                "workspace_roots": [self.workspace],
                "context_usage_percent": 86,
                "message_count": 33,
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/flush_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        msg = out.get("user_message", "")
        self.assertTrue(msg.startswith("[Memory Flush]"))
        self.assertIn("86", msg)
        self.assertIn("33", msg)
        self.assertIn("service/memory/save_fact.py", msg)

    def test_prompt_session_save_completed_returns_followup(self):
        event = json.dumps(
            {
                "type": "stop",
                "conversation_id": "hook-003",
                "workspace_roots": [self.workspace],
                "status": "completed",
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/prompt_session_save.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        msg = out.get("followup_message", "")
        self.assertTrue(msg.startswith("[Session Save]"))
        self.assertIn("service/memory/save_summary.py", msg)

    def test_prompt_session_save_non_completed_returns_empty_json(self):
        event = json.dumps(
            {
                "type": "stop",
                "conversation_id": "hook-004",
                "workspace_roots": [self.workspace],
                "status": "interrupted",
            },
            ensure_ascii=False,
        )
        proc = run_script("service/hooks/prompt_session_save.py", self.workspace, stdin_data=event)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out, {})


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
