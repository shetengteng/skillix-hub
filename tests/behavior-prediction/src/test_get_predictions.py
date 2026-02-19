#!/usr/bin/env python3
"""
测试 get_predictions.py - 预测功能测试
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


class TestGetPredictions(unittest.TestCase):
    """测试预测功能"""
    
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
    
    def test_get_predictions_no_stage(self):
        """测试无当前阶段时的预测"""
        from get_predictions import get_predictions
        
        result = get_predictions()
        
        self.assertIsNone(result["current_stage"])
        self.assertEqual(len(result["predictions"]), 0)
        self.assertIn("auto_execute", result)
    
    def test_get_predictions_with_stage(self):
        """测试有当前阶段时的预测"""
        from get_predictions import get_predictions
        from extract_patterns import update_workflow_patterns
        
        # 先建立一些模式
        for _ in range(5):
            session_data = {
                "session_summary": {
                    "workflow_stages": ["implement", "test"]
                }
            }
            update_workflow_patterns(session_data)
        
        result = get_predictions("implement")
        
        self.assertEqual(result["current_stage"], "implement")
        self.assertTrue(len(result["predictions"]) > 0)
        self.assertEqual(result["predictions"][0]["next_stage"], "test")
    
    def test_calculate_confidence(self):
        """测试置信度计算"""
        from get_predictions import calculate_confidence
        
        # 低样本量降低置信度
        conf = calculate_confidence(0.8, 2)
        self.assertLess(conf, 0.8)
        
        # 高样本量提高置信度
        conf = calculate_confidence(0.8, 15)
        self.assertGreater(conf, 0.8)
        
        # 置信度不超过 1
        conf = calculate_confidence(1.0, 100)
        self.assertLessEqual(conf, 1.0)
    
    def test_generate_suggestion(self):
        """测试生成建议"""
        from get_predictions import generate_suggestion
        
        # 高置信度
        suggestion = generate_suggestion("implement", "test", 0.9)
        self.assertIn("测试", suggestion)
        
        # 中置信度
        suggestion = generate_suggestion("implement", "test", 0.7)
        self.assertIn("测试", suggestion)
        
        # 低置信度
        suggestion = generate_suggestion("implement", "test", 0.5)
        self.assertIn("测试", suggestion)
    
    def test_predict_next_action(self):
        """测试预测下一步动作"""
        from get_predictions import predict_next_action
        from extract_patterns import update_workflow_patterns
        
        # 建立模式
        for _ in range(5):
            session_data = {
                "session_summary": {
                    "workflow_stages": ["design", "implement", "test"]
                }
            }
            update_workflow_patterns(session_data)
        
        # 预测
        result = predict_next_action(["design", "implement"])
        
        self.assertTrue(len(result["predictions"]) > 0)
    
    def test_predict_next_action_empty(self):
        """测试空动作列表的预测"""
        from get_predictions import predict_next_action
        
        result = predict_next_action([])
        
        self.assertEqual(len(result["predictions"]), 0)
        self.assertFalse(result["should_suggest"])
    
    def test_get_workflow_suggestion(self):
        """测试获取工作流程建议"""
        from get_predictions import get_workflow_suggestion
        from extract_patterns import update_workflow_patterns
        
        # 建立模式
        for _ in range(5):
            session_data = {
                "session_summary": {
                    "workflow_stages": ["implement", "test"]
                }
            }
            update_workflow_patterns(session_data)
        
        result = get_workflow_suggestion(["implement"])
        
        self.assertTrue(result["has_suggestion"])
        self.assertEqual(result["suggested_next"], "test")
    
    def test_get_workflow_suggestion_empty(self):
        """测试空工作流程的建议"""
        from get_predictions import get_workflow_suggestion
        
        result = get_workflow_suggestion([])
        
        self.assertFalse(result["has_suggestion"])
    
    def test_get_general_suggestions(self):
        """测试获取通用建议"""
        from get_predictions import get_general_suggestions
        
        profile = {
            "preferences": {
                "common_stages": ["implement", "test", "commit"]
            }
        }
        
        patterns = {
            "patterns": [
                {"description": "implement → test", "count": 5}
            ]
        }
        
        suggestions = get_general_suggestions(profile, patterns)
        
        self.assertTrue(len(suggestions) > 0)
    
    def test_adjust_with_context(self):
        """测试上下文调整"""
        from get_predictions import adjust_with_context
        
        result = {
            "predictions": [
                {"next_stage": "test", "confidence": 0.7}
            ],
            "context_aware": False
        }
        
        context = {"project_type": "backend_api"}
        
        project_patterns = {
            "patterns": {
                "backend_api": {
                    "common_stages": {"test": 5}
                }
            }
        }
        
        adjusted = adjust_with_context(result, context, project_patterns)
        
        # 置信度应该被提高
        self.assertGreater(adjusted["predictions"][0]["confidence"], 0.7)
        # context_aware 在函数外部设置，这里只检查返回值


class TestPredictionsIntegration(unittest.TestCase):
    """预测功能集成测试"""
    
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
    
    def test_full_prediction_workflow(self):
        """测试完整预测工作流程"""
        from record_session import record_session
        from extract_patterns import extract_and_update_patterns
        from get_predictions import get_predictions
        
        # 1. 记录多个会话建立模式
        for i in range(10):
            session_data = {
                "session_summary": {
                    "topic": f"开发 {i+1}",
                    "workflow_stages": ["design", "implement", "test", "commit"]
                },
                "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
                "conversation": {"user_messages": [], "message_count": 0},
                "time": {}
            }
            record_session(session_data)
            extract_and_update_patterns(session_data)
        
        # 2. 获取预测
        result = get_predictions("implement")
        
        # 3. 验证
        self.assertTrue(len(result["predictions"]) > 0)
        self.assertEqual(result["predictions"][0]["next_stage"], "test")
        self.assertTrue(result["predictions"][0]["confidence"] > 0.5)


if __name__ == "__main__":
    unittest.main()
