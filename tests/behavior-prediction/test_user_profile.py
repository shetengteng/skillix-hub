#!/usr/bin/env python3
"""
测试 user_profile.py - 用户画像功能测试
"""

import json
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "skills" / "behavior-prediction" / "scripts"))


class TestUserProfile(unittest.TestCase):
    """测试用户画像功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR 和 get_data_dir 函数
        import utils
        import user_profile
        import record_session
        import extract_patterns
        
        self.original_data_dir = utils.DATA_DIR
        self.original_get_data_dir = utils.get_data_dir
        
        test_data_dir = self.temp_path / "behavior-prediction-data"
        utils.DATA_DIR = test_data_dir
        
        # 创建一个返回测试目录的函数
        def mock_get_data_dir(location="project"):
            return test_data_dir
        
        utils.get_data_dir = mock_get_data_dir
        
        # 同时更新其他模块中的引用
        user_profile.get_data_dir = mock_get_data_dir
        record_session.get_data_dir = mock_get_data_dir
        extract_patterns.get_data_dir = mock_get_data_dir
        
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理"""
        import utils
        import user_profile
        import record_session
        import extract_patterns
        
        # 恢复原始函数
        utils.DATA_DIR = self.original_data_dir
        utils.get_data_dir = self.original_get_data_dir
        user_profile.get_data_dir = self.original_get_data_dir
        record_session.get_data_dir = self.original_get_data_dir
        extract_patterns.get_data_dir = self.original_get_data_dir
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_default_profile(self):
        """测试获取默认画像"""
        from user_profile import get_default_profile
        
        profile = get_default_profile()
        
        self.assertEqual(profile["version"], "2.0")
        self.assertEqual(profile["stats"]["total_sessions"], 0)
        self.assertEqual(profile["stats"]["active_days"], 0)
        self.assertIsNone(profile["stats"]["first_seen"])
        self.assertIsNone(profile["stats"]["last_seen"])
    
    def test_load_user_profile_new_user(self):
        """测试新用户加载画像"""
        from user_profile import load_user_profile
        
        profile = load_user_profile()
        
        # 新用户应该返回默认画像
        self.assertEqual(profile["stats"]["total_sessions"], 0)
    
    def test_load_user_profile_existing(self):
        """测试加载已有画像"""
        from user_profile import load_user_profile
        import utils
        
        # 先创建一个画像文件
        profile_file = utils.DATA_DIR / "profile" / "user_profile.json"
        utils.ensure_dir(profile_file)
        utils.save_json(profile_file, {
            "version": "2.0",
            "stats": {"total_sessions": 10, "active_days": 5}
        })
        
        profile = load_user_profile()
        
        self.assertEqual(profile["stats"]["total_sessions"], 10)
        self.assertEqual(profile["stats"]["active_days"], 5)
    
    def test_update_user_profile(self):
        """测试更新用户画像"""
        from user_profile import update_user_profile
        from record_session import record_session
        
        # 先记录一些会话
        for i in range(3):
            session_data = {
                "session_summary": {
                    "topic": f"测试 {i+1}",
                    "workflow_stages": ["implement", "test"],
                    "technologies_used": ["Python"],
                    "tags": ["#test"]
                },
                "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
                "conversation": {"user_messages": [], "message_count": 0},
                "time": {}
            }
            record_session(session_data)
        
        # 强制更新画像
        profile = update_user_profile(force=True)
        
        self.assertEqual(profile["stats"]["total_sessions"], 3)
        self.assertIn("implement", profile["preferences"]["common_stages"])
    
    def test_get_ai_summary_new_user(self):
        """测试新用户 AI 摘要"""
        from user_profile import get_ai_summary
        
        summary = get_ai_summary()
        
        self.assertIn("summary", summary)
        self.assertIn("新用户", summary["summary"]["description"])
    
    def test_get_ai_summary_with_data(self):
        """测试有数据时的 AI 摘要"""
        from user_profile import get_ai_summary
        
        profile = {
            "stats": {
                "total_sessions": 10,
                "active_days": 5
            },
            "preferences": {
                "common_stages": ["implement", "test"],
                "common_tech": ["Python", "FastAPI"]
            },
            "work_style": {
                "test_driven": 0.3
            }
        }
        
        patterns = {
            "patterns": [
                {"sequence": ["implement", "test"], "count": 5, "description": "implement → test"}
            ],
            "stage_transitions": {
                "implement": {
                    "test": {"probability": 0.8, "count": 5}
                }
            }
        }
        
        summary = get_ai_summary(profile, patterns)
        
        self.assertIn("活跃了 5 天", summary["summary"]["description"])
        self.assertTrue(len(summary["behavior_patterns"]["common_sequences"]) > 0)
        self.assertTrue(len(summary["predictions"]["rules"]) > 0)
    
    def test_generate_suggestions(self):
        """测试生成建议"""
        from user_profile import generate_suggestions
        
        profile = {
            "preferences": {
                "common_stages": ["implement", "test"],
                "common_tech": ["Python"]
            }
        }
        
        patterns = {
            "patterns": [
                {"description": "implement → test", "count": 5}
            ],
            "stage_transitions": {
                "implement": {
                    "test": {"probability": 0.8, "count": 5}
                }
            }
        }
        
        suggestions = generate_suggestions(profile, patterns)
        
        self.assertTrue(len(suggestions) > 0)
    
    def test_describe_work_style(self):
        """测试工作风格描述"""
        from user_profile import describe_work_style
        
        # 空风格
        result = describe_work_style({})
        self.assertEqual(result, "灵活多变")
        
        # 测试驱动
        result = describe_work_style({"test_driven": 0.3})
        self.assertIn("测试驱动", result)
        
        # 注重规划
        result = describe_work_style({"planning_tendency": 0.3})
        self.assertIn("注重规划", result)
        
        # 多种风格
        result = describe_work_style({
            "test_driven": 0.3,
            "planning_tendency": 0.3,
            "documentation_focus": 0.2
        })
        self.assertIn("测试驱动", result)
        self.assertIn("注重规划", result)
        self.assertIn("重视文档", result)
    
    def test_extract_preferred_flow(self):
        """测试提取偏好工作流程"""
        from user_profile import extract_preferred_flow
        
        sessions = [
            {"workflow_stages": ["design", "implement", "test"]},
            {"workflow_stages": ["design", "implement", "test"]},
            {"workflow_stages": ["implement", "test"]},
        ]
        
        flows = extract_preferred_flow(sessions)
        
        self.assertTrue(len(flows) > 0)
        # 最常见的应该是 design → implement 或 implement → test
    
    def test_analyze_work_style(self):
        """测试分析工作风格"""
        from user_profile import analyze_work_style
        from collections import Counter
        
        sessions = []
        stage_counts = Counter({
            "design": 5,
            "implement": 10,
            "test": 8,
            "document": 3
        })
        
        style = analyze_work_style(sessions, stage_counts)
        
        self.assertIn("planning_tendency", style)
        self.assertIn("test_driven", style)
        self.assertIn("documentation_focus", style)
        
        # 检查比例计算
        total = 26
        self.assertAlmostEqual(style["planning_tendency"], 5/total, places=2)
        self.assertAlmostEqual(style["test_driven"], 8/total, places=2)


