#!/usr/bin/env python3
"""安装路径逻辑测试。"""
import os
import unittest


class InstallPathLogicTests(unittest.TestCase):
    def test_global_relative_path_depends_on_project_depth(self):
        skill_install_dir = os.path.expanduser("~/.cursor/skills/memory-skill")
        p1 = "/Users/TerrellShe/Documents/personal/clawd.bot"
        p2 = "/Users/TerrellShe/work/demo"
        p3 = "/Users/TerrellShe/dev"

        r1 = os.path.relpath(skill_install_dir, p1)
        r2 = os.path.relpath(skill_install_dir, p2)
        r3 = os.path.relpath(skill_install_dir, p3)

        self.assertNotEqual(r1, r2)
        self.assertNotEqual(r2, r3)
        self.assertNotEqual(r1, r3)

    def test_local_mode_relative_path_is_stable(self):
        project = "/tmp/sample-project"
        local_skill = os.path.join(project, ".cursor", "skills", "memory-skill")
        rel = os.path.relpath(local_skill, project)
        self.assertEqual(rel, ".cursor/skills/memory-skill")


if __name__ == "__main__":
    unittest.main(verbosity=2)
