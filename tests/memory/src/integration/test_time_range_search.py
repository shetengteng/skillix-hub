#!/usr/bin/env python3
"""时间范围搜索与导出测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import sqlite3
import struct
from datetime import datetime, timedelta

from test_common import IsolatedWorkspaceCase, run_script
from storage.sqlite_store import SQLiteStore
from storage.sqlite_search import search_fts, search_vector, hybrid_search, _build_time_filter


class TestBuildTimeFilter(IsolatedWorkspaceCase):
    def test_no_filters(self):
        conds, params = _build_time_filter()
        self.assertEqual(conds, [])
        self.assertEqual(params, [])

    def test_days_filter(self):
        conds, params = _build_time_filter(days=7)
        self.assertEqual(len(conds), 1)
        self.assertIn("c.timestamp >= ?", conds[0])
        self.assertEqual(len(params), 1)

    def test_from_date_filter(self):
        conds, params = _build_time_filter(from_date="2026-02-01")
        self.assertEqual(len(conds), 1)
        self.assertEqual(params[0], "2026-02-01T00:00:00")

    def test_to_date_filter(self):
        conds, params = _build_time_filter(to_date="2026-02-28")
        self.assertEqual(len(conds), 1)
        self.assertEqual(params[0], "2026-02-28T23:59:59")

    def test_combined_filters(self):
        conds, params = _build_time_filter(from_date="2026-01-01", to_date="2026-01-31")
        self.assertEqual(len(conds), 2)
        self.assertEqual(len(params), 2)


class TestSearchWithTimeFilter(IsolatedWorkspaceCase):
    """在 SQLite 中插入不同时间的数据，验证时间过滤搜索。"""

    def _setup_index(self):
        save_old = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "old_fact_token", "--type", "W"],
        )
        self.assertEqual(save_old.returncode, 0, msg=save_old.stderr)

        save_new = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "new_fact_token", "--type", "W"],
        )
        self.assertEqual(save_new.returncode, 0, msg=save_new.stderr)

        sync = run_script("service/memory/sync_index.py", self.workspace, args=["--project-path", self.workspace])
        self.assertEqual(sync.returncode, 0, msg=sync.stderr)

        db_path = str(self.memory_dir / "index.sqlite")
        conn = sqlite3.connect(db_path)
        old_ts = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute("UPDATE chunks SET timestamp = ? WHERE content LIKE '%old_fact_token%'", (old_ts,))
        conn.commit()
        conn.close()
        return db_path

    def test_fts_with_days_filter(self):
        db_path = self._setup_index()
        store = SQLiteStore(db_path)
        try:
            all_results = search_fts(store, "fact_token", limit=10)
            self.assertGreaterEqual(len(all_results), 2)

            recent = search_fts(store, "fact_token", limit=10, days=30)
            self.assertGreaterEqual(len(recent), 1)
            for r in recent:
                self.assertNotIn("old_fact_token", r.get("content", ""))
        finally:
            store.close()

    def test_fts_with_date_range(self):
        db_path = self._setup_index()
        store = SQLiteStore(db_path)
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            results = search_fts(store, "fact_token", limit=10, from_date=today, to_date=today)
            for r in results:
                self.assertNotIn("old_fact_token", r.get("content", ""))
        finally:
            store.close()

    def test_hybrid_with_days_filter(self):
        db_path = self._setup_index()
        store = SQLiteStore(db_path)
        try:
            recent = hybrid_search(store, "fact_token", limit=10, days=30)
            for r in recent:
                self.assertNotIn("old_fact_token", r.get("content", ""))
        finally:
            store.close()


class TestSearchMemoryScriptTimeArgs(IsolatedWorkspaceCase):
    """测试 search_memory.py 脚本的时间参数。"""

    def test_search_with_days_arg(self):
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "time_test_token", "--type", "W"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)
        sync = run_script("service/memory/sync_index.py", self.workspace, args=["--project-path", self.workspace])
        self.assertEqual(sync.returncode, 0, msg=sync.stderr)

        result = run_script(
            "service/memory/search_memory.py",
            self.workspace,
            args=["time_test_token", "--method", "fts", "--days", "7", "--project-path", self.workspace],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        out = json.loads(result.stdout)
        self.assertGreater(out.get("total", 0), 0)

    def test_search_with_date_range_no_results(self):
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "range_test_token", "--type", "W"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)
        sync = run_script("service/memory/sync_index.py", self.workspace, args=["--project-path", self.workspace])
        self.assertEqual(sync.returncode, 0, msg=sync.stderr)

        result = run_script(
            "service/memory/search_memory.py",
            self.workspace,
            args=["range_test_token", "--method", "fts", "--from", "2020-01-01", "--to", "2020-01-31",
                  "--project-path", self.workspace],
        )
        self.assertIn(result.returncode, (0, 1))
        out = json.loads(result.stdout)
        self.assertEqual(out.get("total", 0), 0)


class TestExportWithTimeFilter(IsolatedWorkspaceCase):
    """测试 manage export 命令的时间过滤。"""

    def test_export_with_days(self):
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "export_time_token", "--type", "W"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)

        result = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "export", "--days", "7"],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        out = json.loads(result.stdout)
        data = out.get("data", out)
        self.assertGreater(data.get("total", 0), 0)

    def test_export_with_old_date_range_empty(self):
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "export_old_token", "--type", "W"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)

        result = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "export", "--from", "2020-01-01", "--to", "2020-01-31"],
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        out = json.loads(result.stdout)
        data = out.get("data", out)
        self.assertEqual(data.get("total", 0), 0)


if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)
