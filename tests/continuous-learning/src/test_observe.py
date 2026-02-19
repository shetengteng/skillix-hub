#!/usr/bin/env python3
"""
observe.py 测试用例（沙盒模式）
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent.parent.parent / "skills" / "continuous-learning" / "scripts"
sys.path.insert(0, str(script_dir))

import utils as utils_module
from observe import handle_init, handle_record, handle_finalize
from utils import (
    clear_pending_session, load_pending_session,
    get_data_dir, ensure_data_dirs
)


class SandboxMixin:
    def _setup_sandbox(self):
        self._sandbox_dir = tempfile.mkdtemp()
        self._sandbox_path = Path(self._sandbox_dir)
        self._original_override = utils_module._data_dir_override
        utils_module._data_dir_override = self._sandbox_path / "continuous-learning-data"
        utils_module._data_dir_override.mkdir(parents=True, exist_ok=True)
        ensure_data_dirs()

    def _teardown_sandbox(self):
        utils_module._data_dir_override = self._original_override
        shutil.rmtree(self._sandbox_dir, ignore_errors=True)

    def _get_sandbox_env(self):
        env = os.environ.copy()
        env['CL_SANDBOX_DATA_DIR'] = str(self._sandbox_path / "continuous-learning-data")
        return env


class TestHandleInit(SandboxMixin):
    """handle_init 测试"""
    
    def setup_method(self):
        self._setup_sandbox()
    
    def teardown_method(self):
        self._teardown_sandbox()
    
    def test_init_creates_pending_session(self):
        """测试初始化创建 pending session"""
        result = handle_init()
        
        assert result["status"] == "success"
        
        # 验证 pending session 被创建
        pending = load_pending_session()
        assert pending is not None
    
    def test_init_returns_suggestions(self):
        """测试初始化返回建议"""
        result = handle_init()
        
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)
    
    def test_init_auto_finalizes_previous_session(self):
        """测试初始化自动 finalize 上一个会话"""
        # 创建一个有观察记录的 pending session
        from utils import save_pending_session, add_observation_to_pending
        
        save_pending_session({})
        add_observation_to_pending({"event": "test", "data": "test_data"})
        
        # 调用 init
        result = handle_init()
        
        assert result["status"] == "success"
        # 如果有自动 finalize，应该有相关信息
        # （取决于是否有足够的观察记录）


class TestHandleRecord(SandboxMixin):
    """handle_record 测试"""
    
    def setup_method(self):
        self._setup_sandbox()
    
    def teardown_method(self):
        self._teardown_sandbox()
    
    def test_record_observation(self):
        """测试记录观察"""
        data = {
            "event": "tool_call",
            "tool": "Write",
            "input": {"file": "test.py"}
        }
        
        result = handle_record(data)
        
        assert result["status"] == "success"
        
        # 验证观察被记录
        pending = load_pending_session()
        assert len(pending.get("observations", [])) == 1
    
    def test_record_multiple_observations(self):
        """测试记录多个观察"""
        for i in range(3):
            handle_record({"event": f"test_{i}"})
        
        pending = load_pending_session()
        assert len(pending.get("observations", [])) == 3
    
    def test_record_adds_timestamp(self):
        """测试记录添加时间戳"""
        handle_record({"event": "test"})
        
        pending = load_pending_session()
        obs = pending["observations"][0]
        assert "timestamp" in obs


class TestHandleFinalize(SandboxMixin):
    """handle_finalize 测试"""
    
    def setup_method(self):
        self._setup_sandbox()
    
    def teardown_method(self):
        self._teardown_sandbox()
    
    def test_finalize_empty_session(self):
        """测试 finalize 空会话"""
        result = handle_finalize({})
        
        assert result["status"] == "success"
        assert result.get("observation_count", 0) == 0
    
    def test_finalize_with_observations(self):
        """测试 finalize 有观察记录的会话"""
        # 先记录一些观察
        handle_record({"event": "test1"})
        handle_record({"event": "test2"})
        
        # Finalize
        result = handle_finalize({
            "topic": "测试会话",
            "summary": "这是一个测试"
        })
        
        assert result["status"] == "success"
        assert result.get("observation_count", 0) >= 2
    
    def test_finalize_clears_pending_session(self):
        """测试 finalize 清除 pending session"""
        handle_record({"event": "test"})
        
        # 验证有 pending session
        assert load_pending_session() is not None
        
        # Finalize
        handle_finalize({})
        
        # 验证 pending session 被清除
        assert load_pending_session() is None


class TestCommandLine(SandboxMixin):
    """命令行接口测试"""

    def setup_method(self):
        self._setup_sandbox()

    def teardown_method(self):
        self._teardown_sandbox()
    
    def test_init_command(self):
        """测试 --init 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "observe.py"), "--init"],
            capture_output=True,
            text=True,
            env=self._get_sandbox_env()
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
    
    def test_record_command(self):
        """测试 --record 命令"""
        import subprocess
        
        data = json.dumps({"event": "test"})
        result = subprocess.run(
            ["python3", str(script_dir / "observe.py"), "--record", data],
            capture_output=True,
            text=True,
            env=self._get_sandbox_env()
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
    
    def test_finalize_command(self):
        """测试 --finalize 命令"""
        import subprocess
        
        data = json.dumps({"topic": "测试"})
        result = subprocess.run(
            ["python3", str(script_dir / "observe.py"), "--finalize", data],
            capture_output=True,
            text=True,
            env=self._get_sandbox_env()
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
    
    def test_invalid_json(self):
        """测试无效 JSON"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "observe.py"), "--record", "invalid json"],
            capture_output=True,
            text=True,
            env=self._get_sandbox_env()
        )
        
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert output["status"] == "error"


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestHandleInit,
        TestHandleRecord,
        TestHandleFinalize,
        TestCommandLine
    ]
    
    total = 0
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        instance = test_class()
        
        # 获取所有测试方法
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total += 1
            method = getattr(instance, method_name)
            
            try:
                # 运行 setup
                if hasattr(instance, "setup_method"):
                    instance.setup_method()
                
                # 运行测试
                method()
                
                # 运行 teardown
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
