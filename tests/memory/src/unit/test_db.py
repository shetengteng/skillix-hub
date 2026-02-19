#!/usr/bin/env python3
"""db 子命令测试：tables / stats / schema / show / query"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import unittest

from test_common import IsolatedWorkspaceCase, run_script


class DbCommandTests(IsolatedWorkspaceCase):
    def _run_init(self):
        proc = run_script(
            "service/init/index.py",
            self.workspace,
            args=["--skip-model", "--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

    def _save_facts(self, count=3):
        for i in range(count):
            proc = run_script(
                "service/memory/save_fact.py",
                self.workspace,
                args=[
                    "--project-path", self.workspace,
                    "--content", f"测试事实 {i}",
                    "--type", "W",
                    "--entities", f"entity_{i}",
                ],
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

    def _sync_index(self):
        proc = run_script(
            "service/memory/sync_index.py",
            self.workspace,
            args=["--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

    def _run_db(self, action, extra_args=None):
        args = ["--project-path", self.workspace, "db", action]
        if extra_args:
            args.extend(extra_args)
        return run_script("service/manage/index.py", self.workspace, args=args)

    def test_db_tables_after_init(self):
        self._run_init()
        self._save_facts(1)
        self._sync_index()
        proc = self._run_db("tables")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        table_names = [t["name"] for t in out["data"]["tables"]]
        self.assertIn("chunks", table_names)
        self.assertIn("meta", table_names)
        self.assertIn("sync_state", table_names)

    def test_db_stats_shows_counts(self):
        self._run_init()
        self._save_facts(3)
        self._sync_index()
        proc = self._run_db("stats")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        data = out["data"]
        self.assertGreater(data["total_chunks"], 0)
        self.assertIn("by_type", data)
        self.assertIn("file_size_kb", data)

    def test_db_schema_chunks(self):
        self._run_init()
        self._save_facts(1)
        self._sync_index()
        proc = self._run_db("schema", ["chunks"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        col_names = [c["name"] for c in out["data"]["columns"]]
        self.assertIn("id", col_names)
        self.assertIn("content", col_names)
        self.assertIn("embedding", col_names)

    def test_db_schema_nonexistent_table(self):
        self._run_init()
        self._save_facts(1)
        self._sync_index()
        proc = self._run_db("schema", ["nonexistent_table"])
        self.assertEqual(proc.returncode, 2)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "error")

    def test_db_show_chunks_with_limit(self):
        self._run_init()
        self._save_facts(5)
        self._sync_index()
        proc = self._run_db("show", ["chunks", "--limit", "2"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertLessEqual(len(out["data"]["rows"]), 2)
        self.assertGreater(out["data"]["total"], 0)
        for row in out["data"]["rows"]:
            if row.get("embedding"):
                self.assertTrue(row["embedding"].startswith("<blob"))

    def test_db_show_meta(self):
        self._run_init()
        self._save_facts(1)
        self._sync_index()
        proc = self._run_db("show", ["meta"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        keys = [r["key"] for r in out["data"]["rows"]]
        self.assertIn("schema_version", keys)

    def test_db_query_select(self):
        self._run_init()
        self._save_facts(2)
        self._sync_index()
        proc = self._run_db("query", ["SELECT id, content, type FROM chunks LIMIT 5"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertGreater(out["data"]["count"], 0)

    def test_db_query_rejects_write(self):
        self._run_init()
        self._save_facts(1)
        self._sync_index()
        proc = self._run_db("query", ["DELETE FROM chunks"])
        self.assertEqual(proc.returncode, 2)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["error"]["code"], "READONLY")

    def test_db_no_database_file(self):
        self._run_init()
        proc = self._run_db("tables")
        self.assertEqual(proc.returncode, 2)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "error")
        self.assertEqual(out["error"]["code"], "DB_NOT_FOUND")


if __name__ == "__main__":
    unittest.main(verbosity=2)
