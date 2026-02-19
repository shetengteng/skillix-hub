#!/usr/bin/env python3
"""update.py 更新流程测试。"""
import json
import os
import shutil
import subprocess
import sys
import unittest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_TEST_DIR, "..", "..", "..", ".."))
SCRIPTS_DIR = os.path.join(_REPO_ROOT, "skills", "memory", "scripts")
UPDATE_SCRIPT = os.path.join(SCRIPTS_DIR, "service", "init", "update.py")
_TMP_ROOT = os.path.join(_REPO_ROOT, ".test_tmp")


def _run_update(*extra_args):
    cmd = [sys.executable, UPDATE_SCRIPT] + list(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


class UpdatePreConditionTests(unittest.TestCase):
    """update.py 前置条件校验。"""

    def setUp(self):
        self.tmpdir = os.path.join(_TMP_ROOT, "precond")
        os.makedirs(self.tmpdir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_missing_source_dir(self):
        result = _run_update("--source", os.path.join(self.tmpdir, "nope"), "--project-path", self.tmpdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source directory not found", result.stderr)

    def test_skill_not_installed(self):
        source = os.path.join(self.tmpdir, "source")
        os.makedirs(source, exist_ok=True)
        project = os.path.join(self.tmpdir, "project")
        os.makedirs(project, exist_ok=True)
        result = _run_update("--source", source, "--project-path", project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skill not installed", result.stderr)

    def test_requires_source_argument(self):
        result = _run_update("--project-path", self.tmpdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--source", result.stderr)


class UpdateCodeTests(unittest.TestCase):
    """update.py 代码更新逻辑测试。"""

    def setUp(self):
        self.tmpdir = os.path.join(_TMP_ROOT, "code")
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)
        os.makedirs(self.tmpdir, exist_ok=True)
        self.source_dir = os.path.join(self.tmpdir, "source", "memory")
        self.project_dir = os.path.join(self.tmpdir, "project")
        self.skill_install = os.path.join(
            self.project_dir, ".cursor", "skills", "memory",
        )
        self.data_dir = os.path.join(
            self.project_dir, ".cursor", "skills", "memory-data",
        )

        os.makedirs(os.path.join(self.source_dir, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(self.source_dir, "templates"), exist_ok=True)

        with open(os.path.join(self.source_dir, "SKILL.md"), "w") as f:
            f.write("# Memory Skill\nscript: {{SCRIPT_PATH}}\nskill: {{SKILL_PATH}}\ndata: {{MEMORY_DATA_PATH}}")

        with open(os.path.join(self.source_dir, "scripts", "main.py"), "w") as f:
            f.write("# new version\nprint('v2')")

        hooks = {
            "hooks": {
                "sessionStart": [
                    {"command": "python3 {{SKILL_PATH}}/scripts/load.py"}
                ]
            }
        }
        with open(os.path.join(self.source_dir, "templates", "hooks.json"), "w") as f:
            json.dump(hooks, f)

        rules_content = "path: {{SCRIPT_PATH}}\nskill: {{SKILL_PATH}}"
        with open(os.path.join(self.source_dir, "templates", "memory-rules.mdc"), "w") as f:
            f.write(rules_content)

        os.makedirs(self.skill_install, exist_ok=True)
        with open(os.path.join(self.skill_install, "SKILL.md"), "w") as f:
            f.write("# old version")
        os.makedirs(os.path.join(self.skill_install, "scripts"), exist_ok=True)
        with open(os.path.join(self.skill_install, "scripts", "main.py"), "w") as f:
            f.write("# old version\nprint('v1')")

        os.makedirs(self.data_dir, exist_ok=True)
        with open(os.path.join(self.data_dir, "config.json"), "w") as f:
            json.dump({"memory": {"load_days_full": 5}}, f)
        with open(os.path.join(self.data_dir, "MEMORY.md"), "w") as f:
            f.write("# My memories\nuser prefers dark mode")
        with open(os.path.join(self.data_dir, "2026-02-19.jsonl"), "w") as f:
            f.write('{"type":"fact","text":"test"}\n')

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_update_replaces_code(self):
        result = _run_update("--source", self.source_dir, "--project-path", self.project_dir)
        self.assertEqual(result.returncode, 0, result.stderr)

        with open(os.path.join(self.skill_install, "scripts", "main.py")) as f:
            self.assertIn("v2", f.read())

    def test_update_resolves_placeholders_in_skill_md(self):
        result = _run_update("--source", self.source_dir, "--project-path", self.project_dir)
        self.assertEqual(result.returncode, 0, result.stderr)

        with open(os.path.join(self.skill_install, "SKILL.md")) as f:
            content = f.read()
        self.assertNotIn("{{SCRIPT_PATH}}", content)
        self.assertNotIn("{{SKILL_PATH}}", content)
        self.assertNotIn("{{MEMORY_DATA_PATH}}", content)
        self.assertIn(".cursor/skills/memory", content)

    def test_update_preserves_data_directory(self):
        _run_update("--source", self.source_dir, "--project-path", self.project_dir)

        with open(os.path.join(self.data_dir, "config.json")) as f:
            cfg = json.load(f)
        self.assertEqual(cfg["memory"]["load_days_full"], 5)

        with open(os.path.join(self.data_dir, "MEMORY.md")) as f:
            self.assertIn("dark mode", f.read())

        self.assertTrue(os.path.exists(os.path.join(self.data_dir, "2026-02-19.jsonl")))

    def test_update_merges_hooks(self):
        hooks_path = os.path.join(self.project_dir, ".cursor", "hooks.json")
        existing = {
            "hooks": {
                "sessionStart": [
                    {"command": "echo existing"}
                ]
            }
        }
        with open(hooks_path, "w") as f:
            json.dump(existing, f)

        _run_update("--source", self.source_dir, "--project-path", self.project_dir)

        with open(hooks_path) as f:
            merged = json.load(f)
        cmds = [c["command"] for c in merged["hooks"]["sessionStart"]]
        self.assertIn("echo existing", cmds)
        self.assertTrue(any(".cursor/skills/memory" in c for c in cmds))

    def test_update_does_not_duplicate_hooks(self):
        skill_rel = ".cursor/skills/memory"
        hooks_path = os.path.join(self.project_dir, ".cursor", "hooks.json")
        existing = {
            "hooks": {
                "sessionStart": [
                    {"command": f"python3 {skill_rel}/scripts/load.py"}
                ]
            }
        }
        with open(hooks_path, "w") as f:
            json.dump(existing, f)

        _run_update("--source", self.source_dir, "--project-path", self.project_dir)

        with open(hooks_path) as f:
            merged = json.load(f)
        cmds = merged["hooks"]["sessionStart"]
        load_cmds = [c for c in cmds if "load.py" in c["command"]]
        self.assertEqual(len(load_cmds), 1)

    def test_update_installs_rules_with_placeholders_resolved(self):
        _run_update("--source", self.source_dir, "--project-path", self.project_dir)

        rules_path = os.path.join(self.project_dir, ".cursor", "rules", "memory-rules.mdc")
        self.assertTrue(os.path.exists(rules_path))
        with open(rules_path) as f:
            content = f.read()
        self.assertNotIn("{{SCRIPT_PATH}}", content)
        self.assertNotIn("{{SKILL_PATH}}", content)

    def test_update_output_messages(self):
        result = _run_update("--source", self.source_dir, "--project-path", self.project_dir)
        self.assertIn("Updating", result.stdout)
        self.assertIn("updated", result.stdout.lower())
        self.assertIn("Preserved", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
