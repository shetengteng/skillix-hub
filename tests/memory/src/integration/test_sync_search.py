#!/usr/bin/env python3
"""同步索引与搜索测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json

from test_common import IsolatedWorkspaceCase, run_script
from storage.sqlite_store import SQLiteStore


class DetailSyncAndSearchTests(IsolatedWorkspaceCase):
    def test_sync_index_build_incremental_rebuild(self):
        token = "DETAIL_SYNC_TOKEN"
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", token, "--type", "W"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)

        sync1 = run_script("service/memory/sync_index.py", self.workspace, args=["--project-path", self.workspace])
        self.assertEqual(sync1.returncode, 0, msg=sync1.stderr)

        db_path = self.memory_dir / "index.sqlite"
        self.assertTrue(db_path.exists())
        store = SQLiteStore(str(db_path))
        try:
            count1 = store.count_chunks()
            self.assertGreater(count1, 0)
            self.assertGreaterEqual(len(store.search_fts(token, limit=5)), 1)
        finally:
            store.close()

        sync2 = run_script("service/memory/sync_index.py", self.workspace, args=["--project-path", self.workspace])
        self.assertEqual(sync2.returncode, 0, msg=sync2.stderr)
        store2 = SQLiteStore(str(db_path))
        try:
            self.assertEqual(store2.count_chunks(), count1)
        finally:
            store2.close()

        rebuild = run_script("service/memory/sync_index.py", self.workspace, args=["--rebuild", "--project-path", self.workspace])
        self.assertEqual(rebuild.returncode, 0, msg=rebuild.stderr)

    def test_search_memory_fts_hybrid_and_missing_index(self):
        token = "DETAIL_SEARCH_TOKEN"
        save = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", token, "--type", "W"],
        )
        self.assertEqual(save.returncode, 0, msg=save.stderr)
        sync = run_script("service/memory/sync_index.py", self.workspace, args=["--project-path", self.workspace])
        self.assertEqual(sync.returncode, 0, msg=sync.stderr)

        fts = run_script(
            "service/memory/search_memory.py",
            self.workspace,
            args=[token, "--method", "fts", "--project-path", self.workspace],
        )
        self.assertEqual(fts.returncode, 0, msg=fts.stderr)
        out_fts = json.loads(fts.stdout)
        self.assertEqual(out_fts.get("method"), "fts")
        self.assertGreater(out_fts.get("total", 0), 0)

        hyb = run_script(
            "service/memory/search_memory.py",
            self.workspace,
            args=["数据库", "--method", "hybrid", "--project-path", self.workspace],
        )
        self.assertIn(hyb.returncode, (0, 1), msg=hyb.stderr)
        out_hyb = json.loads(hyb.stdout)
        self.assertIn(out_hyb.get("method"), ("hybrid", "fts"))

        missing = run_script(
            "service/memory/search_memory.py",
            self.workspace,
            args=["x", "--project-path", self.workspace + "-not-exist"],
        )
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
