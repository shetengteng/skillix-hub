#!/usr/bin/env python3
"""distill_refined.py 单元测试"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.memory.distill_refined import build_memory_md
from service.memory.session_state import read_session_state


class TestBuildMemoryMd(unittest.TestCase):

    def test_basic_structure(self):
        sections = {
            "用户偏好": ["中文回答", "commit message 用英文"],
            "项目背景": ["语义元数据管理系统"],
        }
        md = build_memory_md(sections)
        self.assertIn("# 核心记忆", md)
        self.assertIn("## 用户偏好", md)
        self.assertIn("- 中文回答", md)
        self.assertIn("- commit message 用英文", md)
        self.assertIn("## 项目背景", md)
        self.assertIn("- 语义元数据管理系统", md)

    def test_section_order(self):
        sections = {
            "常用工具": ["memory"],
            "用户偏好": ["中文"],
            "重要决策": ["用 Redis"],
        }
        md = build_memory_md(sections)
        pref_pos = md.index("## 用户偏好")
        dec_pos = md.index("## 重要决策")
        tool_pos = md.index("## 常用工具")
        self.assertLess(pref_pos, dec_pos)
        self.assertLess(dec_pos, tool_pos)

    def test_empty_sections_included(self):
        sections = {"用户偏好": [], "项目背景": ["内容"]}
        md = build_memory_md(sections)
        self.assertIn("## 用户偏好", md)
        self.assertIn("## 项目背景", md)

    def test_custom_section_appended(self):
        sections = {
            "用户偏好": ["中文"],
            "自定义章节": ["自定义内容"],
        }
        md = build_memory_md(sections)
        self.assertIn("## 自定义章节", md)
        self.assertIn("- 自定义内容", md)

    def test_strips_item_whitespace(self):
        sections = {"用户偏好": ["  中文回答  ", "  英文 commit  "]}
        md = build_memory_md(sections)
        self.assertIn("- 中文回答", md)
        self.assertIn("- 英文 commit", md)
        self.assertNotIn("-   ", md)

    def test_all_standard_sections_present(self):
        sections = {
            "用户偏好": ["a"],
            "项目背景": ["b"],
            "项目规范": ["c"],
            "重要决策": ["d"],
            "常用工具": ["e"],
        }
        md = build_memory_md(sections)
        for section in sections:
            self.assertIn(f"## {section}", md)


class TestDistillRefinedIntegration(IsolatedWorkspaceCase):

    def test_writes_memory_md_and_creates_backup(self):
        from service.memory.distill_refined import build_memory_md
        from service.config import MEMORY_MD
        import shutil

        md_path = self.memory_dir / MEMORY_MD
        original_content = md_path.read_text(encoding="utf-8")

        sections = {
            "用户偏好": ["中文回答"],
            "项目背景": ["测试项目"],
            "重要决策": ["用 PostgreSQL"],
        }
        new_content = build_memory_md(sections)
        
        bak_path = self.memory_dir / (MEMORY_MD + ".bak")
        shutil.copy2(str(md_path), str(bak_path))
        md_path.write_text(new_content, encoding="utf-8")

        self.assertTrue(bak_path.exists())
        self.assertEqual(bak_path.read_text(encoding="utf-8"), original_content)

        written = md_path.read_text(encoding="utf-8")
        self.assertIn("- 中文回答", written)
        self.assertIn("- 用 PostgreSQL", written)
        self.assertNotIn("语言：中文", written)

    def test_distilled_flag_in_session_state(self):
        from service.memory.session_state import update_session_state
        
        update_session_state(str(self.memory_dir), "test-distill-session", {"distilled": True})
        state = read_session_state(str(self.memory_dir), "test-distill-session")
        self.assertTrue(state.get("distilled"))


class TestDistillSkipsWhenAlreadyRefined(IsolatedWorkspaceCase):

    def test_distill_skips_when_distilled_flag_set(self):
        from service.memory.session_state import update_session_state
        from service.memory.distill_to_memory import distill

        update_session_state(str(self.memory_dir), "refined-session", {"distilled": True})

        config = {
            "enabled": True,
            "min_confidence": 0.85,
            "min_age_days": 0,
            "max_items_per_run": 5,
            "keywords_rules": {"项目规范": ["必须"], "重要决策": ["使用"]},
        }
        count = distill(self.workspace, config, session_id="refined-session")
        self.assertEqual(count, 0)

    def test_distill_proceeds_when_no_distilled_flag(self):
        from service.memory.distill_to_memory import distill
        from core.utils import today_str
        from datetime import datetime, timezone, timedelta
        import json

        ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        with open(daily_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "fact", "content": "新事实", "confidence": 0.9,
                "timestamp": ts, "memory_type": "W",
            }, ensure_ascii=False) + "\n")

        config = {
            "enabled": True,
            "min_confidence": 0.85,
            "min_age_days": 0,
            "max_items_per_run": 5,
            "keywords_rules": {"项目规范": ["必须"], "重要决策": ["使用"]},
        }
        count = distill(self.workspace, config, session_id="no-flag-session")
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
