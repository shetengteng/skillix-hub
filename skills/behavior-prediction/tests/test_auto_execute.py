#!/usr/bin/env python3
"""
测试自动执行功能

测试 get_predictions.py 中的自动执行评估逻辑
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import unittest


class TestAutoExecuteConfig(unittest.TestCase):
    """测试自动执行配置加载"""
    
    def setUp(self):
        """测试前准备：创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_has_auto_execute(self):
        """测试配置包含自动执行选项"""
        import utils
        
        config = utils.load_config()
        auto_exec = config.get("prediction", {}).get("auto_execute", {})
        
        self.assertIn("enabled", auto_exec)
        self.assertIn("threshold", auto_exec)
        self.assertIn("allowed_actions", auto_exec)
        self.assertIn("forbidden_actions", auto_exec)
        self.assertIn("require_confirmation_below", auto_exec)
    
    def test_config_default_values(self):
        """测试配置默认值"""
        import utils
        
        config = utils.load_config()
        auto_exec = config.get("prediction", {}).get("auto_execute", {})
        
        self.assertTrue(auto_exec.get("enabled"))
        self.assertEqual(auto_exec.get("threshold"), 0.85)
        self.assertEqual(auto_exec.get("require_confirmation_below"), 0.95)
        self.assertIn("run_test", auto_exec.get("allowed_actions", []))
        self.assertIn("delete_file", auto_exec.get("forbidden_actions", []))


class TestEvaluateAutoExecute(unittest.TestCase):
    """测试自动执行评估函数"""
    
    def test_disabled_config(self):
        """测试禁用自动执行"""
        from get_predictions import evaluate_auto_execute
        
        config = {"enabled": False}
        prediction = {"next_stage": "test", "probability": 0.99, "confidence": 0.99}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
        self.assertEqual(result["reason"], "auto_execute_disabled")
    
    def test_empty_config(self):
        """测试空配置"""
        from get_predictions import evaluate_auto_execute
        
        prediction = {"next_stage": "test", "probability": 0.99, "confidence": 0.99}
        
        result = evaluate_auto_execute(prediction, {})
        
        self.assertFalse(result["should_auto_execute"])
        self.assertEqual(result["reason"], "auto_execute_disabled")
    
    def test_high_confidence_auto_execute(self):
        """测试高置信度直接执行"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "test", "probability": 0.96, "confidence": 0.96}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertTrue(result["should_auto_execute"])
        self.assertFalse(result["should_confirm"])
        self.assertEqual(result["action"], "run_test")
        self.assertIn("auto_execute_approved", result["reason"])
    
    def test_medium_confidence_requires_confirmation(self):
        """测试中置信度需要确认"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "test", "probability": 0.90, "confidence": 0.90}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
        self.assertTrue(result["should_confirm"])
        self.assertIn("confidence_requires_confirmation", result["reason"])
    
    def test_low_confidence_no_execute(self):
        """测试低置信度不执行"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "test", "probability": 0.70, "confidence": 0.70}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
        self.assertFalse(result["should_confirm"])
        self.assertIn("confidence_below_threshold", result["reason"])
    
    def test_forbidden_action(self):
        """测试禁止的动作"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test", "delete_file"],
            "forbidden_actions": ["delete_file"],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "delete_file", "probability": 0.99, "confidence": 0.99}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
        self.assertIn("action_forbidden", result["reason"])
    
    def test_not_in_allowed_list(self):
        """测试不在允许列表中的动作"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "deploy", "probability": 0.99, "confidence": 0.99}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
        self.assertIn("action_not_in_allowed_list", result["reason"])
    
    def test_stage_to_action_mapping(self):
        """测试阶段到动作的映射"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test", "run_lint", "git_status", "git_add"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        
        # 测试 test 阶段映射到 run_test
        prediction = {"next_stage": "test", "probability": 0.96, "confidence": 0.96}
        result = evaluate_auto_execute(prediction, config)
        self.assertEqual(result["action"], "run_test")
        
        # 测试 lint 阶段映射到 run_lint
        prediction = {"next_stage": "lint", "probability": 0.96, "confidence": 0.96}
        result = evaluate_auto_execute(prediction, config)
        self.assertEqual(result["action"], "run_lint")


