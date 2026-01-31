#!/usr/bin/env python3
"""
测试 finalize_session.py 会话结束处理功能
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import unittest
import importlib


class TestFinalizeSession(unittest.TestCase):
    """测试会话结束处理功能"""
    
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
        import finalize_session
        importlib.reload(finalize_session)
    
    def tearDown(self):
        """测试后清理：删除临时目录"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 恢复模块
        import finalize_session
        importlib.reload(finalize_session)
    
    def test_finalize_session_empty(self):
        """测试空会话结束处理"""
        from finalize_session import finalize_session
        
        result = finalize_session({
            "actions_summary": [],
            "start_time": "2026-01-31T10:00:00Z",
            "end_time": "2026-01-31T11:00:00Z"
        })
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["actions_count"], 0)
    
    def test_finalize_session_with_actions(self):
        """测试有动作的会话结束处理"""
        from finalize_session import finalize_session
        
        result = finalize_session({
            "actions_summary": [
                {"type": "create_file", "tool": "Write"},
                {"type": "edit_file", "tool": "StrReplace"},
                {"type": "run_test", "tool": "Shell"}
            ],
            "start_time": "2026-01-31T10:00:00Z",
            "end_time": "2026-01-31T11:00:00Z"
        })
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["actions_count"], 3)
    
    def test_finalize_session_updates_matrix(self):
        """测试会话结束更新转移矩阵"""
        from finalize_session import finalize_session
        import utils
        
        finalize_session({
            "actions_summary": [
                {"type": "create_file", "tool": "Write"},
                {"type": "edit_file", "tool": "StrReplace"},
                {"type": "run_test", "tool": "Shell"}
            ]
        })
        
        matrix = utils.load_transition_matrix()
        
        # 检查转移矩阵是否更新
        self.assertIn("create_file", matrix["matrix"])
        self.assertIn("edit_file", matrix["matrix"]["create_file"])
        # 会话结束时权重是 0.5
        self.assertEqual(matrix["matrix"]["create_file"]["edit_file"]["count"], 0.5)
    
    def test_finalize_session_records_stats(self):
        """测试会话结束记录统计"""
        from finalize_session import finalize_session
        import utils
        
        finalize_session({
            "actions_summary": [
                {"type": "create_file", "tool": "Write"},
                {"type": "edit_file", "tool": "StrReplace"}
            ],
            "start_time": "2026-01-31T10:00:00Z",
            "end_time": "2026-01-31T11:00:00Z"
        })
        
        stats_file = utils.DATA_DIR / "stats" / "sessions.json"
        stats = utils.load_json(stats_file)
        
        self.assertEqual(stats["total_sessions"], 1)
        self.assertEqual(len(stats["sessions"]), 1)
        self.assertEqual(stats["sessions"][0]["actions_count"], 2)
    
    def test_finalize_session_supplements_missing(self):
        """测试会话结束补充遗漏的记录"""
        from finalize_session import supplement_missing_actions
        import utils
        
        # 先手动创建一些已有记录
        today = utils.get_today()
        log_file = utils.DATA_DIR / "actions" / f"{today}.json"
        utils.save_json(log_file, {
            "date": today,
            "actions": [
                {"type": "create_file", "tool": "Write", "id": f"{today}-001"}
            ]
        })
        
        # 会话结束时有新的动作类型（不同的 type:tool 组合）
        supplemented = supplement_missing_actions([
            {"type": "create_file", "tool": "Write"},  # 已存在（相同签名）
            {"type": "edit_file", "tool": "StrReplace"}  # 新的（不同签名）
        ])
        
        # 应该补充了 1 个（edit_file:StrReplace 是新的）
        self.assertEqual(supplemented, 1)
        
        # 检查日志
        log_data = utils.load_json(log_file)
        self.assertEqual(len(log_data["actions"]), 2)
    
    def test_finalize_session_limits_sessions(self):
        """测试会话统计限制为最近 100 条"""
        from finalize_session import record_session_stats
        import utils
        
        # 创建 105 条会话记录
        for i in range(105):
            record_session_stats(
                {"actions_summary": [{"type": f"action_{i}"}]},
                1
            )
        
        stats_file = utils.DATA_DIR / "stats" / "sessions.json"
        stats = utils.load_json(stats_file)
        
        # 应该只保留最近 100 条
        self.assertEqual(len(stats["sessions"]), 100)
        self.assertEqual(stats["total_sessions"], 105)


if __name__ == "__main__":
    unittest.main()
