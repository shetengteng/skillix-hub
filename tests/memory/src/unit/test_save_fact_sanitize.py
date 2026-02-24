#!/usr/bin/env python3
"""save_fact.py 的 sanitize_content 和 infer_memory_type 单元测试"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.memory.save_fact import sanitize_content, infer_memory_type


class TestSanitizeContent(unittest.TestCase):

    def test_removes_save_fact_command(self):
        dirty = (
            '修复Bug: python3 /path/to/save_fact.py --content "test" '
            '--type W --entities "a,b" --session "conv-123" 编译问题'
        )
        clean = sanitize_content(dirty)
        self.assertNotIn("save_fact.py", clean)
        self.assertIn("修复Bug", clean)
        self.assertIn("编译问题", clean)

    def test_removes_save_summary_command(self):
        dirty = (
            '完成任务 python3 /path/save_summary.py --topic "主题" '
            '--summary "摘要" --session "conv-456" 结束'
        )
        clean = sanitize_content(dirty)
        self.assertNotIn("save_summary.py", clean)

    def test_removes_partial_save_fact_command(self):
        dirty = "内容 python3 /some/path/save_fact.py --content 后续文本"
        clean = sanitize_content(dirty)
        self.assertNotIn("save_fact.py", clean)

    def test_collapses_multiple_spaces(self):
        content = "hello    world   test"
        clean = sanitize_content(content)
        self.assertEqual(clean, "hello world test")

    def test_strips_whitespace(self):
        content = "  hello world  "
        clean = sanitize_content(content)
        self.assertEqual(clean, "hello world")

    def test_truncates_long_content(self):
        content = "x" * 1000
        clean = sanitize_content(content)
        self.assertEqual(len(clean), 800)

    def test_no_truncation_under_limit(self):
        content = "x" * 500
        clean = sanitize_content(content)
        self.assertEqual(len(clean), 500)

    def test_preserves_normal_content(self):
        content = "Memory Skill 日志路径通过环境变量传递"
        clean = sanitize_content(content)
        self.assertEqual(clean, content)

    def test_real_world_dirty_data(self):
        """模拟 semantic_metadata 中发现的真实脏数据"""
        dirty = (
            "修复SemanticDimensionManager NoClassDefFoundError: "
            "将populateStatistics方法中的responses.forEach(lambda)改为标准for-each循环，"
            '避免匿名内部类python3 /Users/TerrellShe/.cursor/skills/memory/scripts/'
            'service/memory/save_fact.py --content "修复SemanticDimensionManager '
            'NoClassDefFoundError" --type W --entities "semantic-metadata" '
            '--session "8b2e6bcb-0d78-4be8-9590-a418497b48ba"编译缺失问题。'
        )
        clean = sanitize_content(dirty)
        self.assertNotIn("save_fact.py", clean)
        self.assertIn("修复SemanticDimensionManager", clean)
        self.assertIn("编译缺失问题", clean)


class TestInferMemoryType(unittest.TestCase):

    def test_preserves_non_w_types(self):
        self.assertEqual(infer_memory_type("任何内容", "O"), "O")
        self.assertEqual(infer_memory_type("任何内容", "B"), "B")
        self.assertEqual(infer_memory_type("任何内容", "S"), "S")

    def test_infers_o_from_preference_keywords(self):
        self.assertEqual(infer_memory_type("中文回答偏好", "W"), "O")
        self.assertEqual(infer_memory_type("用户习惯使用暗色主题", "W"), "O")
        self.assertEqual(infer_memory_type("禁止使用 forEach", "W"), "O")
        self.assertEqual(infer_memory_type("必须放在 tests/ 目录", "W"), "O")
        self.assertEqual(infer_memory_type("项目规范要求", "W"), "O")
        self.assertEqual(infer_memory_type("代码风格约定", "W"), "O")

    def test_infers_b_from_project_keywords(self):
        self.assertEqual(infer_memory_type("项目结构包含三个子项目", "W"), "B")
        self.assertEqual(infer_memory_type("技术栈是 Spring Boot", "W"), "B")
        self.assertEqual(infer_memory_type("本工作区是语义元数据系统", "W"), "B")

    def test_keeps_w_for_technical_decisions(self):
        self.assertEqual(infer_memory_type("使用 Redis 作为缓存层", "W"), "W")
        self.assertEqual(infer_memory_type("API 调用用 XHR 而非 fetch", "W"), "W")
        self.assertEqual(infer_memory_type("relationType 兼容 NULL", "W"), "W")

    def test_o_takes_priority_over_b(self):
        """当内容同时匹配 O 和 B 关键词时，O 优先"""
        result = infer_memory_type("项目规范要求技术栈统一", "W")
        self.assertEqual(result, "O")


if __name__ == "__main__":
    unittest.main(verbosity=2)
