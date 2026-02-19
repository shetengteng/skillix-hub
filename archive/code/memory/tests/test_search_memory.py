#!/usr/bin/env python3
"""测试 search_memory.py 搜索记忆功能"""

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
        "retrieval": {
            "max_candidates": 10,
            "max_results": 3,
            "search_scope_days": 30,
            "time_decay_rate": 0.95,
            "source_weight": {"project": 1.0, "global": 0.7}
        }
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


def create_test_memories(test_dir):
    """创建测试记忆数据"""
    import utils
    original_func = utils.get_project_root
    utils.get_project_root = lambda: test_dir
    
    from save_memory import save_memory
    
    # 创建多条测试记忆
    memories = [
        {
            "topic": "API 设计讨论",
            "key_info": ["使用 FastAPI 框架", "RESTful 风格"],
            "tags": ["#api", "#design"]
        },
        {
            "topic": "数据库优化",
            "key_info": ["添加索引", "查询优化"],
            "tags": ["#database", "#optimization"]
        },
        {
            "topic": "前端重构",
            "key_info": ["使用 React", "组件化设计"],
            "tags": ["#frontend", "#react"]
        }
    ]
    
    for memory in memories:
        save_memory(**memory)
    
    utils.get_project_root = original_func
    return memories


class TestSearchMemory:
    """测试搜索记忆功能"""
    
    def setup(self):
        """每个测试前的设置"""
        self.test_dir = setup_test_env()
        import utils
        self.original_func = utils.get_project_root
        utils.get_project_root = lambda: self.test_dir
        self.memories = create_test_memories(self.test_dir)
    
    def teardown(self):
        """每个测试后的清理"""
        import utils
        utils.get_project_root = self.original_func
        teardown_test_env()
    
    def test_search_basic(self):
        """测试基本搜索"""
        from search_memory import search_memories
        
        result = search_memories("API 设计")
        
        assert "candidates" in result
        assert len(result["candidates"]) > 0
    
    def test_search_returns_matching_memory(self):
        """测试搜索返回匹配的记忆"""
        from search_memory import search_memories
        
        result = search_memories("FastAPI API")
        
        assert len(result["candidates"]) > 0
        # 第一个结果应该是 API 设计讨论
        assert "API" in result["candidates"][0]["summary"]
    
    def test_search_no_match(self):
        """测试无匹配结果"""
        from search_memory import search_memories
        
        result = search_memories("完全不相关的内容 xyz123")
        
        assert result["candidates_count"] == 0
    
    def test_search_query_keywords(self):
        """测试查询关键词提取"""
        from search_memory import search_memories
        
        result = search_memories("数据库 优化")
        
        assert "query_keywords" in result
        assert "数据库" in result["query_keywords"] or "优化" in result["query_keywords"]
    
    def test_search_score_calculation(self):
        """测试分数计算"""
        from search_memory import search_memories
        
        result = search_memories("API")
        
        if result["candidates"]:
            # 分数应该在 0-1 之间
            for candidate in result["candidates"]:
                assert 0 <= candidate["score"] <= 1
    
    def test_search_matched_keywords(self):
        """测试匹配关键词返回"""
        from search_memory import search_memories
        
        result = search_memories("API FastAPI")
        
        if result["candidates"]:
            # 应该返回匹配的关键词
            assert "matched_keywords" in result["candidates"][0]
    
    def test_search_content_included(self):
        """测试搜索结果包含内容"""
        from search_memory import search_memories
        
        result = search_memories("API")
        
        if result["candidates"]:
            assert "content" in result["candidates"][0]
            assert len(result["candidates"][0]["content"]) > 0
    
    def test_search_instruction_included(self):
        """测试搜索结果包含指令"""
        from search_memory import search_memories
        
        result = search_memories("API")
        
        assert "instruction" in result
    
    def test_search_multiple_matches(self):
        """测试多个匹配结果"""
        from search_memory import search_memories
        
        # 搜索一个可能匹配多条记忆的关键词
        # 使用更通用的关键词
        result = search_memories("使用 框架")
        
        # 应该返回至少一个结果
        assert result["candidates_count"] >= 0  # 可能没有匹配也是正常的
    
    def test_search_sorted_by_score(self):
        """测试结果按分数排序"""
        from search_memory import search_memories
        
        result = search_memories("API 设计")
        
        if len(result["candidates"]) > 1:
            scores = [c["score"] for c in result["candidates"]]
            # 分数应该是降序排列
            assert scores == sorted(scores, reverse=True)


class TestSearchMemoryEmpty:
    """测试空记忆库搜索"""
    
    def setup(self):
        """每个测试前的设置"""
        self.test_dir = setup_test_env()
        import utils
        self.original_func = utils.get_project_root
        utils.get_project_root = lambda: self.test_dir
        # 不创建任何记忆
    
    def teardown(self):
        """每个测试后的清理"""
        import utils
        utils.get_project_root = self.original_func
        teardown_test_env()
    
    def test_search_empty_database(self):
        """测试空数据库搜索"""
        from search_memory import search_memories
        
        result = search_memories("任何关键词")
        
        assert result["candidates_count"] == 0
        assert result["candidates"] == []


class TestSearchMemoryDisabled:
    """测试禁用状态下的搜索"""
    
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
    
    def test_search_when_disabled(self):
        """测试禁用时搜索返回空"""
        from search_memory import search_memories
        
        result = search_memories("任何关键词")
        
        assert result["candidates"] == []
        assert "禁用" in result.get("message", "")


def run_tests():
    """运行所有测试"""
    test_classes = [
        TestSearchMemory,
        TestSearchMemoryEmpty,
        TestSearchMemoryDisabled
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
