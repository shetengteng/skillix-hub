#!/usr/bin/env python3
"""JSONL 读写测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
from datetime import datetime, timedelta, timezone

from test_common import IsolatedWorkspaceCase
from storage.jsonl import read_jsonl, read_last_entry, read_recent_facts


class DetailJsonlTests(IsolatedWorkspaceCase):
    def test_read_jsonl_and_last_entry(self):
        facts_path = self.memory_dir / "facts.jsonl"
        rows = [
            {"id": "f-1", "type": "fact", "memory_type": "W", "content": "A", "confidence": 1.0, "timestamp": "2026-02-19T00:00:00Z"},
            {"id": "f-2", "type": "fact", "memory_type": "O", "content": "B", "confidence": 0.8, "timestamp": "2026-02-19T00:01:00Z"},
        ]
        with facts_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        got = read_jsonl(str(facts_path))
        self.assertEqual(len(got), 2)
        last = read_last_entry(str(facts_path))
        self.assertIsInstance(last, dict)
        self.assertEqual(last["id"], "f-2")

    def test_read_recent_facts_respects_recent_order(self):
        facts_path = self.memory_dir / "facts.jsonl"
        base = datetime.now(timezone.utc) - timedelta(days=1)
        with facts_path.open("w", encoding="utf-8") as f:
            for i in range(6):
                row = {
                    "id": f"f-{i}",
                    "type": "fact",
                    "memory_type": "W",
                    "content": f"item-{i}",
                    "confidence": 0.9,
                    "timestamp": (base + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        got = read_recent_facts(str(facts_path))
        self.assertGreaterEqual(len(got), 1)
        self.assertEqual(got[0]["id"], "f-5")

    def test_nonexistent_file_fallbacks(self):
        miss = self.memory_dir / "missing.jsonl"
        self.assertEqual(read_jsonl(str(miss)), [])
        self.assertIsNone(read_last_entry(str(miss)))


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
