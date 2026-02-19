#!/usr/bin/env python3
"""
保存触发检测测试用例
"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from utils import detect_save_trigger, SAVE_TRIGGER_KEYWORDS


class TestSaveTriggerKeywords:
    """保存触发关键词测试"""
    
    def test_keywords_structure(self):
        """测试关键词结构"""
        assert "zh" in SAVE_TRIGGER_KEYWORDS
        assert "en" in SAVE_TRIGGER_KEYWORDS
        
        # 检查中文类别
        zh_categories = SAVE_TRIGGER_KEYWORDS["zh"]
        assert "decision" in zh_categories
        assert "preference" in zh_categories
        assert "config" in zh_categories
        assert "plan" in zh_categories
        assert "important" in zh_categories
    
    def test_keywords_not_empty(self):
        """测试关键词列表不为空"""
        for lang in ["zh", "en"]:
            for category, keywords in SAVE_TRIGGER_KEYWORDS[lang].items():
                assert len(keywords) > 0, f"{lang}.{category} 关键词列表为空"


class TestDetectSaveTrigger:
    """detect_save_trigger 测试"""
    
    def test_decision_keywords_zh(self):
        """测试中文决策类关键词"""
        test_cases = [
            ("我们决定使用 FastAPI", "决定", "decision"),
            ("选择 PostgreSQL 作为数据库", "选择", "decision"),
            ("采用微服务架构", "采用", "decision"),
            ("确定了这个方案", "确定", "decision"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
            assert result["trigger_keyword"] == expected_kw, f"'{text}' 关键词应该是 '{expected_kw}'"
            assert result["trigger_category"] == expected_cat, f"'{text}' 类别应该是 '{expected_cat}'"
    
    def test_preference_keywords_zh(self):
        """测试中文偏好类关键词"""
        test_cases = [
            ("我喜欢函数式编程", "喜欢", "preference"),
            ("我习惯用 TypeScript", "习惯", "preference"),
            ("我偏好简洁的代码风格", "偏好", "preference"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
    
    def test_config_keywords_zh(self):
        """测试中文配置类关键词"""
        test_cases = [
            ("API 前缀配置为 /api/v2", "配置", "config"),
            ("设置超时时间为 30 秒", "设置", "config"),
            ("命名规范使用驼峰式", "命名", "config"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
    
    def test_plan_keywords_zh(self):
        """测试中文计划类关键词"""
        test_cases = [
            ("下一步要实现认证功能", "下一步", "plan"),
            ("待办事项：完成测试", "待办", "plan"),
            ("计划明天完成部署", "计划", "plan"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
    
    def test_important_keywords_zh(self):
        """测试中文重要类关键词"""
        test_cases = [
            ("这个很重要，要记住", "重要", "important"),
            ("记住这个配置", "记住", "important"),
            ("注意这个边界条件", "注意", "important"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
    
    def test_decision_keywords_en(self):
        """测试英文决策类关键词"""
        test_cases = [
            ("Let's use Python for this", "use", "decision"),
            ("I decide to go with FastAPI", "decide", "decision"),
            ("We should choose PostgreSQL", "choose", "decision"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
    
    def test_preference_keywords_en(self):
        """测试英文偏好类关键词"""
        test_cases = [
            ("I prefer TypeScript over JavaScript", "prefer", "preference"),
            ("I like functional programming", "like", "preference"),
            ("I usually use pytest", "usually", "preference"),
        ]
        
        for text, expected_kw, expected_cat in test_cases:
            result = detect_save_trigger(text)
            assert result["should_save"], f"'{text}' 应该触发保存"
    
    def test_no_trigger(self):
        """测试无触发关键词"""
        test_cases = [
            "今天天气不错",
            "Hello world",
            "这是一个测试",
            "The quick brown fox",
        ]
        
        for text in test_cases:
            result = detect_save_trigger(text)
            assert not result["should_save"], f"'{text}' 不应该触发保存"
    
    def test_short_message(self):
        """测试短消息不触发"""
        result = detect_save_trigger("决定")  # 太短
        assert not result["should_save"], "短消息不应该触发保存"
    
    def test_multiple_keywords(self):
        """测试多个关键词"""
        result = detect_save_trigger("我们决定使用 FastAPI，配置前缀为 /api")
        
        assert result["should_save"]
        assert "all_matches" in result
        assert len(result["all_matches"]) > 1
    
    def test_confidence_calculation(self):
        """测试置信度计算"""
        # 单个关键词
        result1 = detect_save_trigger("我们决定使用 FastAPI")
        
        # 多个关键词
        result2 = detect_save_trigger("我们决定使用 FastAPI，配置前缀为 /api，下一步实现认证")
        
        # 多个关键词应该有更高的置信度
        assert result2["confidence"] >= result1["confidence"]


class TestCustomKeywords:
    """自定义关键词测试"""
    
    def test_custom_keywords(self):
        """测试自定义关键词"""
        config = {
            "save_trigger": {
                "enabled": True,
                "min_message_length": 5,
                "custom_keywords": {
                    "zh": ["自定义词"],
                    "en": ["customword"]
                },
                "excluded_keywords": {
                    "zh": [],
                    "en": []
                }
            }
        }
        
        result = detect_save_trigger("这是一个自定义词测试", config)
        assert result["should_save"]
        assert result["trigger_category"] == "custom"
    
    def test_excluded_keywords(self):
        """测试排除关键词"""
        config = {
            "save_trigger": {
                "enabled": True,
                "min_message_length": 5,
                "custom_keywords": {
                    "zh": [],
                    "en": []
                },
                "excluded_keywords": {
                    "zh": ["测试"],
                    "en": []
                }
            }
        }
        
        # 虽然有"决定"关键词，但包含排除词"测试"
        result = detect_save_trigger("这是一个测试，我们决定使用 FastAPI", config)
        assert not result["should_save"]


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestSaveTriggerKeywords,
        TestDetectSaveTrigger,
        TestCustomKeywords
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
