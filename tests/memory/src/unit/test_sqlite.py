#!/usr/bin/env python3
"""SQLite 存储测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pathlib import Path

from test_common import IsolatedWorkspaceCase
from storage.sqlite_store import SQLiteStore
from storage.sqlite_search import cosine_similarity


class DetailSqliteTests(IsolatedWorkspaceCase):
    def test_upsert_fts_meta_sync_state(self):
        db_path = Path(self.workspace) / "detail.sqlite"
        store = SQLiteStore(str(db_path))
        try:
            store.upsert_chunk("k1", "Hello world", chunk_type="fact", memory_type="W", confidence=0.9, timestamp="2026-02-19T00:00:00Z")
            self.assertEqual(store.count_chunks(), 1)
            store.upsert_chunk("k1", "Hello updated", chunk_type="fact", memory_type="W", confidence=0.95, timestamp="2026-02-19T00:01:00Z")
            self.assertEqual(store.count_chunks(), 1)

            self.assertGreaterEqual(len(store.search_fts("Hello", limit=5)), 1)
            self.assertEqual(len(store.search_fts("zzz-not-found", limit=5)), 0)

            store.set_meta("alpha", "beta")
            self.assertEqual(store.get_meta("alpha"), "beta")
            self.assertEqual(store.get_meta("schema_version"), "1")

            store.update_sync_state("daily/2026-02-19.jsonl", 10, "k1", 123456)
            state = store.get_sync_state("daily/2026-02-19.jsonl")
            self.assertIsNotNone(state)
            self.assertEqual(state["last_line"], 10)
        finally:
            store.close()

    def test_cosine_similarity_edges(self):
        self.assertAlmostEqual(cosine_similarity([1, 0, 0], [1, 0, 0]), 1.0, places=3)
        self.assertAlmostEqual(cosine_similarity([1, 0, 0], [0, 1, 0]), 0.0, places=3)
        self.assertAlmostEqual(cosine_similarity([1, 0, 0], [-1, 0, 0]), -1.0, places=3)


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
