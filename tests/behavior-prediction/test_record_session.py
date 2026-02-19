#!/usr/bin/env python3
"""
测试 record_session.py - 会话记录功能测试
"""

import json
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "skills" / "behavior-prediction" / "scripts"))


class TestRecordSession(unittest.TestCase):
    """测试会话记录功能"""
    
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
    
    def test_record_session_success(self):
        """测试会话记录成功"""
        from record_session import record_session
        
        session_data = {
            "session_summary": {
                "topic": "测试会话",
                "workflow_stages": ["implement", "test"]
            },
            "operations": {
                "files": {"created": ["test.py"], "modified": [], "deleted": []},
                "commands": ["pytest"]
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
        
        session_id = record_session(session_data)
        
        self.assertTrue(session_id.startswith("sess_"))
        self.assertIn("_", session_id)
    
    def test_session_id_format(self):
        """测试会话 ID 格式"""
        from record_session import record_session
        
        session_data = {
            "session_summary": {"topic": "测试"},
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {}
        }
        
        session_id = record_session(session_data)
        
        # 格式应该是 sess_YYYYMMDD_NNN
        parts = session_id.split("_")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "sess")
        self.assertEqual(len(parts[1]), 8)  # YYYYMMDD
        self.assertEqual(len(parts[2]), 3)  # NNN
    
    def test_session_file_created(self):
        """测试会话文件创建"""
        from record_session import record_session
        import utils
        
        session_data = {
            "session_summary": {"topic": "测试"},
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
        }
        
        session_id = record_session(session_data)
        
        # 检查文件是否创建
        month_str = datetime.now().strftime("%Y-%m")
        session_file = utils.DATA_DIR / "sessions" / month_str / f"{session_id}.json"
        self.assertTrue(session_file.exists())
    
    def test_session_index_updated(self):
        """测试会话索引更新"""
        from record_session import record_session
        import utils
        
        session_data = {
            "session_summary": {
                "topic": "测试主题",
                "tags": ["#test"],
                "workflow_stages": ["implement"]
            },
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {}
        }
        
        record_session(session_data)
        
        # 检查索引是否更新
        index_file = utils.DATA_DIR / "index" / "sessions_index.json"
        self.assertTrue(index_file.exists())
        
        index = utils.load_json(index_file)
        self.assertEqual(len(index["sessions"]), 1)
        self.assertEqual(index["sessions"][0]["topic"], "测试主题")
    
    def test_multiple_sessions_increment(self):
        """测试多次会话序号递增"""
        from record_session import record_session
        
        session_data = {
            "session_summary": {"topic": "测试"},
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {}
        }
        
        session_id_1 = record_session(session_data)
        session_id_2 = record_session(session_data)
        session_id_3 = record_session(session_data)
        
        # 序号应该递增
        num_1 = int(session_id_1.split("_")[2])
        num_2 = int(session_id_2.split("_")[2])
        num_3 = int(session_id_3.split("_")[2])
        
        self.assertEqual(num_2, num_1 + 1)
        self.assertEqual(num_3, num_2 + 1)
    
    def test_get_session_count_today(self):
        """测试获取今日会话数"""
        from record_session import record_session, get_session_count_today
        
        # 初始应该是 0
        self.assertEqual(get_session_count_today(), 0)
        
        session_data = {
            "session_summary": {"topic": "测试"},
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {}
        }
        
        record_session(session_data)
        self.assertEqual(get_session_count_today(), 1)
        
        record_session(session_data)
        self.assertEqual(get_session_count_today(), 2)
    
    def test_get_recent_sessions(self):
        """测试获取最近会话"""
        from record_session import record_session, get_recent_sessions
        
        # 记录几个会话
        for i in range(5):
            session_data = {
                "session_summary": {"topic": f"测试 {i+1}"},
                "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
                "conversation": {"user_messages": [], "message_count": 0},
                "time": {}
            }
            record_session(session_data)
        
        # 获取最近 3 个
        recent = get_recent_sessions(3)
        self.assertEqual(len(recent), 3)
        
        # 获取所有
        all_sessions = get_recent_sessions(10)
        self.assertEqual(len(all_sessions), 5)
    
    def test_duration_calculation(self):
        """测试时长计算"""
        from record_session import record_session
        import utils
        
        session_data = {
            "session_summary": {"topic": "测试"},
            "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
            "conversation": {"user_messages": [], "message_count": 0},
            "time": {
                "start": "2026-01-31T10:00:00Z",
                "end": "2026-01-31T10:30:00Z"
            }
        }
        
        session_id = record_session(session_data)
        
        # 读取会话文件检查时长
        month_str = datetime.now().strftime("%Y-%m")
        session_file = utils.DATA_DIR / "sessions" / month_str / f"{session_id}.json"
        session_record = utils.load_json(session_file)
        
        self.assertEqual(session_record["time"]["duration_minutes"], 30)


if __name__ == "__main__":
    unittest.main()
