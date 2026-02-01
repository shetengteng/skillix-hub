#!/usr/bin/env python3
"""
utils.py 测试用例
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from utils import (
    get_timestamp, get_date_str, get_month_str, calculate_days_since,
    load_pending_session, save_pending_session, clear_pending_session,
    add_observation_to_pending, parse_instinct_file, generate_instinct_file,
    load_skills_index, save_skills_index, add_skill_to_index, remove_skill_from_index,
    get_default_config
)


class TestTimeUtils:
    """时间工具测试"""
    
    def test_get_timestamp(self):
        """测试获取时间戳"""
        ts = get_timestamp()
        assert ts is not None
        assert "T" in ts  # ISO8601 格式
        # 验证可以解析
        datetime.fromisoformat(ts)
    
    def test_get_date_str(self):
        """测试获取日期字符串"""
        date_str = get_date_str()
        assert len(date_str) == 10  # YYYY-MM-DD
        assert date_str.count("-") == 2
    
    def test_get_month_str(self):
        """测试获取月份字符串"""
        month_str = get_month_str()
        assert len(month_str) == 7  # YYYY-MM
        assert month_str.count("-") == 1
    
    def test_calculate_days_since(self):
        """测试计算天数"""
        # 今天
        today = get_timestamp()
        assert calculate_days_since(today) == 0
        
        # 空值
        assert calculate_days_since("") == float('inf')
        assert calculate_days_since(None) == float('inf')


class TestPendingSession:
    """Pending Session 测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_save_and_load_pending_session(self):
        """测试保存和加载 pending session"""
        # 保存
        save_pending_session({"test": "data"})
        
        # 加载
        pending = load_pending_session()
        assert pending is not None
        assert pending.get("test") == "data"
        assert "session_start" in pending
        assert "observations" in pending
    
    def test_clear_pending_session(self):
        """测试清除 pending session"""
        save_pending_session({"test": "data"})
        assert load_pending_session() is not None
        
        clear_pending_session()
        assert load_pending_session() is None
    
    def test_add_observation_to_pending(self):
        """测试添加观察记录"""
        # 添加第一个观察
        add_observation_to_pending({"event": "test1"})
        pending = load_pending_session()
        assert len(pending.get("observations", [])) == 1
        
        # 添加第二个观察
        add_observation_to_pending({"event": "test2"})
        pending = load_pending_session()
        assert len(pending.get("observations", [])) == 2
        
        # 验证时间戳被添加
        assert "timestamp" in pending["observations"][0]


class TestInstinctFile:
    """本能文件解析测试"""
    
    def test_parse_instinct_file(self):
        """测试解析本能文件"""
        content = """---
id: test-instinct
trigger: "测试触发条件"
confidence: 0.7
domain: "testing"
evidence_count: 3
---

# 测试本能

## 行为
这是测试行为。
"""
        result = parse_instinct_file(content)
        
        assert result["id"] == "test-instinct"
        assert result["trigger"] == "测试触发条件"
        assert result["confidence"] == 0.7
        assert result["domain"] == "testing"
        assert result["evidence_count"] == 3
        assert "测试本能" in result["content"]
    
    def test_parse_instinct_file_minimal(self):
        """测试解析最小本能文件"""
        content = """---
id: minimal
---

内容
"""
        result = parse_instinct_file(content)
        assert result["id"] == "minimal"
        assert "内容" in result["content"]
    
    def test_generate_instinct_file(self):
        """测试生成本能文件"""
        instinct = {
            "id": "test-instinct",
            "trigger": "测试触发条件",
            "confidence": 0.7,
            "domain": "testing",
            "content": "# 测试本能\n\n## 行为\n测试行为"
        }
        
        content = generate_instinct_file(instinct)
        
        assert "id: test-instinct" in content
        assert "confidence: 0.7" in content
        assert "# 测试本能" in content
    
    def test_roundtrip(self):
        """测试解析和生成的往返"""
        original = {
            "id": "roundtrip-test",
            "trigger": "往返测试",
            "confidence": 0.8,
            "domain": "test",
            "content": "# 测试\n\n内容"
        }
        
        # 生成
        content = generate_instinct_file(original)
        
        # 解析
        parsed = parse_instinct_file(content)
        
        assert parsed["id"] == original["id"]
        assert parsed["trigger"] == original["trigger"]
        assert parsed["confidence"] == original["confidence"]


class TestSkillsIndex:
    """技能索引测试"""
    
    def test_load_empty_index(self):
        """测试加载空索引"""
        index = load_skills_index()
        assert "skills" in index
        assert isinstance(index["skills"], list)
    
    def test_add_and_remove_skill(self):
        """测试添加和移除技能"""
        skill_info = {
            "name": "test-skill",
            "path": "/test/path",
            "triggers": ["test"]
        }
        
        # 添加
        add_skill_to_index(skill_info)
        index = load_skills_index()
        
        found = [s for s in index["skills"] if s["name"] == "test-skill"]
        assert len(found) == 1
        
        # 移除
        remove_skill_from_index("test-skill")
        index = load_skills_index()
        
        found = [s for s in index["skills"] if s["name"] == "test-skill"]
        assert len(found) == 0


class TestDefaultConfig:
    """默认配置测试"""
    
    def test_get_default_config(self):
        """测试获取默认配置"""
        config = get_default_config()
        
        assert config["version"] == "1.0"
        assert config["enabled"] == True
        assert "observation" in config
        assert "detection" in config
        assert "instincts" in config
        assert "evolution" in config
    
    def test_default_config_values(self):
        """测试默认配置值"""
        config = get_default_config()
        
        assert config["observation"]["retention_days"] == 90
        assert config["detection"]["min_evidence_count"] == 2
        assert config["instincts"]["min_confidence"] == 0.3
        assert config["evolution"]["cluster_threshold"] == 3


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestTimeUtils,
        TestPendingSession,
        TestInstinctFile,
        TestSkillsIndex,
        TestDefaultConfig
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
