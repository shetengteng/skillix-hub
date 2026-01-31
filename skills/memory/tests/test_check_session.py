#!/usr/bin/env python3
"""
测试 check_session.py 会话检查功能
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


class TestCheckSession(unittest.TestCase):
    """测试会话检查功能"""
    
    def setUp(self):
        """测试前准备：创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的数据目录
        import utils
        self.original_get_data_dir = utils.get_data_dir
        self.original_get_project_root = utils.get_project_root
        
        # Mock get_data_dir
        def mock_get_data_dir(location="project"):
            return self.temp_path / "memory-data"
        
        def mock_get_project_root():
            return self.temp_path
        
        utils.get_data_dir = mock_get_data_dir
        utils.get_project_root = mock_get_project_root
        
        # 重新加载依赖 utils 的模块
        import check_session
        importlib.reload(check_session)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.get_data_dir = self.original_get_data_dir
        utils.get_project_root = self.original_get_project_root
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 恢复模块
        import check_session
        importlib.reload(check_session)
    
    def test_check_session_empty(self):
        """测试空数据的会话检查"""
        from check_session import check_session
        
        result = check_session()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["total_memories"], 0)
        self.assertEqual(result["summary"]["today_count"], 0)
        self.assertEqual(len(result["recent_memories"]), 0)
        # 应该有首次使用的建议
        self.assertTrue(len(result["suggestions"]) > 0)
        self.assertEqual(result["suggestions"][0]["type"], "info")
    
    def test_check_session_with_data(self):
        """测试有数据的会话检查"""
        from check_session import check_session
        import utils
        
        # 初始化数据目录
        utils.initialize_data_dir()
        
        # 创建一些测试数据
        index = utils.load_index()
        today = datetime.now().strftime("%Y-%m-%d")
        index["entries"] = [
            {
                "id": f"{today}-001",
                "date": today,
                "session": 1,
                "keywords": ["test", "memory"],
                "summary": "测试记忆",
                "tags": ["#test"]
            }
        ]
        utils.save_index(index)
        
        result = check_session()
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"]["total_memories"], 1)
        self.assertEqual(result["summary"]["today_count"], 1)
        self.assertEqual(len(result["recent_memories"]), 1)
        self.assertEqual(result["recent_memories"][0]["id"], f"{today}-001")
    
    def test_get_data_summary(self):
        """测试获取数据摘要"""
        from check_session import get_data_summary
        import utils
        
        utils.initialize_data_dir()
        data_dir = utils.get_data_dir()
        index = utils.load_index()
        
        summary = get_data_summary(index, data_dir, "project")
        
        self.assertIn("total_memories", summary)
        self.assertIn("total_days", summary)
        self.assertIn("today_count", summary)
        self.assertIn("file_count", summary)
        self.assertIn("data_dir", summary)
        self.assertEqual(summary["location"], "project")
    
    def test_get_recent_memories(self):
        """测试获取最近记忆"""
        from check_session import get_recent_memories
        import utils
        
        utils.initialize_data_dir()
        index = utils.load_index()
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        
        index["entries"] = [
            {"id": f"{today}-001", "date": today, "summary": "今天的记忆", "tags": []},
            {"id": f"{yesterday}-001", "date": yesterday, "summary": "昨天的记忆", "tags": []},
            {"id": f"{old_date}-001", "date": old_date, "summary": "10天前的记忆", "tags": []}
        ]
        
        # 获取最近 7 天的记忆
        recent = get_recent_memories(index, days=7)
        
        # 应该只有今天和昨天的记忆
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["id"], f"{today}-001")  # 按日期倒序
        self.assertEqual(recent[1]["id"], f"{yesterday}-001")
    
    def test_cleanup_old_memories(self):
        """测试清理过期记忆"""
        from check_session import cleanup_old_memories
        import utils
        
        utils.initialize_data_dir()
        data_dir = utils.get_data_dir()
        index = utils.load_index()
        
        today = datetime.now().strftime("%Y-%m-%d")
        old_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        
        index["entries"] = [
            {"id": f"{today}-001", "date": today, "summary": "今天的记忆", "tags": []},
            {"id": f"{old_date}-001", "date": old_date, "summary": "100天前的记忆", "tags": []}
        ]
        
        # 清理 90 天前的记忆
        cleaned = cleanup_old_memories(index, data_dir, 90, "project")
        
        self.assertEqual(cleaned, 1)
        self.assertEqual(len(index["entries"]), 1)
        self.assertEqual(index["entries"][0]["id"], f"{today}-001")
    
    def test_generate_suggestions_first_use(self):
        """测试首次使用的建议"""
        from check_session import generate_suggestions
        
        summary = {"total_memories": 0, "today_count": 0}
        recent = []
        
        suggestions = generate_suggestions(summary, recent)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "info")
        self.assertIn("第一次", suggestions[0]["message"])
    
    def test_generate_suggestions_context(self):
        """测试上下文建议"""
        from check_session import generate_suggestions
        
        summary = {"total_memories": 10, "today_count": 0}
        recent = [{"id": "2026-01-30-001", "summary": "测试"}]
        
        suggestions = generate_suggestions(summary, recent)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "context")
    
    def test_generate_suggestions_many_memories(self):
        """测试大量记忆的建议"""
        from check_session import generate_suggestions
        
        summary = {"total_memories": 150, "today_count": 5}
        recent = []
        
        suggestions = generate_suggestions(summary, recent)
        
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "tip")
        self.assertIn("retention_days", suggestions[0]["message"])


if __name__ == "__main__":
    unittest.main()