class TestUserProfileIntegration(unittest.TestCase):
    """用户画像集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        import utils
        import user_profile
        import record_session
        import extract_patterns
        
        self.original_data_dir = utils.DATA_DIR
        self.original_get_data_dir = utils.get_data_dir
        
        test_data_dir = self.temp_path / "behavior-prediction-data"
        utils.DATA_DIR = test_data_dir
        
        def mock_get_data_dir(location="project"):
            return test_data_dir
        
        utils.get_data_dir = mock_get_data_dir
        user_profile.get_data_dir = mock_get_data_dir
        record_session.get_data_dir = mock_get_data_dir
        extract_patterns.get_data_dir = mock_get_data_dir
        
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理"""
        import utils
        import user_profile
        import record_session
        import extract_patterns
        
        utils.DATA_DIR = self.original_data_dir
        utils.get_data_dir = self.original_get_data_dir
        user_profile.get_data_dir = self.original_get_data_dir
        record_session.get_data_dir = self.original_get_data_dir
        extract_patterns.get_data_dir = self.original_get_data_dir
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        from record_session import record_session
        from extract_patterns import extract_and_update_patterns
        from user_profile import update_user_profile, get_ai_summary
        
        # 1. 记录多个会话
        for i in range(5):
            session_data = {
                "session_summary": {
                    "topic": f"API 开发 {i+1}",
                    "workflow_stages": ["design", "implement", "test"],
                    "technologies_used": ["Python", "FastAPI"],
                    "tags": ["#api"]
                },
                "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
                "conversation": {"user_messages": [], "message_count": 0},
                "time": {}
            }
            record_session(session_data)
            extract_and_update_patterns(session_data)
        
        # 2. 更新用户画像
        profile = update_user_profile(force=True)
        
        # 3. 获取 AI 摘要
        summary = get_ai_summary()
        
        # 验证
        self.assertEqual(profile["stats"]["total_sessions"], 5)
        self.assertIn("design", profile["preferences"]["common_stages"])
        self.assertTrue(len(summary["predictions"]["rules"]) > 0)


if __name__ == "__main__":
    unittest.main()
