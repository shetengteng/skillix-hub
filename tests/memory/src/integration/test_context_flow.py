#!/usr/bin/env python3
"""会话上下文生命周期测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import time

from test_common import IsolatedWorkspaceCase, run_script


class DetailContextFlowTests(IsolatedWorkspaceCase):
    def test_lifecycle_session_start_precompact_stop_and_next_session(self):
        # 1) sessionStart
        start_event = json.dumps(
            {"type": "sessionStart", "conversation_id": "ctx-1", "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        load1 = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=start_event)
        self.assertEqual(load1.returncode, 0, msg=load1.stderr)
        out1 = json.loads(load1.stdout)
        self.assertIn("核心记忆", out1.get("additional_context", ""))

        # 2) preCompact
        compact_event = json.dumps(
            {
                "type": "preCompact",
                "conversation_id": "ctx-1",
                "workspace_roots": [self.workspace],
                "context_usage_percent": 88,
                "message_count": 42,
            },
            ensure_ascii=False,
        )
        flush = run_script("service/hooks/flush_memory.py", self.workspace, stdin_data=compact_event)
        self.assertEqual(flush.returncode, 0, msg=flush.stderr)
        out_flush = json.loads(flush.stdout)
        self.assertTrue(out_flush.get("user_message", "").startswith("[Memory Flush]"))

        # 3) 模拟新增事实
        token = f"CTX_FLOW_{int(time.time())}"
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", token, "--type", "W", "--session", "ctx-1"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)

        # 4) stop — session already has fact data, so followup_message should be skipped
        stop_event = json.dumps(
            {"type": "stop", "conversation_id": "ctx-1", "workspace_roots": [self.workspace], "status": "completed"},
            ensure_ascii=False,
        )
        stop = run_script("service/hooks/prompt_session_save.py", self.workspace, stdin_data=stop_event)
        self.assertEqual(stop.returncode, 0, msg=stop.stderr)
        out_stop = json.loads(stop.stdout)
        self.assertEqual(out_stop.get("followup_message", ""), "",
                         "stop hook should skip [Session Save] when session already has fact data")

        # 5) 下一个会话可见新增事实
        start_event_2 = json.dumps(
            {"type": "sessionStart", "conversation_id": "ctx-2", "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        load2 = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=start_event_2)
        self.assertEqual(load2.returncode, 0, msg=load2.stderr)
        out2 = json.loads(load2.stdout)
        self.assertIn(token, out2.get("additional_context", ""))


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
