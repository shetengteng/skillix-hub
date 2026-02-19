#!/usr/bin/env python3
"""service/memory/save_summary.py 单元测试。"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from test_common import IsolatedWorkspaceCase, run_script


class SaveSummaryTests(IsolatedWorkspaceCase):

    def test_save_summary_creates_sessions_jsonl(self):
        proc = run_script(
            "service/memory/save_summary.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--topic", "缓存设计讨论",
                "--summary", "决定使用Redis Cluster作为缓存方案",
                "--decisions", "Redis Cluster,读写分离",
                "--todos", "部署Redis,配置监控",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")
        self.assertTrue(out["id"].startswith("sum-"))

        sessions_path = self.memory_dir / "sessions.jsonl"
        self.assertTrue(sessions_path.exists())
        with open(sessions_path, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline())
        self.assertEqual(entry["topic"], "缓存设计讨论")
        self.assertEqual(entry["decisions"], ["Redis Cluster", "读写分离"])
        self.assertEqual(entry["todos"], ["部署Redis", "配置监控"])

    def test_save_summary_appends_to_existing(self):
        for i in range(3):
            run_script(
                "service/memory/save_summary.py",
                self.workspace,
                args=[
                    "--project-path", self.workspace,
                    "--topic", f"话题{i}",
                    "--summary", f"摘要{i}",
                ],
            )
        sessions_path = self.memory_dir / "sessions.jsonl"
        with open(sessions_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 3)

    def test_save_summary_empty_decisions_and_todos(self):
        proc = run_script(
            "service/memory/save_summary.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--topic", "简单话题",
                "--summary", "简单摘要",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        sessions_path = self.memory_dir / "sessions.jsonl"
        with open(sessions_path, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline())
        self.assertEqual(entry["decisions"], [])
        self.assertEqual(entry["todos"], [])

    def test_save_summary_requires_topic_and_summary(self):
        proc = run_script(
            "service/memory/save_summary.py",
            self.workspace,
            args=["--project-path", self.workspace, "--topic", "只有话题"],
        )
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
