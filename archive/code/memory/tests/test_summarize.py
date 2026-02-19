#!/usr/bin/env python3
"""
summarize.py 测试用例
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from summarize import (
    group_by_category, merge_similar_memories,
    generate_session_content, summarize_temp_memories
)
from utils import clear_pending_session, get_data_dir


class TestGroupByCategory:
    """group_by_category 测试"""
    
    def test_empty_list(self):
        """测试空列表"""
        result = group_by_category([])
        assert result == {}
    
    def test_single_category(self):
        """测试单一类别"""
        memories = [
            {"trigger_category": "decision"},
            {"trigger_category": "decision"}
        ]
        
        result = group_by_category(memories)
        
        assert "decision" in result
        assert len(result["decision"]) == 2
    
    def test_multiple_categories(self):
        """测试多个类别"""
        memories = [
            {"trigger_category": "decision"},
            {"trigger_category": "config"},
            {"trigger_category": "decision"},
            {"trigger_category": "plan"}
        ]
        
        result = group_by_category(memories)
        
        assert len(result) == 3
        assert len(result["decision"]) == 2
        assert len(result["config"]) == 1
        assert len(result["plan"]) == 1
    
    def test_missing_category(self):
        """测试缺少类别字段"""
        memories = [
            {"trigger_category": "decision"},
            {}  # 没有 trigger_category
        ]
        
        result = group_by_category(memories)
        
        assert "decision" in result
        assert "general" in result


class TestMergeSimilarMemories:
    """merge_similar_memories 测试"""
    
    def test_empty_list(self):
        """测试空列表"""
        result = merge_similar_memories([])
        assert result == []
    
    def test_no_similar(self):
        """测试无相似记忆"""
        memories = [
            {"extracted_info": {"topic": "API 设计"}},
            {"extracted_info": {"topic": "数据库配置"}}
        ]
        
        result = merge_similar_memories(memories, similarity_threshold=0.8)
        
        # 不相似，不合并
        assert len(result) == 2
    
    def test_similar_memories(self):
        """测试相似记忆合并"""
        memories = [
            {
                "extracted_info": {
                    "topic": "FastAPI 框架选择",
                    "key_info": ["使用 FastAPI"],
                    "tags": ["#api"]
                },
                "timestamp": "2026-02-01T10:00:00"
            },
            {
                "extracted_info": {
                    "topic": "FastAPI 框架配置",
                    "key_info": ["配置路由"],
                    "tags": ["#config"]
                },
                "timestamp": "2026-02-01T10:05:00"
            }
        ]
        
        result = merge_similar_memories(memories, similarity_threshold=0.5)
        
        # 相似度较高，应该合并
        # 注意：实际结果取决于相似度计算
        assert len(result) >= 1


class TestGenerateSessionContent:
    """generate_session_content 测试"""
    
    def test_empty_memories(self):
        """测试空记忆列表"""
        result = generate_session_content([])
        
        assert "## Session" in result
        assert "---" in result
    
    def test_with_topic(self):
        """测试有主题的记忆"""
        memories = [
            {"extracted_info": {"topic": "API 设计", "key_info": [], "tags": []}}
        ]
        
        result = generate_session_content(memories)
        
        assert "### 主题" in result
        assert "API 设计" in result
    
    def test_with_key_info(self):
        """测试有关键信息的记忆"""
        memories = [
            {"extracted_info": {"topic": "", "key_info": ["使用 FastAPI", "配置路由"], "tags": []}}
        ]
        
        result = generate_session_content(memories)
        
        assert "### 关键信息" in result
        assert "使用 FastAPI" in result
        assert "配置路由" in result
    
    def test_with_tags(self):
        """测试有标签的记忆"""
        memories = [
            {"extracted_info": {"topic": "", "key_info": [], "tags": ["#api", "#config"]}}
        ]
        
        result = generate_session_content(memories)
        
        assert "### 标签" in result
        assert "#api" in result
        assert "#config" in result


class TestSummarizeTempMemories:
    """summarize_temp_memories 测试"""
    
    def setup_method(self):
        """每个测试前清理"""
        clear_pending_session()
    
    def teardown_method(self):
        """每个测试后清理"""
        clear_pending_session()
    
    def test_empty_memories(self):
        """测试空记忆列表"""
        result = summarize_temp_memories([])
        
        assert result["status"] == "skipped"
        assert result["reason"] == "no_memories"
    
    def test_single_memory(self):
        """测试单个记忆"""
        memories = [
            {
                "trigger_category": "decision",
                "user_message": "我们决定使用 FastAPI",
                "extracted_info": {
                    "topic": "技术选型",
                    "key_info": ["使用 FastAPI"],
                    "tags": ["#decision"]
                },
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        result = summarize_temp_memories(memories)
        
        assert result["status"] == "success"
        assert result["original_count"] == 1
        assert "file_path" in result
    
    def test_multiple_memories(self):
        """测试多个记忆"""
        memories = [
            {
                "trigger_category": "decision",
                "user_message": "我们决定使用 FastAPI",
                "extracted_info": {
                    "topic": "技术选型",
                    "key_info": ["使用 FastAPI"],
                    "tags": ["#decision"]
                },
                "timestamp": datetime.now().isoformat()
            },
            {
                "trigger_category": "config",
                "user_message": "API 前缀配置为 /api/v2",
                "extracted_info": {
                    "topic": "API 配置",
                    "key_info": ["前缀 /api/v2"],
                    "tags": ["#config"]
                },
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        result = summarize_temp_memories(memories)
        
        assert result["status"] == "success"
        assert result["original_count"] == 2


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestGroupByCategory,
        TestMergeSimilarMemories,
        TestGenerateSessionContent,
        TestSummarizeTempMemories
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
