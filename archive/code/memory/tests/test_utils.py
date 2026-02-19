#!/usr/bin/env python3
"""测试 utils.py 工具函数"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from utils import (
    extract_keywords,
    time_decay,
    calculate_score,
    get_default_config,
    deep_merge
)


class TestExtractKeywords:
    """测试关键词提取"""
    
    def test_basic_extraction(self):
        """测试基本关键词提取"""
        text = "Memory Skill 设计讨论"
        keywords = extract_keywords(text)
        assert "memory" in keywords
        assert "skill" in keywords
        assert "设计讨论" in keywords
    
    def test_stopwords_removal(self):
        """测试停用词过滤"""
        text = "the quick brown fox is a fast animal"
        keywords = extract_keywords(text)
        # 停用词应该被过滤
        assert "the" not in keywords
        assert "is" not in keywords
        assert "a" not in keywords
        # 有意义的词应该保留
        assert "quick" in keywords
        assert "brown" in keywords
        assert "fox" in keywords
    
    def test_chinese_stopwords_removal(self):
        """测试中文停用词过滤"""
        text = "这个项目的 API 设计是很好的"
        keywords = extract_keywords(text)
        # 中文停用词应该被过滤（单字符会被过滤）
        assert "的" not in keywords
        assert "是" not in keywords
        # 有意义的词应该保留
        assert "api" in keywords
        # 注意：中文分词可能会把"这个项目的"作为一个词
        # 所以我们只检查 api 和设计相关的词是否存在
    
    def test_max_keywords_limit(self):
        """测试关键词数量限制"""
        text = " ".join([f"word{i}" for i in range(50)])
        keywords = extract_keywords(text)
        assert len(keywords) <= 20
    
    def test_deduplication(self):
        """测试关键词去重"""
        text = "API API API 设计 设计"
        keywords = extract_keywords(text)
        assert keywords.count("api") == 1
        assert keywords.count("设计") == 1
    
    def test_empty_input(self):
        """测试空输入"""
        keywords = extract_keywords("")
        assert keywords == []
    
    def test_punctuation_removal(self):
        """测试标点符号移除"""
        text = "Hello, world! How are you?"
        keywords = extract_keywords(text)
        assert "hello" in keywords
        assert "world" in keywords


class TestTimeDecay:
    """测试时间衰减"""
    
    def test_today_no_decay(self):
        """测试今天无衰减"""
        decay = time_decay(0)
        assert decay == 1.0
    
    def test_one_day_decay(self):
        """测试一天衰减"""
        decay = time_decay(1, decay_rate=0.95)
        assert abs(decay - 0.95) < 0.001
    
    def test_seven_days_decay(self):
        """测试七天衰减"""
        decay = time_decay(7, decay_rate=0.95)
        expected = 0.95 ** 7
        assert abs(decay - expected) < 0.001
    
    def test_thirty_days_decay(self):
        """测试三十天衰减"""
        decay = time_decay(30, decay_rate=0.95)
        expected = 0.95 ** 30
        assert abs(decay - expected) < 0.001
    
    def test_custom_decay_rate(self):
        """测试自定义衰减率"""
        decay = time_decay(10, decay_rate=0.99)
        expected = 0.99 ** 10
        assert abs(decay - expected) < 0.001


class TestCalculateScore:
    """测试综合分数计算"""
    
    def test_full_match_today_project(self):
        """测试完全匹配、今天、项目级"""
        query_keywords = {"api", "design"}
        memory_keywords = ["api", "design", "fastapi"]
        score = calculate_score(
            query_keywords,
            memory_keywords,
            days_ago=0,
            is_project_level=True
        )
        # 关键词匹配分 = 2/2 = 1.0
        # 时间衰减 = 1.0
        # 来源权重 = 1.0
        assert abs(score - 1.0) < 0.001
    
    def test_partial_match(self):
        """测试部分匹配"""
        query_keywords = {"api", "design"}
        memory_keywords = ["api", "fastapi"]
        score = calculate_score(
            query_keywords,
            memory_keywords,
            days_ago=0,
            is_project_level=True
        )
        # 关键词匹配分 = 1/2 = 0.5
        assert abs(score - 0.5) < 0.001
    
    def test_no_match(self):
        """测试无匹配"""
        query_keywords = {"api", "design"}
        memory_keywords = ["database", "optimization"]
        score = calculate_score(
            query_keywords,
            memory_keywords,
            days_ago=0,
            is_project_level=True
        )
        assert score == 0
    
    def test_global_level_weight(self):
        """测试全局级权重"""
        query_keywords = {"api"}
        memory_keywords = ["api"]
        score = calculate_score(
            query_keywords,
            memory_keywords,
            days_ago=0,
            is_project_level=False
        )
        # 关键词匹配分 = 1.0
        # 时间衰减 = 1.0
        # 来源权重 = 0.7
        assert abs(score - 0.7) < 0.001
    
    def test_time_decay_effect(self):
        """测试时间衰减效果"""
        query_keywords = {"api"}
        memory_keywords = ["api"]
        
        score_today = calculate_score(query_keywords, memory_keywords, 0, True)
        score_week = calculate_score(query_keywords, memory_keywords, 7, True)
        score_month = calculate_score(query_keywords, memory_keywords, 30, True)
        
        # 分数应该随时间递减
        assert score_today > score_week > score_month


class TestDeepMerge:
    """测试深度合并"""
    
    def test_simple_merge(self):
        """测试简单合并"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_nested_merge(self):
        """测试嵌套合并"""
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": {"y": 3, "z": 4}}
        result = deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 3, "z": 4}}
    
    def test_deep_nested_merge(self):
        """测试深层嵌套合并"""
        base = {"a": {"b": {"c": 1}}}
        override = {"a": {"b": {"d": 2}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": 1, "d": 2}}}


class TestGetDefaultConfig:
    """测试默认配置"""
    
    def test_config_structure(self):
        """测试配置结构"""
        config = get_default_config()
        
        assert "version" in config
        assert "enabled" in config
        assert "auto_save" in config
        assert "auto_retrieve" in config
        assert "storage" in config
        assert "retrieval" in config
    
    def test_storage_config(self):
        """测试存储配置"""
        config = get_default_config()
        storage = config["storage"]
        
        assert storage["location"] == "project-first"
        assert storage["retention_days"] == -1
    
    def test_retrieval_config(self):
        """测试检索配置"""
        config = get_default_config()
        retrieval = config["retrieval"]
        
        assert retrieval["max_candidates"] == 10
        assert retrieval["max_results"] == 3
        assert retrieval["search_scope_days"] == 30
        assert retrieval["time_decay_rate"] == 0.95


def run_tests():
    """运行所有测试"""
    test_classes = [
        TestExtractKeywords,
        TestTimeDecay,
        TestCalculateScore,
        TestDeepMerge,
        TestGetDefaultConfig
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    getattr(instance, method_name)()
                    passed_tests += 1
                    print(f"✓ {test_class.__name__}.{method_name}")
                except AssertionError as e:
                    failed_tests.append((test_class.__name__, method_name, str(e)))
                    print(f"✗ {test_class.__name__}.{method_name}: {e}")
                except Exception as e:
                    failed_tests.append((test_class.__name__, method_name, str(e)))
                    print(f"✗ {test_class.__name__}.{method_name}: {e}")
    
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
