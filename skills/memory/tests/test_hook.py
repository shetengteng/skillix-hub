#!/usr/bin/env python3
"""
hook.py 测试用例
"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from hook import handle_init, handle_save, handle_finalize, handle_status
from utils import (
    clear_pending_session, load_pending_session, get_temp_memories,
    get_data_dir
)


class TestHandleInit:
    """handle_init 测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_init_creates_pending_session(self):
        """测试初始化创建 pending session"""
        result = handle_init()
        
        assert result["status"] == "success"
        assert "session_start" in result
        
        # 验证 pending session 被创建
        pending = load_pending_session()
        assert pending is not None
    
    def test_init_returns_config_status(self):
        """测试初始化返回配置状态"""
        result = handle_init()
        
        assert "save_trigger_enabled" in result
        assert "temp_memory_enabled" in result


class TestHandleSave:
    """handle_save 测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
        handle_init()  # 初始化会话
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_save_with_trigger_keyword(self):
        """测试有触发关键词时保存"""
        data = {
            "user_message": "我们决定使用 FastAPI",
            "topic": "技术选型",
            "key_info": ["使用 FastAPI"],
            "tags": ["#decision"]
        }
        
        result = handle_save(data)
        
        assert result["status"] == "success"
        assert result["trigger_keyword"] == "决定"
        assert result["trigger_category"] == "decision"
        
        # 验证临时记忆被保存
        temp_memories = get_temp_memories()
        assert len(temp_memories) == 1
    
    def test_save_without_trigger_keyword(self):
        """测试无触发关键词时跳过"""
        data = {
            "user_message": "今天天气不错",
        }
        
        result = handle_save(data)
        
        assert result["status"] == "skipped"
        assert result["reason"] == "no_trigger_keyword"
    
    def test_save_with_force(self):
        """测试强制保存"""
        data = {
            "user_message": "今天天气不错",
            "force": True
        }
        
        result = handle_save(data)
        
        assert result["status"] == "success"
    
    def test_save_multiple_memories(self):
        """测试保存多个临时记忆"""
        messages = [
            "我们决定使用 FastAPI",
            "API 前缀配置为 /api/v2",
            "下一步要实现认证"
        ]
        
        for msg in messages:
            handle_save({"user_message": msg})
        
        temp_memories = get_temp_memories()
        assert len(temp_memories) == 3


class TestHandleFinalize:
    """handle_finalize 测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
        handle_init()
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_finalize_empty_session(self):
        """测试 finalize 空会话"""
        result = handle_finalize()
        
        assert result["status"] == "success"
        assert result["memory_count"] == 0
    
    def test_finalize_with_memories(self):
        """测试 finalize 有记忆的会话"""
        # 先保存一些记忆
        handle_save({"user_message": "我们决定使用 FastAPI"})
        handle_save({"user_message": "API 前缀配置为 /api/v2"})
        
        result = handle_finalize({"topic": "技术讨论"})
        
        assert result["status"] == "success"
        assert result["memory_count"] == 2
        
        # 验证 pending session 被清除
        assert load_pending_session() is None
    
    def test_finalize_creates_daily_file(self):
        """测试 finalize 创建每日文件"""
        from datetime import datetime
        
        handle_save({"user_message": "我们决定使用 FastAPI"})
        result = handle_finalize()
        
        assert result["status"] == "success"
        
        # 验证文件存在
        if "summarize_result" in result:
            file_path = result["summarize_result"].get("file_path")
            if file_path:
                assert Path(file_path).exists()


class TestHandleStatus:
    """handle_status 测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_status_no_session(self):
        """测试无会话时的状态"""
        result = handle_status()
        
        assert result["status"] == "no_session"
    
    def test_status_active_session(self):
        """测试有活跃会话时的状态"""
        handle_init()
        
        result = handle_status()
        
        assert result["status"] == "active"
        assert "session_start" in result
        assert "temp_memory_count" in result
    
    def test_status_with_memories(self):
        """测试有记忆时的状态"""
        handle_init()
        handle_save({"user_message": "我们决定使用 FastAPI"})
        
        result = handle_status()
        
        assert result["status"] == "active"
        assert result["temp_memory_count"] == 1
        assert len(result["recent_memories"]) == 1


class TestCommandLine:
    """命令行接口测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_init_command(self):
        """测试 --init 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "hook.py"), "--init"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
    
    def test_save_command(self):
        """测试 --save 命令"""
        import subprocess
        
        # 先初始化
        subprocess.run(
            ["python3", str(script_dir / "hook.py"), "--init"],
            capture_output=True
        )
        
        # 保存
        data = json.dumps({"user_message": "我们决定使用 FastAPI"})
        result = subprocess.run(
            ["python3", str(script_dir / "hook.py"), "--save", data],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
    
    def test_status_command(self):
        """测试 --status 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "hook.py"), "--status"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "status" in output


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestHandleInit,
        TestHandleSave,
        TestHandleFinalize,
        TestHandleStatus,
        TestCommandLine
    ]
    
    total = 0
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        instance = test_class()
        
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total += 1
            method = getattr(instance, method_name)
            
            try:
                if hasattr(instance, "setup_method"):
                    instance.setup_method()
                
                method()
                
                if hasattr(instance, "teardown_method"):
                    instance.teardown_method()
                
                print(f"✅ {test_class.__name__}.{method_name}")
                passed += 1
            except Exception as e:
                print(f"❌ {test_class.__name__}.{method_name}")
                print(f"   Error: {e}")
                traceback.print_exc()
                failed += 1
    
    print(f"\n总计: {total}, 通过: {passed}, 失败: {failed}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
