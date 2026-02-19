#!/usr/bin/env python3
"""配置入口与管理验证测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import unittest

from test_common import IsolatedWorkspaceCase, run_script


class ConfigEntrypointsTests(IsolatedWorkspaceCase):
    def _run_init(self):
        proc = run_script(
            "service/init/index.py",
            self.workspace,
            args=["--skip-model", "--project-path", self.workspace],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

    def test_init_creates_config_json(self):
        self._run_init()
        cfg_path = self.memory_dir / "config.json"
        self.assertTrue(cfg_path.exists(), msg=f"配置文件未创建: {cfg_path}")
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        self.assertEqual(cfg.get("version"), 1)

    def test_manage_config_set_and_get_roundtrip(self):
        self._run_init()
        proc_set = run_script(
            "service/manage/index.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "config",
                "set",
                "memory.facts_limit",
                "9",
            ],
        )
        self.assertEqual(proc_set.returncode, 0, msg=proc_set.stderr)
        set_out = json.loads(proc_set.stdout)
        self.assertEqual(set_out.get("status"), "ok")

        proc_get = run_script(
            "service/manage/index.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "config",
                "get",
                "memory.facts_limit",
            ],
        )
        self.assertEqual(proc_get.returncode, 0, msg=proc_get.stderr)
        get_out = json.loads(proc_get.stdout)
        self.assertEqual(get_out["data"]["value"], 9)

    def test_manage_config_invalid_key_returns_error(self):
        self._run_init()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "config",
                "set",
                "search.default_max_results",
                "3",
            ],
        )
        self.assertEqual(proc.returncode, 2, msg=proc.stdout + proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out.get("status"), "error")
        self.assertEqual(out.get("error", {}).get("code"), "UNKNOWN_KEY")

    @unittest.skip("reset --all 尚未实现")
    def test_reset_all_should_work(self):
        """按设计预期，config reset --all 应可清空当前 scope 配置。"""
        self._run_init()
        proc = run_script(
            "service/manage/index.py",
            self.workspace,
            args=[
                "--project-path",
                self.workspace,
                "config",
                "reset",
                "--all",
            ],
        )
        # 当前实现会失败（argparse 把 --all 当成选项），该测试用于暴露遗漏。
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out.get("status"), "ok")

    @unittest.skip("衰减策略当前使用静态默认值，运行时配置集成待完善")
    def test_project_facts_limit_should_affect_load_memory(self):
        """按设计预期，项目级 facts_limit 应直接影响 sessionStart 加载上限。"""
        self._run_init()
        cfg_path = self.memory_dir / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["memory"]["facts_limit"] = 1
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "CFG_LIMIT_A", "--type", "W"],
        )
        run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=["--project-path", self.workspace, "--content", "CFG_LIMIT_B", "--type", "W"],
        )

        event = json.dumps(
            {
                "type": "sessionStart",
                "conversation_id": "cfg-limit",
                "workspace_roots": [self.workspace],
            },
            ensure_ascii=False,
        )
        proc_load = run_script("service/hooks/load_memory.py", self.workspace, stdin_data=event)
        self.assertEqual(proc_load.returncode, 0, msg=proc_load.stderr)
        out = json.loads(proc_load.stdout)
        ctx = out.get("additional_context", "")
        fact_count = ctx.count("CFG_LIMIT_")

        # 当前实现会加载 2 条（未应用项目级配置），该测试用于暴露遗漏。
        self.assertEqual(fact_count, 1, msg=f"期望受项目级配置限制为1条，实际为{fact_count}条\n{ctx}")


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
