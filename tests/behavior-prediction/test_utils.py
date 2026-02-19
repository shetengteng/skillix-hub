#!/usr/bin/env python3
"""
测试 utils.py 工具函数 (V2)
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "skills" / "behavior-prediction" / "scripts"))

import unittest


class TestUtils(unittest.TestCase):
    """测试工具函数"""
    
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
    
    def test_ensure_data_dirs(self):
        """测试确保数据目录存在"""
        import utils
        
        utils.ensure_data_dirs()
        
        self.assertTrue((utils.DATA_DIR / "sessions").exists())
        self.assertTrue((utils.DATA_DIR / "patterns").exists())
        self.assertTrue((utils.DATA_DIR / "profile").exists())
        self.assertTrue((utils.DATA_DIR / "index").exists())
    
    def test_load_json_not_exists(self):
        """测试加载不存在的 JSON 文件"""
        import utils
        
        result = utils.load_json(self.temp_path / "not_exists.json", {"default": True})
        self.assertEqual(result, {"default": True})
    
    def test_load_json_exists(self):
        """测试加载存在的 JSON 文件"""
        import utils
        
        test_file = self.temp_path / "test.json"
        test_file.write_text('{"key": "value"}')
        
        result = utils.load_json(test_file)
        self.assertEqual(result, {"key": "value"})
    
    def test_save_json(self):
        """测试保存 JSON 文件"""
        import utils
        
        test_file = self.temp_path / "subdir" / "test.json"
        utils.save_json(test_file, {"key": "value"})
        
        self.assertTrue(test_file.exists())
        content = json.loads(test_file.read_text())
        self.assertEqual(content, {"key": "value"})
    
    def test_get_today(self):
        """测试获取今天日期"""
        import utils
        
        today = utils.get_today()
        expected = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(today, expected)
    
    def test_get_month(self):
        """测试获取当前月份"""
        import utils
        
        month = utils.get_month()
        expected = datetime.now().strftime("%Y-%m")
        self.assertEqual(month, expected)
    
    def test_get_timestamp(self):
        """测试获取时间戳"""
        import utils
        
        timestamp = utils.get_timestamp()
        # ISO8601 格式包含 T
        self.assertIn("T", timestamp)
        # 应该可以解析
        datetime.fromisoformat(timestamp)
    
    def test_load_config_default(self):
        """测试加载默认配置"""
        import utils
        
        config = utils.load_config()
        
        self.assertTrue(config.get("enabled"))
        self.assertIn("prediction", config)
        self.assertIn("recording", config)
    
    def test_load_config_has_auto_execute(self):
        """测试配置包含自动执行选项"""
        import utils
        
        config = utils.load_config()
        auto_exec = config.get("prediction", {}).get("auto_execute", {})
        
        self.assertIn("enabled", auto_exec)
        self.assertIn("threshold", auto_exec)
        self.assertIn("allowed_actions", auto_exec)
        self.assertIn("forbidden_actions", auto_exec)
    
    def test_supported_ai_dirs(self):
        """测试支持的 AI 助手目录列表"""
        import utils
        
        # 确保支持多种 AI 助手
        self.assertIn(".cursor", utils.SUPPORTED_AI_DIRS)
        self.assertIn(".claude", utils.SUPPORTED_AI_DIRS)
        self.assertIn(".ai", utils.SUPPORTED_AI_DIRS)
        self.assertIn(".copilot", utils.SUPPORTED_AI_DIRS)
        self.assertIn(".codeium", utils.SUPPORTED_AI_DIRS)
    
    def test_get_project_root(self):
        """测试获取项目根目录"""
        import utils
        
        root = utils.get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())
    
    def test_get_ai_dir(self):
        """测试获取 AI 助手目录名称"""
        import utils
        
        ai_dir = utils.get_ai_dir()
        self.assertIn(ai_dir, utils.SUPPORTED_AI_DIRS)
    
    def test_get_data_dir_project(self):
        """测试获取项目级数据目录"""
        import utils
        
        data_dir = utils.get_data_dir("project")
        self.assertIsInstance(data_dir, Path)
        self.assertIn("behavior-prediction-data", str(data_dir))
    
    def test_get_data_dir_global(self):
        """测试获取全局数据目录"""
        import utils
        
        data_dir = utils.get_data_dir("global")
        self.assertIsInstance(data_dir, Path)
        self.assertIn("behavior-prediction-data", str(data_dir))
        # 全局目录应该在用户主目录下
        self.assertTrue(str(data_dir).startswith(str(Path.home())))
    
    def test_detect_project_info(self):
        """测试检测项目信息"""
        import utils
        
        info = utils.detect_project_info()
        
        self.assertIn("path", info)
        self.assertIn("name", info)
        self.assertIn("type", info)
        self.assertIn("tech_stack", info)
    
    def test_workflow_stages(self):
        """测试工作流程阶段定义"""
        import utils
        
        self.assertIn("design", utils.WORKFLOW_STAGES)
        self.assertIn("implement", utils.WORKFLOW_STAGES)
        self.assertIn("test", utils.WORKFLOW_STAGES)
        self.assertIn("debug", utils.WORKFLOW_STAGES)
        self.assertIn("commit", utils.WORKFLOW_STAGES)
    
    def test_get_retention_days(self):
        """测试获取数据保留天数"""
        import utils
        
        days = utils.get_retention_days()
        self.assertIsInstance(days, int)
    
    def test_should_retain_recent(self):
        """测试最近日期应该保留"""
        import utils
        
        today = utils.get_today()
        self.assertTrue(utils.should_retain(today))
    
    def test_ensure_dir_file_path(self):
        """测试确保文件路径的父目录存在"""
        import utils
        
        file_path = self.temp_path / "new_dir" / "file.json"
        utils.ensure_dir(file_path)
        
        self.assertTrue(file_path.parent.exists())
    
    def test_ensure_dir_directory(self):
        """测试确保目录存在"""
        import utils
        
        dir_path = self.temp_path / "new_dir"
        utils.ensure_dir(dir_path)
        
        self.assertTrue(dir_path.exists())


if __name__ == "__main__":
    unittest.main()
