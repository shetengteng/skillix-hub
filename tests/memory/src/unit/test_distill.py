#!/usr/bin/env python3
"""distill_to_memory.py 单元测试"""
import json
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from core.utils import today_str
from service.memory.distill_to_memory import (
    _parse_memory_md, _flatten_existing, _is_duplicate, _classify,
    select_candidates, write_to_memory_md, distill, DISTILL_DEFAULTS,
)

_KW_RULES = DISTILL_DEFAULTS["keywords_rules"]


class TestDistillParsing(IsolatedWorkspaceCase):

    def test_parse_memory_md_sections(self):
        sections = _parse_memory_md(str(self.memory_dir / "MEMORY.md"))
        self.assertIn("用户偏好", sections)
        self.assertIn("项目背景", sections)
        self.assertIn("重要决策", sections)
        self.assertEqual(sections["用户偏好"], ["语言：中文"])
        self.assertEqual(sections["项目背景"], ["项目：standalone-test"])

    def test_parse_empty_memory_md(self):
        (self.memory_dir / "MEMORY.md").write_text(
            "# 核心记忆\n\n## 用户偏好\n\n## 项目背景\n\n## 重要决策\n",
            encoding="utf-8",
        )
        sections = _parse_memory_md(str(self.memory_dir / "MEMORY.md"))
        self.assertEqual(sections["用户偏好"], [])
        self.assertEqual(sections["重要决策"], [])

    def test_flatten_existing(self):
        sections = _parse_memory_md(str(self.memory_dir / "MEMORY.md"))
        existing = _flatten_existing(sections)
        self.assertIn("语言：中文", existing)
        self.assertIn("项目：standalone-test", existing)


class TestDistillDuplication(IsolatedWorkspaceCase):

    def test_exact_duplicate(self):
        existing = {"语言：中文", "项目：standalone-test"}
        self.assertTrue(_is_duplicate("语言：中文", existing))
        self.assertFalse(_is_duplicate("新的事实", existing))

    def test_substring_duplicate(self):
        existing = {"测试文件必须放在 tests/ 目录下对应的 skill 子目录中"}
        self.assertTrue(_is_duplicate(
            "测试文件必须放在 tests/ 目录下对应的 skill 子目录中，不能放在 skills/ 目录内部",
            existing,
        ))


class TestDistillClassify(IsolatedWorkspaceCase):

    def test_opinion_to_user_preference(self):
        fact = {"memory_type": "O", "content": "用户偏好 TypeScript"}
        self.assertEqual(_classify(fact, _KW_RULES), "用户偏好")

    def test_world_with_rule_keyword(self):
        fact = {"memory_type": "W", "content": "测试文件必须放在 tests/ 目录下"}
        self.assertEqual(_classify(fact, _KW_RULES), "项目规范")

    def test_world_with_decision_keyword(self):
        fact = {"memory_type": "W", "content": "项目决定使用 PostgreSQL 数据库"}
        self.assertEqual(_classify(fact, _KW_RULES), "重要决策")

    def test_world_fallback_to_background(self):
        fact = {"memory_type": "W", "content": "前端框架是 React"}
        self.assertEqual(_classify(fact, _KW_RULES), "项目背景")

    def test_biographical_to_background(self):
        fact = {"memory_type": "B", "content": "2026-02-17 完成了 API 重构"}
        self.assertEqual(_classify(fact, _KW_RULES), "项目背景")


