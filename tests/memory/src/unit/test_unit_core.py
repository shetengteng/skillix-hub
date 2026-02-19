#!/usr/bin/env python3
"""核心单元行为测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
from datetime import datetime, timedelta, timezone

from test_common import IsolatedWorkspaceCase, run_script
from storage.jsonl import read_recent_facts


class UnitBehaviorTests(IsolatedWorkspaceCase):
    def test_partial_window_prefers_latest_entries(self):
        facts_path = self.memory_dir / "facts.jsonl"
        base_day = datetime.now(timezone.utc) - timedelta(days=3)
        rows = []
        for i in range(5):
            ts = (
                base_day.replace(hour=10, minute=0, second=0, microsecond=0)
                + timedelta(minutes=i)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            rows.append(
                {
                    "id": f"fact-{i + 1}",
                    "type": "fact",
                    "memory_type": "W",
                    "content": f"item-{i + 1}",
                    "confidence": 0.9,
                    "timestamp": ts,
                }
            )

        with facts_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        selected = read_recent_facts(str(facts_path))
        selected_ids = [r["id"] for r in selected]
        self.assertEqual(selected_ids, ["fact-5", "fact-4", "fact-3"])

    def test_save_fact_cli_output_schema(self):
        token = "UNIT_SCHEMA_TOKEN"
        proc = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "--content",
                token,
                "--type",
                "W",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload.get("status"), "ok")
        self.assertTrue(str(payload.get("id", "")).startswith("log-"))


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
