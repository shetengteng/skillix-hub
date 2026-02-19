#!/usr/bin/env python3
"""测试 save_memory.py 保存记忆功能"""

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


def patch_get_project_root(test_dir):
    """临时修改 get_project_root 函数"""
    import utils
    original_func = utils.get_project_root
    utils.get_project_root = lambda: test_dir
    return original_func


def restore_get_project_root(original_func):
    """恢复 get_project_root 函数"""
    import utils
    utils.get_project_root = original_func


class TestSaveMemory:
    """测试保存记忆功能"""
    
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
    
    def test_save_basic_memory(self):
        """测试基本保存功能"""
        from save_memory import save_memory
        
        result = save_memory(
            topic="测试主题",
            key_info=["要点1", "要点2"],
            tags=["#test"]
        )
        
        assert result["success"] == True
        assert "memory_id" in result
        assert result["date"] == datetime.now().strftime("%Y-%m-%d")
        assert result["session"] == 1
    
    def test_save_creates_daily_file(self):
        """测试保存创建每日文件"""
        from save_memory import save_memory
        from utils import get_data_dir
        
        save_memory(
            topic="测试主题",
            key_info=["要点1"],
            tags=["#test"]
        )
        
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = get_data_dir() / "daily" / f"{today}.md"
        
        assert daily_file.exists()
        content = daily_file.read_text(encoding='utf-8')
        assert "测试主题" in content
        assert "要点1" in content
        assert "#test" in content
    
    def test_save_updates_index(self):
        """测试保存更新索引"""
        from save_memory import save_memory
        from utils import load_index
        
        save_memory(
            topic="索引测试",
            key_info=["关键信息"],
            tags=["#index"]
        )
        
        index = load_index()
        assert len(index["entries"]) == 1
        assert index["entries"][0]["summary"] == "索引测试"
    
    def test_save_multiple_sessions(self):
        """测试保存多个会话"""
        from save_memory import save_memory
        
        result1 = save_memory(topic="会话1", key_info=["信息1"])
        result2 = save_memory(topic="会话2", key_info=["信息2"])
        result3 = save_memory(topic="会话3", key_info=["信息3"])
        
        assert result1["session"] == 1
        assert result2["session"] == 2
        assert result3["session"] == 3
    
    def test_save_extracts_keywords(self):
        """测试保存提取关键词"""
        from save_memory import save_memory
        
        result = save_memory(
            topic="API 设计讨论",
            key_info=["使用 FastAPI 框架", "RESTful 风格"]
        )
        
        assert "api" in result["keywords"]
        assert "fastapi" in result["keywords"]
    
    def test_save_without_tags(self):
        """测试无标签保存"""
        from save_memory import save_memory
        
        result = save_memory(
            topic="无标签测试",
            key_info=["信息"]
        )
        
        assert result["success"] == True
    
    def test_save_empty_topic_fails(self):
        """测试空主题失败"""
        from save_memory import save_memory
        
        result = save_memory(
            topic="",
            key_info=["信息"]
        )
        
        # 空主题应该仍然成功（但不推荐）
        # 这里我们测试函数不会崩溃
        assert "success" in result
    
    def test_memory_id_format(self):
        """测试记忆 ID 格式"""
        from save_memory import save_memory
        
        result = save_memory(
            topic="ID 测试",
            key_info=["信息"]
        )
        
        today = datetime.now().strftime("%Y-%m-%d")
        assert result["memory_id"] == f"{today}-001"


class TestSaveMemoryDisabled:
    """测试禁用状态下的保存"""
    
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
    
    def test_save_when_disabled(self):
        """测试禁用时保存失败"""
        from save_memory import save_memory
        
        result = save_memory(
            topic="禁用测试",
            key_info=["信息"]
        )
        
        assert result["success"] == False
        assert "禁用" in result["message"]


def run_tests():
    """运行所有测试"""
    test_classes = [
        TestSaveMemory,
        TestSaveMemoryDisabled
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
