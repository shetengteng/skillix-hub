#!/usr/bin/env python3
"""已知缺陷回归测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import time
from datetime import datetime, timedelta, timezone

from test_common import IsolatedWorkspaceCase, run_script
from storage.jsonl import _apply_decay
from core.utils import ts_id


class DetailRegressionTests(IsolatedWorkspaceCase):
    def test_fact_recall_pipeline(self):
        token = f"RECALL_TOKEN_{int(time.time() * 1000)}"
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", token, "--type", "W", "--entities", "recall-test"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)

        event = json.dumps(
            {"type": "sessionStart", "conversation_id": "reg-1", "workspace_roots": [self.workspace]},
            ensure_ascii=False,
        )
        load = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(load.returncode, 0, msg=load.stderr)
        out = json.loads(load.stdout)
        self.assertIn(token, out.get("additional_context", ""))

    def test_decay_prefers_newest_partial_window(self):
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)
        entries = []
        for i in range(6):
            entries.append(
                {
                    "content": f"fact-{i + 1}",
                    "memory_type": "W",
                    "timestamp": (three_days_ago + timedelta(minutes=i * 10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "confidence": 0.8,
                }
            )
        result = _apply_decay(entries)
        contents = [e["content"] for e in result]
        self.assertIn("fact-6", contents)
        self.assertNotEqual(contents, ["fact-1", "fact-2", "fact-3"])

    def test_ts_id_high_frequency_uniqueness(self):
        values = [ts_id() for _ in range(200)]
        self.assertEqual(len(values), len(set(values)))


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
