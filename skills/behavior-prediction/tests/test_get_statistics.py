#!/usr/bin/env python3
"""
测试 get_statistics.py 获取统计数据功能
"""

import json
import sys
import tempfile
import shutil
import time
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import unittest
import importlib


class TestGetStatistics(unittest.TestCase):
    """测试获取统计数据功能"""
    
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
        import get_statistics
        import record_action
        importlib.reload(get_statistics)
        importlib.reload(record_action)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 恢复模块
        import get_statistics
        import record_action
        importlib.reload(get_statistics)
        importlib.reload(record_action)
    
    def test_get_statistics_empty(self):
        """测试获取空统计数据"""
        from get_statistics import get_statistics
        
        result = get_statistics("create_file")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["current_action"], "create_file")
        self.assertEqual(result["transitions"], {})
        self.assertEqual(result["total_samples"], 0)
    
    def test_get_statistics_with_data(self):
        """测试获取有数据的统计"""
        from get_statistics import get_statistics
        from record_action import record_action
        
        # 记录一些动作
        record_action({"type": "create_file", "tool": "Write", "details": {}})
        time.sleep(0.1)
        record_action({"type": "edit_file", "tool": "StrReplace", "details": {}})
        time.sleep(0.1)
        record_action({"type": "run_test", "tool": "Shell", "details": {}})
        
        # 获取 edit_file 的统计
        result = get_statistics("edit_file")
        
        self.assertEqual(result["status"], "success")
        self.assertIn("run_test", result["transitions"])
        self.assertEqual(result["transitions"]["run_test"]["count"], 1)
        self.assertEqual(result["transitions"]["run_test"]["probability"], 1.0)
    
    def test_get_statistics_recent_sequence(self):
        """测试获取最近动作序列"""
        from get_statistics import get_statistics
        from record_action import record_action
        
        # 记录一些动作
        record_action({"type": "action1", "tool": "Test", "details": {}})
        time.sleep(0.1)
        record_action({"type": "action2", "tool": "Test", "details": {}})
        time.sleep(0.1)
        record_action({"type": "action3", "tool": "Test", "details": {}})
        
        result = get_statistics("action3")
        
        self.assertEqual(result["recent_sequence"], ["action1", "action2", "action3"])
    
    def test_get_statistics_top_prediction(self):
        """测试获取 Top 预测"""
        from get_statistics import get_statistics
        from record_action import record_action
        
        # 记录多次相同模式
        for _ in range(5):
            record_action({"type": "write_code", "tool": "Write", "details": {}})
            time.sleep(0.1)
            record_action({"type": "run_test", "tool": "Shell", "details": {}})
            time.sleep(0.1)
        
        result = get_statistics("write_code")
        
        self.assertEqual(result["status"], "success")
        self.assertIn("top_prediction", result)
        self.assertEqual(result["top_prediction"]["action"], "run_test")
        self.assertEqual(result["top_prediction"]["probability"], 1.0)
    
    def test_get_all_statistics_empty(self):
        """测试获取空的所有统计"""
        from get_statistics import get_all_statistics
        
        result = get_all_statistics()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_transitions"], 0)
        self.assertEqual(result["action_types_count"], 0)
    
    def test_get_all_statistics_with_data(self):
        """测试获取有数据的所有统计"""
        from get_statistics import get_all_statistics
        from record_action import record_action
        
        # 记录一些动作
        record_action({"type": "create_file", "tool": "Write", "details": {}})
        time.sleep(0.1)
        record_action({"type": "edit_file", "tool": "StrReplace", "details": {}})
        time.sleep(0.1)
        record_action({"type": "run_test", "tool": "Shell", "details": {}})
        
        result = get_all_statistics()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_transitions"], 2)
        self.assertEqual(result["action_types_count"], 3)
        self.assertEqual(result["today_actions"], 3)
    
    def test_calculate_recent_pattern(self):
        """测试计算最近行为模式"""
        from get_statistics import calculate_recent_pattern
        
        recent_sequence = ["a", "b", "a", "b", "a", "c"]
        
        result = calculate_recent_pattern(recent_sequence, "a", "b")
        
        # a 出现 3 次，其中 2 次后面是 b，1 次后面是 c
        # 函数统计的是 a 后面有动作的情况
        self.assertEqual(result["occurrences"], 3)  # a 出现 3 次（最后一个也算）
        self.assertEqual(result["followed_by_prediction"], 2)  # 2 次后面是 b
        self.assertAlmostEqual(result["pattern_strength"], 0.67, places=2)
    
    def test_get_statistics_context(self):
        """测试获取上下文信息"""
        from get_statistics import get_statistics
        import utils
        
        result = get_statistics("test_action")
        
        self.assertIn("context", result)
        self.assertEqual(result["context"]["date"], utils.get_today())
        self.assertIn("time", result["context"])
    
    def test_get_statistics_prediction_config(self):
        """测试获取预测配置"""
        from get_statistics import get_statistics
        
        result = get_statistics("test_action")
        
        self.assertIn("prediction_config", result)
        self.assertIn("suggest_threshold", result["prediction_config"])
        self.assertIn("auto_execute_threshold", result["prediction_config"])


if __name__ == "__main__":
    unittest.main()