class TestDistillCandidates(IsolatedWorkspaceCase):

    def _write_facts(self, facts):
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        with open(daily_file, "w", encoding="utf-8") as f:
            for fact in facts:
                f.write(json.dumps(fact, ensure_ascii=False) + "\n")

    def test_filters_low_confidence(self):
        ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self._write_facts([
            {"type": "fact", "content": "高置信度事实", "confidence": 0.9, "timestamp": ts, "memory_type": "W"},
            {"type": "fact", "content": "低置信度事实", "confidence": 0.5, "timestamp": ts, "memory_type": "W"},
        ])
        daily_dir = str(self.memory_dir / "daily")
        candidates = select_candidates(daily_dir, set(), {"min_confidence": 0.85, "min_age_days": 0, "max_items_per_run": 10})
        contents = [c["content"] for c in candidates]
        self.assertIn("高置信度事实", contents)
        self.assertNotIn("低置信度事实", contents)

    def test_filters_by_age(self):
        old_ts = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        new_ts = datetime.now(timezone.utc).isoformat()
        self._write_facts([
            {"type": "fact", "content": "旧事实", "confidence": 0.9, "timestamp": old_ts, "memory_type": "W"},
            {"type": "fact", "content": "新事实", "confidence": 0.9, "timestamp": new_ts, "memory_type": "W"},
        ])
        daily_dir = str(self.memory_dir / "daily")
        candidates = select_candidates(daily_dir, set(), {"min_confidence": 0.85, "min_age_days": 2, "max_items_per_run": 10})
        contents = [c["content"] for c in candidates]
        self.assertIn("旧事实", contents)
        self.assertNotIn("新事实", contents)

    def test_skips_duplicates(self):
        ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self._write_facts([
            {"type": "fact", "content": "语言：中文", "confidence": 0.9, "timestamp": ts, "memory_type": "O"},
        ])
        daily_dir = str(self.memory_dir / "daily")
        existing = {"语言：中文"}
        candidates = select_candidates(daily_dir, existing, {"min_confidence": 0.85, "min_age_days": 0, "max_items_per_run": 10})
        self.assertEqual(len(candidates), 0)

    def test_opinion_sorted_first(self):
        ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self._write_facts([
            {"type": "fact", "content": "W 类型事实", "confidence": 0.9, "timestamp": ts, "memory_type": "W"},
            {"type": "fact", "content": "O 类型偏好", "confidence": 0.9, "timestamp": ts, "memory_type": "O"},
        ])
        daily_dir = str(self.memory_dir / "daily")
        candidates = select_candidates(daily_dir, set(), {"min_confidence": 0.85, "min_age_days": 0, "max_items_per_run": 10})
        self.assertEqual(candidates[0]["content"], "O 类型偏好")


class TestDistillWrite(IsolatedWorkspaceCase):

    def test_write_to_existing_section(self):
        md_path = str(self.memory_dir / "MEMORY.md")
        write_to_memory_md(md_path, {"用户偏好": ["偏好 TypeScript"]})
        content = (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8")
        self.assertIn("- 偏好 TypeScript", content)
        self.assertIn("- 语言：中文", content)

    def test_write_to_new_section(self):
        md_path = str(self.memory_dir / "MEMORY.md")
        write_to_memory_md(md_path, {"项目规范": ["测试必须放在 tests/ 目录下"]})
        content = (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8")
        self.assertIn("## 项目规范", content)
        self.assertIn("- 测试必须放在 tests/ 目录下", content)

    def test_idempotent_write(self):
        md_path = str(self.memory_dir / "MEMORY.md")
        write_to_memory_md(md_path, {"用户偏好": ["新偏好"]})
        content1 = (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8")
        self.assertEqual(content1.count("- 新偏好"), 1)


class TestDistillIntegration(IsolatedWorkspaceCase):

    def test_full_distill_flow(self):
        ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        facts = [
            {"type": "fact", "content": "项目必须使用 ESLint", "confidence": 0.9, "timestamp": ts, "memory_type": "W"},
            {"type": "fact", "content": "用户偏好暗色主题", "confidence": 0.9, "timestamp": ts, "memory_type": "O"},
        ]
        with open(daily_file, "w", encoding="utf-8") as f:
            for fact in facts:
                f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        config = {
            "enabled": True,
            "min_confidence": 0.85,
            "min_age_days": 0,
            "max_items_per_run": 5,
            "keywords_rules": {
                "项目规范": ["必须", "规则", "规范"],
                "重要决策": ["决定", "使用", "选择"],
            },
        }
        count = distill(self.workspace, config)
        self.assertEqual(count, 2)

        content = (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8")
        self.assertIn("用户偏好暗色主题", content)
        self.assertIn("项目必须使用 ESLint", content)

    def test_disabled_distill(self):
        count = distill(self.workspace, {"enabled": False})
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
