#!/usr/bin/env python3
"""端到端链路测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import uuid

from test_common import IsolatedWorkspaceCase, run_script


class E2EFlowTests(IsolatedWorkspaceCase):
    def test_saved_daily_fact_loaded_by_session_start(self):
        token = f"E2E_DAILY_ONLY_{uuid.uuid4().hex[:10]}"
        proc_save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "--content",
                token,
                "--type",
                "W",
                "--session",
                "e2e-flow-1",
            ],
        )
        self.assertEqual(proc_save.returncode, 0, msg=proc_save.stderr)

        event = json.dumps(
            {
                "type": "sessionStart",
                "conversation_id": "e2e-flow-1",
                "workspace_roots": [self.workspace],
            },
            ensure_ascii=False,
        )
        proc_load = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(proc_load.returncode, 0, msg=proc_load.stderr)
        out = json.loads(proc_load.stdout)
        self.assertIn(token, out.get("additional_context", ""))

    def test_session_end_sync_makes_new_fact_searchable(self):
        token = f"E2E_END_SYNC_{uuid.uuid4().hex[:10]}"

        proc_save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "--content",
                token,
                "--type",
                "W",
                "--session",
                "e2e-flow-2",
            ],
        )
        self.assertEqual(proc_save.returncode, 0, msg=proc_save.stderr)

        end_event = json.dumps(
            {
                "type": "sessionEnd",
                "conversation_id": "e2e-flow-2",
                "workspace_roots": [self.workspace],
                "reason": "completed",
                "duration_ms": 1000,
            },
            ensure_ascii=False,
        )
        proc_end = run_script("service/hooks/sync_and_cleanup.py", self.workspace, stdin_data=end_event)
        self.assertEqual(proc_end.returncode, 0, msg=proc_end.stderr)

        proc_before = run_script(
            "service/memory/search_memory.py",
            self.workspace,
            args=[token, "--method", "fts", "--project-path", self.workspace],
        )
        out = json.loads(proc_before.stdout)
        self.assertEqual(proc_before.returncode, 0, msg=proc_before.stderr)
        self.assertGreaterEqual(out.get("total", 0), 1, msg=proc_before.stdout)


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
