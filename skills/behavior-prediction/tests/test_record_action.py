#!/usr/bin/env python3
"""
测试 record_action.py 记录动作功能
"""

import json
import sys
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import unittest
import importlib


class TestRecordAction(unittest.TestCase):
    """测试记录动作功能"""
    
    def setUp(self):
        """测试前准备：创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
        utils.ensure_data_dirs()
        
        # 重新加载依赖 utils 的模块
        import record_action
        importlib.reload(record_action)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 恢复模块
        import record_action
        importlib.reload(record_action)
    
    def test_record_action_success(self):
        """测试成功记录动作"""
        from record_action import record_action
        
        result = record_action({
            "type": "create_file",
            "tool": "Write",
            "details": {"file_path": "test.py"}
        })
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["type"], "create_file")
        self.assertIn("action_id", result)
        self.assertEqual(result["total_actions_today"], 1)
    
    def test_record_action_missing_type(self):
        """测试缺少动作类型"""
        from record_action import record_action
        
        result = record_action({
            "tool": "Write",
            "details": {}
        })
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing", result["message"])
    
    def test_record_action_duplicate_within_5s(self):
        """测试 5 秒内重复动作被跳过"""
        from record_action import record_action
        
        # 第一次记录
        result1 = record_action({
            "type": "create_file",
            "tool": "Write",
            "details": {"file_path": "test.py"}
        })
        self.assertEqual(result1["status"], "success")
        
        # 立即再次记录相同动作
        result2 = record_action({
            "type": "create_file",
            "tool": "Write",
            "details": {"file_path": "test.py"}
        })
        self.assertEqual(result2["status"], "skipped")
        self.assertIn("duplicate", result2["reason"])
    
    def test_record_action_different_type_no_skip(self):
        """测试不同类型动作不会被跳过"""
        from record_action import record_action
        
        # 第一次记录
        result1 = record_action({
            "type": "create_file",
            "tool": "Write",
            "details": {}
        })
        self.assertEqual(result1["status"], "success")
        
        # 记录不同类型
        result2 = record_action({
            "type": "edit_file",
            "tool": "StrReplace",
            "details": {}
        })
        self.assertEqual(result2["status"], "success")
    
    def test_record_action_updates_transition_matrix(self):
        """测试记录动作更新转移矩阵"""
        from record_action import record_action
        import utils
        
        # 记录两个连续动作
        record_action({"type": "create_file", "tool": "Write", "details": {}})
        
        # 等待一下避免重复检测
        time.sleep(0.1)
        
        record_action({"type": "edit_file", "tool": "StrReplace", "details": {}})
        
        # 检查转移矩阵
        matrix = utils.load_transition_matrix()
        self.assertIn("create_file", matrix["matrix"])
        self.assertIn("edit_file", matrix["matrix"]["create_file"])
        self.assertEqual(matrix["matrix"]["create_file"]["edit_file"]["count"], 1)
        self.assertEqual(matrix["matrix"]["create_file"]["edit_file"]["probability"], 1.0)
    
    def test_record_action_with_new_type(self):
        """测试记录新类型动作"""
        from record_action import record_action
        import utils
        
        result = record_action({
            "type": "train_model",
            "tool": "Shell",
            "details": {"command": "python train.py"},
            "classification": {
                "confidence": 0.85,
                "is_new_type": True,
                "description": "训练机器学习模型"
            }
        })
        
        self.assertEqual(result["status"], "success")
        
        # 检查类型注册表
        registry = utils.load_types_registry()
        self.assertIn("train_model", registry["types"])
        self.assertEqual(registry["types"]["train_model"]["source"], "auto_generated")
    
    def test_record_action_creates_daily_log(self):
        """测试记录动作创建每日日志"""
        from record_action import record_action
        import utils
        
        record_action({"type": "test_action", "tool": "Test", "details": {}})
        
        today = utils.get_today()
        log_file = utils.DATA_DIR / "actions" / f"{today}.json"
        
        self.assertTrue(log_file.exists())
        
        log_data = utils.load_json(log_file)
        self.assertEqual(log_data["date"], today)
        self.assertEqual(len(log_data["actions"]), 1)
        self.assertEqual(log_data["actions"][0]["type"], "test_action")
    
    def test_record_action_increments_id(self):
        """测试动作 ID 递增"""
        from record_action import record_action
        import utils
        
        result1 = record_action({"type": "action1", "tool": "Test", "details": {}})
        time.sleep(0.1)
        result2 = record_action({"type": "action2", "tool": "Test", "details": {}})
        time.sleep(0.1)
        result3 = record_action({"type": "action3", "tool": "Test", "details": {}})
        
        today = utils.get_today()
        self.assertEqual(result1["action_id"], f"{today}-001")
        self.assertEqual(result2["action_id"], f"{today}-002")
        self.assertEqual(result3["action_id"], f"{today}-003")


if __name__ == "__main__":
    unittest.main()
