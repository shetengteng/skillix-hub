#!/usr/bin/env python3
"""测试 delete_memory.py 删除记忆功能"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

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


class TestDeleteMemory:
    """测试删除记忆功能"""
    
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
    
    def _create_test_memory(self, topic="测试主题", key_info=None):
        """创建测试记忆"""
        from save_memory import save_memory
        if key_info is None:
            key_info = ["测试要点"]
        return save_memory(topic=topic, key_info=key_info)
    
    def test_delete_by_id(self):
        """测试按 ID 删除"""
        from delete_memory import delete_memory_by_id
        
        # 先创建记忆
        result = self._create_test_memory()
        memory_id = result["memory_id"]
        
        # 删除记忆
        delete_result = delete_memory_by_id(memory_id)
        
        assert delete_result["success"] == True
        assert delete_result["memory_id"] == memory_id
        assert delete_result["deleted_from_index"] == True
    
    def test_delete_nonexistent_id(self):
        """测试删除不存在的 ID"""
        from delete_memory import delete_memory_by_id
        
        result = delete_memory_by_id("2099-01-01-999")
        
        assert result["success"] == False
        assert "未找到" in result["message"]
    
    def test_delete_by_date(self):
        """测试按日期删除"""
        from delete_memory import delete_memories_by_date
        from utils import load_index
        
        # 创建多个记忆
        self._create_test_memory("主题1")
        self._create_test_memory("主题2")
        self._create_test_memory("主题3")
        
        # 验证创建成功
        index = load_index()
        assert len(index["entries"]) == 3
        
        # 按日期删除
        today = datetime.now().strftime("%Y-%m-%d")
        result = delete_memories_by_date(today)
        
        assert result["success"] == True
        assert result["deleted_count"] == 3
        
        # 验证删除成功
        index = load_index()
        assert len(index["entries"]) == 0
    
    def test_delete_nonexistent_date(self):
        """测试删除不存在日期的记忆"""
        from delete_memory import delete_memories_by_date
        
        result = delete_memories_by_date("2099-01-01")
        
        assert result["success"] == False
        assert "未找到" in result["message"]
    
    def test_clear_all_without_confirm(self):
        """测试清空所有记忆（无确认）"""
        from delete_memory import clear_all_memories
        
        # 创建记忆
        self._create_test_memory()
        
        # 尝试清空（无确认）
        result = clear_all_memories(confirm=False)
        
        assert result["success"] == False
        assert "确认" in result["message"]
    
    def test_clear_all_with_confirm(self):
        """测试清空所有记忆（有确认）"""
        from delete_memory import clear_all_memories
        from utils import load_index
        
        # 创建多个记忆
        self._create_test_memory("主题1")
        self._create_test_memory("主题2")
        
        # 清空（有确认）
        result = clear_all_memories(confirm=True)
        
        assert result["success"] == True
        assert result["deleted_count"] == 2
        
        # 验证清空成功
        index = load_index()
        assert len(index["entries"]) == 0
    
    def test_delete_updates_index(self):
        """测试删除后索引更新"""
        from delete_memory import delete_memory_by_id
        from utils import load_index
        
        # 创建多个记忆
        result1 = self._create_test_memory("主题1")
        result2 = self._create_test_memory("主题2")
        
        # 删除第一个
        delete_memory_by_id(result1["memory_id"])
        
        # 验证索引只剩一个
        index = load_index()
        assert len(index["entries"]) == 1
        assert index["entries"][0]["summary"] == "主题2"


class TestDeleteMemoryDisabled:
    """测试禁用状态下的删除"""
    
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
    
    def test_delete_when_disabled(self):
        """测试禁用时删除失败"""
        from delete_memory import delete_memory_by_id
        
        result = delete_memory_by_id("2026-01-29-001")
        
        assert result["success"] == False
        assert "禁用" in result["message"]


def run_tests():
    """运行所有测试"""
    test_classes = [
        TestDeleteMemory,
        TestDeleteMemoryDisabled
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
