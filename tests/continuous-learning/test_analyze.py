#!/usr/bin/env python3
"""
analyze.py 测试用例（沙盒模式）
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent.parent / "skills" / "continuous-learning" / "scripts"
sys.path.insert(0, str(script_dir))

import utils as utils_module
from utils import ensure_data_dirs
from analyze import (
    analyze_observations,
    detect_user_corrections,
    detect_error_resolutions,
    detect_tool_preferences
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


class TestAnalyzeObservations:
    """analyze_observations 测试"""
    
    def test_empty_observations(self):
        """测试空观察列表"""
        result = analyze_observations([])
        
        assert result["pattern_count"] == 0
        assert result["user_corrections"] == []
        assert result["error_resolutions"] == []
        assert result["tool_preferences"] == []
    
    def test_basic_analysis(self):
        """测试基本分析"""
        observations = [
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Read"},
        ]
        
        result = analyze_observations(observations)
        
        assert "patterns_found" in result
        assert "pattern_count" in result


class TestDetectUserCorrections:
    """detect_user_corrections 测试"""
    
    def test_no_corrections(self):
        """测试没有纠正"""
        observations = [
            {"event": "tool_call", "tool": "Write"},
            {"event": "user_feedback", "content": "很好，继续"}
        ]
        
        result = detect_user_corrections(observations)
        assert len(result) == 0
    
    def test_detect_chinese_correction(self):
        """测试检测中文纠正"""
        observations = [
            {"event": "tool_call", "tool": "Write", "input": {"file": "test.py"}},
            {"event": "user_feedback", "content": "不要用 class，改成函数"}
        ]
        
        result = detect_user_corrections(observations)
        assert len(result) == 1
        assert result[0]["type"] == "user_correction"
    
    def test_detect_english_correction(self):
        """测试检测英文纠正"""
        observations = [
            {"event": "tool_call", "tool": "Write", "input": {"file": "test.py"}},
            {"event": "user_feedback", "content": "No, that's wrong. Should be async"}
        ]
        
        result = detect_user_corrections(observations)
        assert len(result) == 1
    
    def test_multiple_corrections(self):
        """测试多个纠正"""
        observations = [
            {"event": "tool_call", "tool": "Write"},
            {"event": "user_feedback", "content": "不对，改成这样"},
            {"event": "tool_call", "tool": "Write"},
            {"event": "user_feedback", "content": "还是不行，换个方法"}
        ]
        
        result = detect_user_corrections(observations)
        assert len(result) == 2


class TestDetectErrorResolutions:
    """detect_error_resolutions 测试"""
    
    def test_no_errors(self):
        """测试没有错误"""
        observations = [
            {"event": "tool_call", "tool": "Write", "exit_code": 0},
            {"event": "tool_call", "tool": "Read", "exit_code": 0}
        ]
        
        result = detect_error_resolutions(observations)
        assert len(result) == 0
    
    def test_detect_error_with_fix(self):
        """测试检测错误和修复"""
        observations = [
            {"event": "tool_call", "tool": "Shell", "exit_code": 1, "error": "ModuleNotFoundError"},
            {"event": "tool_call", "tool": "Shell", "input": "pip install module"}
        ]
        
        result = detect_error_resolutions(observations)
        assert len(result) == 1
        assert result[0]["type"] == "error_resolution"
    
    def test_detect_tool_error(self):
        """测试检测工具错误"""
        observations = [
            {"event": "tool_error", "error": "File not found"},
            {"event": "tool_call", "tool": "Write", "input": {"file": "missing.py"}}
        ]
        
        result = detect_error_resolutions(observations)
        assert len(result) == 1


class TestDetectToolPreferences:
    """detect_tool_preferences 测试"""
    
    def test_no_preferences(self):
        """测试没有偏好（使用次数不够）"""
        observations = [
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Read"}
        ]
        
        result = detect_tool_preferences(observations)
        assert len(result) == 0
    
    def test_detect_preference(self):
        """测试检测偏好"""
        observations = [
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Read"}
        ]
        
        result = detect_tool_preferences(observations)
        assert len(result) == 1
        assert result[0]["tool"] == "Write"
        assert result[0]["count"] == 4
    
    def test_multiple_preferences(self):
        """测试多个偏好"""
        observations = [
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Write"},
            {"event": "tool_call", "tool": "Shell"},
            {"event": "tool_call", "tool": "Shell"},
            {"event": "tool_call", "tool": "Shell"},
            {"event": "tool_call", "tool": "Read"}
        ]
        
        result = detect_tool_preferences(observations)
        # 两个工具都达到阈值
        assert len(result) >= 1


class TestCommandLine(SandboxMixin):
    """命令行接口测试"""

    def setup_method(self):
        self._setup_sandbox()

    def teardown_method(self):
        self._teardown_sandbox()
    
    def test_observations_command(self):
        """测试 --observations 命令"""
        import subprocess
        
        data = json.dumps([
            {"event": "tool_call", "tool": "Write"},
            {"event": "user_feedback", "content": "不对，改一下"}
        ])
        
        result = subprocess.run(
            ["python3", str(script_dir / "analyze.py"), "--observations", data],
            capture_output=True,
            text=True,
            env=self._get_sandbox_env()
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "patterns_found" in output
    
    def test_recent_command(self):
        """测试 --recent 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "analyze.py"), "--recent", "7"],
            capture_output=True,
            text=True,
            env=self._get_sandbox_env()
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "days_analyzed" in output or "status" in output


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestAnalyzeObservations,
        TestDetectUserCorrections,
        TestDetectErrorResolutions,
        TestDetectToolPreferences,
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