class TestGenerateAutoCommand(unittest.TestCase):
    """测试命令生成函数"""
    
    def test_run_test_command(self):
        """测试运行测试命令"""
        from get_predictions import generate_auto_command
        
        cmd = generate_auto_command("run_test")
        self.assertEqual(cmd, "pytest")
    
    def test_run_lint_command(self):
        """测试运行 lint 命令"""
        from get_predictions import generate_auto_command
        
        cmd = generate_auto_command("run_lint")
        self.assertEqual(cmd, "ruff check .")
    
    def test_git_status_command(self):
        """测试 git status 命令"""
        from get_predictions import generate_auto_command
        
        cmd = generate_auto_command("git_status")
        self.assertEqual(cmd, "git status")
    
    def test_git_add_command(self):
        """测试 git add 命令"""
        from get_predictions import generate_auto_command
        
        cmd = generate_auto_command("git_add")
        self.assertEqual(cmd, "git add -A")
    
    def test_unknown_action(self):
        """测试未知动作"""
        from get_predictions import generate_auto_command
        
        cmd = generate_auto_command("unknown_action")
        self.assertIsNone(cmd)
    
    def test_context_test_file(self):
        """测试带上下文的测试命令"""
        from get_predictions import generate_auto_command
        
        context = {"test_file": "tests/test_auth.py"}
        cmd = generate_auto_command("run_test", context)
        self.assertEqual(cmd, "pytest tests/test_auth.py")
    
    def test_context_directory(self):
        """测试带上下文的 lint 命令"""
        from get_predictions import generate_auto_command
        
        context = {"directory": "src/"}
        cmd = generate_auto_command("run_lint", context)
        self.assertEqual(cmd, "ruff check src/")


class TestBoundaryConditions(unittest.TestCase):
    """测试边界条件"""
    
    def test_confidence_equals_threshold(self):
        """测试置信度恰好等于阈值"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        # 置信度恰好等于 0.85
        prediction = {"next_stage": "test", "probability": 0.85, "confidence": 0.85}
        
        result = evaluate_auto_execute(prediction, config)
        
        # 恰好等于阈值时，应该需要确认
        self.assertFalse(result["should_auto_execute"])
        self.assertTrue(result["should_confirm"])
    
    def test_confidence_equals_confirm_threshold(self):
        """测试置信度恰好等于确认阈值"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        # 置信度恰好等于 0.95
        prediction = {"next_stage": "test", "probability": 0.95, "confidence": 0.95}
        
        result = evaluate_auto_execute(prediction, config)
        
        # 恰好等于确认阈值时，应该直接执行
        self.assertTrue(result["should_auto_execute"])
        self.assertFalse(result["should_confirm"])
    
    def test_confidence_just_below_threshold(self):
        """测试置信度刚好低于阈值"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["run_test"],
            "forbidden_actions": [],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "test", "probability": 0.84, "confidence": 0.84}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
        self.assertFalse(result["should_confirm"])
        self.assertIn("confidence_below_threshold", result["reason"])


class TestSafety(unittest.TestCase):
    """测试安全性"""
    
    def test_forbidden_overrides_allowed(self):
        """测试禁止列表优先级高于允许列表"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["delete_file"],  # 在允许列表
            "forbidden_actions": ["delete_file"],  # 也在禁止列表
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "delete_file", "probability": 1.0, "confidence": 1.0}
        
        result = evaluate_auto_execute(prediction, config)
        
        # 禁止列表优先
        self.assertFalse(result["should_auto_execute"])
        self.assertIn("action_forbidden", result["reason"])
    
    def test_git_push_blocked(self):
        """测试 git push 被阻止"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["git_push"],
            "forbidden_actions": ["git_push"],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "git_push", "probability": 1.0, "confidence": 1.0}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])
    
    def test_deploy_blocked(self):
        """测试 deploy 被阻止"""
        from get_predictions import evaluate_auto_execute
        
        config = {
            "enabled": True,
            "threshold": 0.85,
            "allowed_actions": ["deploy"],
            "forbidden_actions": ["deploy"],
            "require_confirmation_below": 0.95
        }
        prediction = {"next_stage": "deploy", "probability": 1.0, "confidence": 1.0}
        
        result = evaluate_auto_execute(prediction, config)
        
        self.assertFalse(result["should_auto_execute"])


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备：创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_predictions_includes_auto_execute(self):
        """测试 get_predictions 返回包含 auto_execute"""
        from get_predictions import get_predictions
        
        result = get_predictions("implement")
        
        self.assertIn("auto_execute", result)
        self.assertIn("enabled", result["auto_execute"])
        self.assertIn("should_auto_execute", result["auto_execute"])
    
    def test_get_predictions_no_stage(self):
        """测试无当前阶段时的返回"""
        from get_predictions import get_predictions
        
        result = get_predictions()
        
        self.assertIn("auto_execute", result)
        self.assertFalse(result["auto_execute"]["should_auto_execute"])


if __name__ == "__main__":
    unittest.main()
