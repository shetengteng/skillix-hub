#!/usr/bin/env python3
"""
测试 check_last_session.py 会话检查功能
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import unittest
import importlib


class TestCheckLastSession(unittest.TestCase):
    """测试会话检查功能"""
    
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
        import check_last_session
        importlib.reload(check_last_session)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 恢复模块
        import check_last_session
        importlib.reload(check_last_session)
    
    def test_check_last_session_first_time(self):
        """测试首次检查"""
        from check_last_session import check_last_session
        
        result = check_last_session()
        
        self.assertEqual(result["status"], "success")
        self.assertIn(result["action"], ["none", "recalculated"])
    
    def test_check_last_session_already_checked(self):
        """测试今天已检查过"""
        from check_last_session import check_last_session
        import utils
        
        # 第一次检查
        check_last_session()
        
        # 第二次检查应该跳过
        result = check_last_session()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "none")
        self.assertIn("Already checked", result["reason"])
    
    def test_has_action_logs_empty(self):
        """测试检查空的动作日志"""
        from check_last_session import has_action_logs
        
        result = has_action_logs()
        self.assertFalse(result)
    
    def test_has_action_logs_with_data(self):
        """测试检查有数据的动作日志"""
        from check_last_session import has_action_logs
        import utils
        
        # 创建一个日志文件
        today = utils.get_today()
        log_file = utils.DATA_DIR / "actions" / f"{today}.json"
        utils.save_json(log_file, {"date": today, "actions": []})
        
        result = has_action_logs()
        self.assertTrue(result)
    
    def test_recalculate_transition_matrix(self):
        """测试重新计算转移矩阵"""
        from check_last_session import recalculate_transition_matrix
        import utils
        
        # 创建一些动作日志
        today = utils.get_today()
        log_file = utils.DATA_DIR / "actions" / f"{today}.json"
        utils.save_json(log_file, {
            "date": today,
            "actions": [
                {"type": "create_file", "tool": "Write"},
                {"type": "edit_file", "tool": "StrReplace"},
                {"type": "run_test", "tool": "Shell"}
            ]
        })
        
        # 重新计算
        recalculate_transition_matrix()
        
        # 检查结果
        matrix = utils.load_transition_matrix()
        
        self.assertIn("create_file", matrix["matrix"])
        self.assertIn("edit_file", matrix["matrix"]["create_file"])
        self.assertEqual(matrix["matrix"]["create_file"]["edit_file"]["count"], 1)
        self.assertTrue(matrix.get("recalculated"))
    
    def test_get_data_summary(self):
        """测试获取数据摘要"""
        from check_last_session import get_data_summary
        from record_action import record_action
        import time
        
        # 记录一些动作
        record_action({"type": "action1", "tool": "Test", "details": {}})
        time.sleep(0.1)
        record_action({"type": "action2", "tool": "Test", "details": {}})
        
        result = get_data_summary()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["log_files_count"], 1)
        self.assertEqual(result["total_actions"], 2)
        self.assertEqual(result["total_transitions"], 1)
    
    def test_recalculate_with_multiple_days(self):
        """测试多天数据的重新计算"""
        from check_last_session import recalculate_transition_matrix
        import utils
        
        # 创建多天的日志
        today = datetime.now()
        for i in range(3):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = utils.DATA_DIR / "actions" / f"{date}.json"
            utils.save_json(log_file, {
                "date": date,
                "actions": [
                    {"type": "create_file", "tool": "Write"},
                    {"type": "edit_file", "tool": "StrReplace"}
                ]
            })
        
        # 重新计算
        recalculate_transition_matrix()
        
        # 检查结果
        matrix = utils.load_transition_matrix()
        
        # 3 天的数据，每天 1 次转移
        self.assertEqual(matrix["matrix"]["create_file"]["edit_file"]["count"], 3)
        self.assertEqual(matrix["total_transitions"], 3)


if __name__ == "__main__":
    unittest.main()
