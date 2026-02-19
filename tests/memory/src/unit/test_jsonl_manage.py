#!/usr/bin/env python3
"""storage/jsonl_manage.py 单元测试。"""
import sys
import os
import json
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory-skill", "scripts"))

from storage.jsonl_manage import (
    read_all_entries, filter_entries, soft_delete_entries,
    restore_entries, purge_entries, count_by_type, write_audit_entry,
)


def _write_jsonl(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


class JsonlManageTests(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.daily_dir = os.path.join(self.tmpdir, "daily")
        self.sessions_path = os.path.join(self.tmpdir, "sessions.jsonl")
        os.makedirs(self.daily_dir)

        self.daily_entries = [
            {"id": "f-1", "type": "fact", "content": "Redis缓存", "timestamp": "2026-02-18T10:00:00Z"},
            {"id": "f-2", "type": "fact", "content": "PostgreSQL数据库", "timestamp": "2026-02-18T11:00:00Z"},
            {"id": "f-3", "type": "session_start", "content": "", "timestamp": "2026-02-18T09:00:00Z"},
        ]
        _write_jsonl(os.path.join(self.daily_dir, "2026-02-18.jsonl"), self.daily_entries)

        self.session_entries = [
            {"id": "s-1", "type": "session", "topic": "缓存设计", "summary": "讨论了Redis方案", "timestamp": "2026-02-18T12:00:00Z"},
        ]
        _write_jsonl(self.sessions_path, self.session_entries)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_read_all_entries_daily_scope(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="daily")
        self.assertEqual(len(entries), 3)
        self.assertTrue(all("_source_file" in e for e in entries))

    def test_read_all_entries_sessions_scope(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="sessions")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "s-1")

    def test_read_all_entries_all_scope(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="all")
        self.assertEqual(len(entries), 4)

    def test_filter_by_keyword(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="all")
        filtered = filter_entries(entries, keyword="redis")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "f-1")

    def test_filter_by_id(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="all")
        filtered = filter_entries(entries, entry_id="f-2")
        self.assertEqual(len(filtered), 1)

    def test_filter_by_type(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="daily")
        filtered = filter_entries(entries, entry_type="session_start")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "f-3")

    def test_filter_by_date_range(self):
        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="daily")
        filtered = filter_entries(entries, date_from="2026-02-18", date_to="2026-02-18")
        self.assertEqual(len(filtered), 3)

    def test_soft_delete_marks_entries(self):
        result = soft_delete_entries(self.daily_dir, self.sessions_path, {"f-1", "f-2"})
        self.assertEqual(result["deleted"], 2)
        self.assertIn("2026-02-18.jsonl", result["affected_files"])

        remaining = read_all_entries(self.daily_dir, self.sessions_path, scope="daily", include_deleted=False)
        active_ids = {e["id"] for e in remaining}
        self.assertNotIn("f-1", active_ids)
        self.assertNotIn("f-2", active_ids)
        self.assertIn("f-3", active_ids)

    def test_soft_delete_then_restore(self):
        soft_delete_entries(self.daily_dir, self.sessions_path, {"f-1"})
        result = restore_entries(self.daily_dir, self.sessions_path, {"f-1"})
        self.assertEqual(result["restored"], 1)

        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="daily", include_deleted=False)
        ids = {e["id"] for e in entries}
        self.assertIn("f-1", ids)

    def test_purge_removes_permanently(self):
        result = purge_entries(self.daily_dir, self.sessions_path, {"f-1"})
        self.assertEqual(result["purged"], 1)

        all_entries = read_all_entries(self.daily_dir, self.sessions_path, scope="daily", include_deleted=True)
        ids = {e["id"] for e in all_entries}
        self.assertNotIn("f-1", ids)

    def test_purge_session_entry(self):
        result = purge_entries(self.daily_dir, self.sessions_path, {"s-1"})
        self.assertEqual(result["purged"], 1)

        entries = read_all_entries(self.daily_dir, self.sessions_path, scope="sessions")
        self.assertEqual(len(entries), 0)

    def test_count_by_type(self):
        counts = count_by_type(self.daily_dir, self.sessions_path)
        self.assertIn("fact", counts)
        self.assertEqual(counts["fact"]["active"], 2)
        self.assertEqual(counts["session_start"]["active"], 1)

    def test_count_by_type_with_deleted(self):
        soft_delete_entries(self.daily_dir, self.sessions_path, {"f-1"})
        counts = count_by_type(self.daily_dir, self.sessions_path)
        self.assertEqual(counts["fact"]["deleted"], 1)
        self.assertEqual(counts["fact"]["active"], 1)

    def test_write_audit_entry(self):
        write_audit_entry(self.tmpdir, {"op": "test", "timestamp": "2026-02-18T10:00:00Z"})
        audit_path = os.path.join(self.tmpdir, "audit", "operations.jsonl")
        self.assertTrue(os.path.isfile(audit_path))
        with open(audit_path, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline())
        self.assertEqual(entry["op"], "test")

    def test_include_deleted_flag(self):
        soft_delete_entries(self.daily_dir, self.sessions_path, {"f-1"})
        with_deleted = read_all_entries(self.daily_dir, self.sessions_path, scope="daily", include_deleted=True)
        without_deleted = read_all_entries(self.daily_dir, self.sessions_path, scope="daily", include_deleted=False)
        self.assertEqual(len(with_deleted), 3)
        self.assertEqual(len(without_deleted), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
