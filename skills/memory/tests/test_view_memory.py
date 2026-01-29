#!/usr/bin/env python3
"""测试 view_memory.py 查看记忆功能"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

# 创建临时测试目录
TEST_DIR = None


def setup_test_env():
    """设置测试环境"""
    global TEST_DIR
    TEST_DIR = Path(tempfile.mkdtemp())
    
    # 创建 .git 目录以模拟项目根目录
    (TEST_DIR / ".git").mkdir()
    
    # 创建 skills/memory 目录结构
    skill_dir = TEST_DIR / ".cursor" / "skills" / "memory"
    skill_dir.mkdir(parents=True)
    
    # 复制默认配置
    default_config = {
        "version": "1.0",
        "enabled": True,
        "auto_save": True,
        "auto_retrieve": True,
        "storage": {"location": "project-first", "retention_days": -1},
        "retrieval": {"max_candidates": 10, "max_results": 3, "search_scope_days": 30}
    }
    with open(skill_dir / "default_config.json", 'w') as f:
        json.dump(default_config, f)
    
    return TEST_DIR


def teardown_test_env():
    """清理测试环境"""
    global TEST_DIR
    if TEST_DIR and TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR = None


class TestViewMemory:
    """测试查看记忆功能"""
    
    def setup(self):
        """每个测试前的设置"""
        self.test_dir = setup_test_env()
        import utils
        self.original_func = utils.get_project_root
        utils.get_project_root = lambda: self.test_dir
    
    def teardown(self):
        """每个测试后的清理"""
        import utils
        utils.get_project_root = self.original_func
        teardown_test_env()
    
    def _create_test_memory(self, topic="测试主题", key_info=None, tags=None):
        """创建测试记忆"""
        from save_memory import save_memory
        if key_info is None:
            key_info = ["测试要点"]
        return save_memory(topic=topic, key_info=key_info, tags=tags)
    
    def test_view_today_empty(self):
        """测试查看今日记忆（空）"""
        from view_memory import view_memories_by_date
        
        result = view_memories_by_date()
        
        assert result["success"] == True
        assert result["count"] == 0
        assert result["memories"] == []
    
    def test_view_today_with_memories(self):
        """测试查看今日记忆（有记忆）"""
        from view_memory import view_memories_by_date
        
        # 创建记忆
        self._create_test_memory("主题1", ["要点1"])
        self._create_test_memory("主题2", ["要点2"])
        
        result = view_memories_by_date()
        
        assert result["success"] == True
        assert result["count"] == 2
        assert len(result["memories"]) == 2
    
    def test_view_specific_date(self):
        """测试查看指定日期记忆"""
        from view_memory import view_memories_by_date
        
        # 创建记忆
        self._create_test_memory("今日主题")
        
        today = datetime.now().strftime("%Y-%m-%d")
        result = view_memories_by_date(today)
        
        assert result["success"] == True
        assert result["date"] == today
        assert result["count"] == 1
    
    def test_view_nonexistent_date(self):
        """测试查看不存在日期的记忆"""
        from view_memory import view_memories_by_date
        
        result = view_memories_by_date("2099-01-01")
        
        assert result["success"] == True
        assert result["count"] == 0
    
    def test_view_memory_content(self):
        """测试查看记忆内容"""
        from view_memory import view_memories_by_date
        
        # 创建记忆
        self._create_test_memory("详细主题", ["详细要点1", "详细要点2"], ["#tag1"])
        
        result = view_memories_by_date()
        
        assert result["success"] == True
        assert len(result["memories"]) == 1
        
        memory = result["memories"][0]
        assert memory["summary"] == "详细主题"
        assert "详细主题" in memory["content"]
    
    def test_view_recent_memories(self):
        """测试查看最近记忆"""
        from view_memory import view_recent_memories
        
        # 创建记忆
        self._create_test_memory("最近主题1")
        self._create_test_memory("最近主题2")
        
        result = view_recent_memories(days=7)
        
        assert result["success"] == True
        assert result["total_count"] == 2
    
    def test_view_recent_empty(self):
        """测试查看最近记忆（空）"""
        from view_memory import view_recent_memories
        
        result = view_recent_memories(days=7)
        
        assert result["success"] == True
        assert result["total_count"] == 0
    
    def test_list_all_dates(self):
        """测试列出所有日期"""
        from view_memory import list_all_dates
        
        # 创建记忆
        self._create_test_memory("主题1")
        self._create_test_memory("主题2")
        
        result = list_all_dates()
        
        assert result["success"] == True
        assert result["total_dates"] == 1
        assert result["total_memories"] == 2
    
    def test_list_dates_empty(self):
        """测试列出日期（空）"""
        from view_memory import list_all_dates
        
        result = list_all_dates()
        
        assert result["success"] == True
        assert result["total_dates"] == 0
        assert result["total_memories"] == 0


class TestViewMemoryDisabled:
    """测试禁用状态下的查看"""
    
    def setup(self):
        """每个测试前的设置"""
        self.test_dir = setup_test_env()
        import utils
        self.original_func = utils.get_project_root
        utils.get_project_root = lambda: self.test_dir
        
        # 创建禁用的配置
        data_dir = self.test_dir / ".cursor" / "skills" / "memory-data"
        data_dir.mkdir(parents=True, exist_ok=True)
        config = {"enabled": False}
        with open(data_dir / "config.json", 'w') as f:
            json.dump(config, f)
    
    def teardown(self):
        """每个测试后的清理"""
        import utils
        utils.get_project_root = self.original_func
        teardown_test_env()
    
    def test_view_when_disabled(self):
        """测试禁用时查看失败"""
        from view_memory import view_memories_by_date
        
        result = view_memories_by_date()
        
        assert result["success"] == False
        assert "禁用" in result["message"]


def run_tests():
    """运行所有测试"""
    test_classes = [
        TestViewMemory,
        TestViewMemoryDisabled
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                total_tests += 1
                instance = test_class()
                try:
                    if hasattr(instance, 'setup'):
                        instance.setup()
                    getattr(instance, method_name)()
                    passed_tests += 1
                    print(f"✓ {test_class.__name__}.{method_name}")
                except AssertionError as e:
                    failed_tests.append((test_class.__name__, method_name, str(e)))
                    print(f"✗ {test_class.__name__}.{method_name}: {e}")
                except Exception as e:
                    failed_tests.append((test_class.__name__, method_name, str(e)))
                    print(f"✗ {test_class.__name__}.{method_name}: {e}")
                finally:
                    if hasattr(instance, 'teardown'):
                        try:
                            instance.teardown()
                        except:
                            pass
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    
    if failed_tests:
        print(f"\n失败的测试:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
