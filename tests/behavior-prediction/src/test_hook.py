#!/usr/bin/env python3
"""
测试 hook.py - V2 Session Hook 功能测试
"""

import json
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "skills" / "behavior-prediction" / "scripts"))


class TestHookInit(unittest.TestCase):
    """测试 hook.py --init 功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_handle_init_success(self):
        """测试初始化成功"""
        from hook import handle_init
        
        result = handle_init()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("user_profile", result)
        self.assertIn("behavior_patterns", result)
        self.assertIn("ai_summary", result)
        self.assertIn("suggestions", result)
    
    def test_handle_init_new_user(self):
        """测试新用户初始化"""
        from hook import handle_init
        
        result = handle_init()
        
        # 用户画像应该有基本的统计结构
        profile = result["user_profile"]
        self.assertIn("total_sessions", profile["stats"])
        self.assertIn("active_days", profile["stats"])
    
    def test_handle_init_profile_structure(self):
        """测试用户画像结构"""
        from hook import handle_init
        
        result = handle_init()
        profile = result["user_profile"]
        
        self.assertIn("updated_at", profile)
        self.assertIn("stats", profile)
        self.assertIn("preferences", profile)
        self.assertIn("time_patterns", profile)
    
    def test_handle_init_ai_summary_structure(self):
        """测试 AI 摘要结构"""
        from hook import handle_init
        
        result = handle_init()
        ai_summary = result["ai_summary"]
        
        self.assertIn("summary", ai_summary)
        self.assertIn("behavior_patterns", ai_summary)
        self.assertIn("predictions", ai_summary)
        self.assertIn("preferences", ai_summary)


class TestHookFinalize(unittest.TestCase):
    """测试 hook.py --finalize 功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_handle_finalize_success(self):
        """测试会话结束处理成功"""
        from hook import handle_finalize
        
        session_data = {
            "session_summary": {
                "topic": "测试会话",
                "goals": ["测试"],
                "completed_tasks": ["完成测试"],
                "technologies_used": ["Python"],
                "workflow_stages": ["implement", "test"],
                "tags": ["#test"]
            },
            "operations": {
                "files": {"created": ["test.py"], "modified": [], "deleted": []},
                "commands": []
            },
            "conversation": {
                "user_messages": ["测试消息"],
                "message_count": 1
            },
            "time": {
                "start": "2026-01-31T10:00:00Z",
                "end": "2026-01-31T10:30:00Z"
            }
        }
        
        result = handle_finalize(session_data)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("session_id", result)
        self.assertIn("message", result)
    
    def test_handle_finalize_creates_session_file(self):
        """测试会话文件创建"""
        from hook import handle_finalize
        import utils
        
        session_data = {
            "session_summary": {
                "topic": "测试",
                "workflow_stages": ["implement"]
            },
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
        }
        
        result = handle_finalize(session_data)
        
        # 检查返回结果包含 session_id
        self.assertIn("session_id", result)
        self.assertTrue(result["session_id"].startswith("sess_"))
    
    def test_handle_finalize_empty_session(self):
        """测试空会话处理"""
        from hook import handle_finalize
        
        session_data = {
            "session_summary": {},
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {}
        }
        
        result = handle_finalize(session_data)
        
        # 空会话也应该成功处理
        self.assertEqual(result["status"], "success")


class TestHookIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_then_finalize(self):
        """测试初始化后结束会话"""
        from hook import handle_init, handle_finalize
        
        # 初始化
        init_result = handle_init()
        self.assertEqual(init_result["status"], "success")
        
        # 结束会话
        session_data = {
            "session_summary": {
                "topic": "测试流程",
                "workflow_stages": ["implement"]
            },
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
        }
        
        finalize_result = handle_finalize(session_data)
        self.assertEqual(finalize_result["status"], "success")
    
    def test_multiple_sessions(self):
        """测试多次会话"""
        from hook import handle_init, handle_finalize
        
        for i in range(3):
            # 初始化
            handle_init()
            
            # 结束会话
            session_data = {
                "session_summary": {
                    "topic": f"测试会话 {i+1}",
                    "workflow_stages": ["implement", "test"]
                },
                "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
                "conversation": {"user_messages": [], "message_count": 0},
                "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
            }
            
            result = handle_finalize(session_data)
            self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()
