#!/usr/bin/env python3
"""提示词模板文件加载和格式化测试"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.hooks.flush_memory import _load_template as flush_load, SAVE_FACT_CMD
from service.hooks.prompt_session_save import (
    _load_template as save_load,
    SAVE_SUMMARY_CMD, SAVE_FACT_CMD as SAVE_FACT_CMD2,
    DISTILL_REFINED_CMD,
)


class TestFlushTemplate(unittest.TestCase):

    def test_template_file_exists(self):
        prompts_dir = SCRIPTS_DIR / "service" / "hooks" / "prompts"
        self.assertTrue((prompts_dir / "flush_template.txt").exists())

    def test_template_loads_and_formats(self):
        tpl = flush_load("flush_template.txt")
        result = tpl.format(
            usage=85, msg_count=42, save_fact_cmd="/path/save_fact.py", conv_id="test-123"
        )
        self.assertIn("[Memory Flush]", result)
        self.assertIn("85%", result)
        self.assertIn("42", result)
        self.assertIn("test-123", result)

    def test_template_contains_quality_rules(self):
        tpl = flush_load("flush_template.txt")
        self.assertIn("type O", tpl)
        self.assertIn("type W", tpl)
        self.assertIn("type B", tpl)
        self.assertIn("80 字", tpl)
        self.assertIn("结论性表述", tpl)

    def test_template_contains_type_guidance(self):
        tpl = flush_load("flush_template.txt")
        self.assertIn("用户偏好", tpl)
        self.assertIn("项目规范", tpl)
        self.assertIn("项目背景", tpl)


class TestSessionSaveTemplate(unittest.TestCase):

    def test_template_file_exists(self):
        prompts_dir = SCRIPTS_DIR / "service" / "hooks" / "prompts"
        self.assertTrue((prompts_dir / "session_save_template.txt").exists())

    def test_template_loads_and_formats(self):
        tpl = save_load("session_save_template.txt")
        result = tpl.format(
            save_summary_cmd="/path/save_summary.py",
            save_fact_cmd="/path/save_fact.py",
            conv_id="test-456",
            distill_section="",
        )
        self.assertIn("[Session Save]", result)
        self.assertIn("test-456", result)

    def test_template_contains_quality_rules(self):
        tpl = save_load("session_save_template.txt")
        self.assertIn("一句话原则", tpl)
        self.assertIn("80 字", tpl)
        self.assertIn("不要保存", tpl)
        self.assertIn("合并同类", tpl)

    def test_template_contains_type_guidance(self):
        tpl = save_load("session_save_template.txt")
        self.assertIn("type O", tpl)
        self.assertIn("type W", tpl)
        self.assertIn("type B", tpl)
        self.assertIn("不要全部使用 W", tpl)

    def test_template_with_distill_section(self):
        tpl = save_load("session_save_template.txt")
        distill = save_load("distill_section_template.txt").format(
            memory_md_path="/test/MEMORY.md",
            distill_cmd="/path/distill_refined.py",
            project_path="/test",
            conv_id="test-789",
        )
        result = tpl.format(
            save_summary_cmd="/path/save_summary.py",
            save_fact_cmd="/path/save_fact.py",
            conv_id="test-789",
            distill_section=distill,
        )
        self.assertIn("精炼核心记忆", result)
        self.assertIn("下个月还重要", result)

    def test_template_without_distill_section(self):
        tpl = save_load("session_save_template.txt")
        result = tpl.format(
            save_summary_cmd="/path/save_summary.py",
            save_fact_cmd="/path/save_fact.py",
            conv_id="test-000",
            distill_section="",
        )
        self.assertNotIn("精炼核心记忆", result)
        self.assertIn("[Session Save]", result)


class TestDistillSectionTemplate(unittest.TestCase):

    def test_template_file_exists(self):
        prompts_dir = SCRIPTS_DIR / "service" / "hooks" / "prompts"
        self.assertTrue((prompts_dir / "distill_section_template.txt").exists())

    def test_template_loads_and_formats(self):
        tpl = save_load("distill_section_template.txt")
        result = tpl.format(
            memory_md_path="/test/MEMORY.md",
            distill_cmd="/path/distill_refined.py",
            project_path="/test/project",
            conv_id="test-distill",
        )
        self.assertIn("精炼核心记忆", result)
        self.assertIn("/test/MEMORY.md", result)
        self.assertIn("distill_refined.py", result)
        self.assertIn("test-distill", result)

    def test_template_contains_judgment_standard(self):
        tpl = save_load("distill_section_template.txt")
        self.assertIn("下个月还重要", tpl)
        self.assertIn("50 条", tpl)

    def test_template_contains_refine_rules(self):
        tpl = save_load("distill_section_template.txt")
        self.assertIn("80 字", tpl)
        self.assertIn("合并语义重复", tpl)
        self.assertIn("过滤临时性信息", tpl)
        self.assertIn("用户偏好", tpl)
        self.assertIn("项目规范", tpl)


if __name__ == "__main__":
    unittest.main(verbosity=2)
