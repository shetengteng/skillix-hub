#!/usr/bin/env python3
"""manage 命令端到端测试：通过 CLI 调用 manage/index.py 验证各子命令。"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from test_common import IsolatedWorkspaceCase, run_script


class ManageListStatsTests(IsolatedWorkspaceCase):

    def _seed_facts(self, count=3):
        for i in range(count):
            run_script(
                "service/memory/save_fact.py",
                self.workspace,
                args=["--project-path", self.workspace, "--content", f"事实{i}", "--type", "W"],
            )

    def test_list_returns_json_with_records(self):
        self._seed_facts(2)
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "list", "--scope", "daily"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["data"]["total"], 2)
        self.assertEqual(len(out["data"]["records"]), 2)

    def test_list_with_keyword_filter(self):
        self._seed_facts()
        run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "Redis缓存方案", "--type", "W"],
        )
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "list", "--keyword", "Redis"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertGreaterEqual(out["data"]["total"], 1)

    def test_list_pagination(self):
        self._seed_facts(5)
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "list", "--limit", "2", "--offset", "0"],
        )
        out = json.loads(proc.stdout)
        self.assertEqual(len(out["data"]["records"]), 2)
        self.assertEqual(out["data"]["total"], 5)

    def test_stats_returns_disk_and_daily_info(self):
        self._seed_facts(2)
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "stats"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertIn("disk_usage_kb", out["data"])
        self.assertIn("daily", out["data"])
        self.assertGreater(out["data"]["daily"]["total"], 0)


class ManageDeleteRestoreTests(IsolatedWorkspaceCase):

    def _seed_and_get_id(self):
        proc = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "待删除事实", "--type", "W"],
        )
        return json.loads(proc.stdout)["id"]

    def test_delete_preview_without_confirm(self):
        fact_id = self._seed_and_get_id()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "delete", "--id", fact_id, "--no-sync"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "preview")
        self.assertEqual(out["data"]["total"], 1)

    def test_delete_soft_with_confirm(self):
        fact_id = self._seed_and_get_id()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "delete", "--id", fact_id, "--confirm", "--no-sync"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["data"]["deleted"], 1)
        self.assertEqual(out["data"]["mode"], "soft")

    def test_delete_then_restore_by_id(self):
        fact_id = self._seed_and_get_id()
        run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "delete", "--id", fact_id, "--confirm", "--no-sync"],
        )
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "restore", "--id", fact_id, "--no-sync"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["data"]["restored"], 1)

    def test_delete_purge_removes_permanently(self):
        fact_id = self._seed_and_get_id()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "delete", "--id", fact_id, "--confirm", "--purge", "--no-sync"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["data"]["mode"], "purge")

        proc_list = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "list", "--id", fact_id],
        )
        list_out = json.loads(proc_list.stdout)
        self.assertEqual(list_out["data"]["total"], 0)

    def test_delete_no_match_returns_zero(self):
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "delete", "--id", "nonexistent-id", "--no-sync"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["data"]["total"], 0)


class ManageEditExportTests(IsolatedWorkspaceCase):

    def _seed_and_get_id(self):
        proc = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "原始内容", "--type", "W"],
        )
        return json.loads(proc.stdout)["id"]

    def test_edit_content(self):
        fact_id = self._seed_and_get_id()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "edit", "--id", fact_id, "--content", "修改后内容", "--no-sync"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertIn("content", out["data"]["updated_fields"])

    def test_edit_without_id_fails(self):
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "edit", "--content", "无ID", "--no-sync"],
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_export_returns_records(self):
        self._seed_and_get_id()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "export"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertIn("records", out["data"])
        self.assertGreater(out["data"]["total"], 0)

    def test_export_to_file(self):
        self._seed_and_get_id()
        output_path = os.path.join(self.workspace, "export.json")
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "export", "--output", output_path],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertTrue(os.path.isfile(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("records", data)


class ManageIndexDoctorTests(IsolatedWorkspaceCase):

    def test_doctor_returns_checks(self):
        run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "诊断测试", "--type", "W"],
        )
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=["--project-path", self.workspace, "doctor"],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertIn("checks", out["data"])
        self.assertIn("summary", out["data"])
        check_names = [c["name"] for c in out["data"]["checks"]]
        self.assertIn("JSONL 可解析性", check_names)
        self.assertIn("ID 唯一性", check_names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
