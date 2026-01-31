#!/usr/bin/env python3
"""
测试 utils.py 工具函数
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
        
        self.assertTrue((utils.DATA_DIR / "actions").exists())
        self.assertTrue((utils.DATA_DIR / "patterns").exists())
        self.assertTrue((utils.DATA_DIR / "stats").exists())
    
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
    
    def test_get_timestamp(self):
        """测试获取时间戳"""
        import utils
        
        timestamp = utils.get_timestamp()
        self.assertTrue(timestamp.endswith("Z"))
        self.assertIn("T", timestamp)
    
    def test_load_config_default(self):
        """测试加载默认配置"""
        import utils
        
        config = utils.load_config()
        
        self.assertTrue(config.get("enabled"))
        self.assertIn("prediction", config)
        self.assertIn("recording", config)
    
    def test_load_transition_matrix_empty(self):
        """测试加载空转移矩阵"""
        import utils
        
        matrix = utils.load_transition_matrix()
        
        self.assertEqual(matrix.get("version"), "1.0")
        self.assertEqual(matrix.get("matrix"), {})
        self.assertEqual(matrix.get("total_transitions"), 0)
    
    def test_save_transition_matrix(self):
        """测试保存转移矩阵"""
        import utils
        
        utils.ensure_data_dirs()
        
        matrix = {
            "version": "1.0",
            "matrix": {"a": {"b": {"count": 1, "probability": 1.0}}},
            "total_transitions": 1
        }
        utils.save_transition_matrix(matrix)
        
        loaded = utils.load_transition_matrix()
        self.assertEqual(loaded["matrix"], matrix["matrix"])
        self.assertIn("updated_at", loaded)
    
    def test_register_action_type_new(self):
        """测试注册新动作类型"""
        import utils
        
        utils.ensure_data_dirs()
        
        utils.register_action_type("test_action", "测试动作", is_new=True)
        
        registry = utils.load_types_registry()
        self.assertIn("test_action", registry["types"])
        self.assertEqual(registry["types"]["test_action"]["source"], "auto_generated")
        self.assertEqual(registry["types"]["test_action"]["count"], 1)
    
    def test_register_action_type_existing(self):
        """测试注册已存在的动作类型"""
        import utils
        
        utils.ensure_data_dirs()
        
        # 注册两次
        utils.register_action_type("test_action")
        utils.register_action_type("test_action")
        
        registry = utils.load_types_registry()
        self.assertEqual(registry["types"]["test_action"]["count"], 2)
    
    def test_get_recent_actions_empty(self):
        """测试获取空的最近动作"""
        import utils
        
        utils.ensure_data_dirs()
        
        recent = utils.get_recent_actions()
        self.assertEqual(recent, [])
    
    def test_collect_context(self):
        """测试收集上下文"""
        import utils
        
        context = utils.collect_context()
        
        self.assertIn("date", context)
        self.assertIn("time", context)
    
    def test_supported_skills_dirs(self):
        """测试支持的 AI 助手目录列表"""
        import utils
        
        # 确保支持多种 AI 助手
        self.assertIn(".cursor", utils.SUPPORTED_SKILLS_DIRS)
        self.assertIn(".claude", utils.SUPPORTED_SKILLS_DIRS)
        self.assertIn(".ai", utils.SUPPORTED_SKILLS_DIRS)
        self.assertIn(".copilot", utils.SUPPORTED_SKILLS_DIRS)
        self.assertIn(".codeium", utils.SUPPORTED_SKILLS_DIRS)
    
    def test_get_project_root(self):
        """测试获取项目根目录"""
        import utils
        
        root = utils.get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())
    
    def test_get_skills_base_dir(self):
        """测试获取 AI 助手目录名称"""
        import utils
        
        base_dir = utils.get_skills_base_dir()
        self.assertIn(base_dir, utils.SUPPORTED_SKILLS_DIRS)
    
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


if __name__ == "__main__":
    unittest.main()
