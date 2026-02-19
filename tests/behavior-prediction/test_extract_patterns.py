#!/usr/bin/env python3
"""
测试 extract_patterns.py - 模式提取功能测试
"""

import json
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "skills" / "behavior-prediction" / "scripts"))


class TestExtractPatterns(unittest.TestCase):
    """测试模式提取功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 修改 utils 模块的 DATA_DIR
        import utils
        self.original_data_dir = utils.DATA_DIR
        utils.DATA_DIR = self.temp_path / "behavior-prediction-data"
        utils.ensure_data_dirs()
    
    def tearDown(self):
        """测试后清理"""
        import utils
        utils.DATA_DIR = self.original_data_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_extract_and_update_patterns(self):
        """测试提取并更新模式"""
        from extract_patterns import extract_and_update_patterns
        
        session_data = {
            "session_summary": {
                "topic": "测试",
                "workflow_stages": ["design", "implement", "test"],
                "technologies_used": ["Python", "FastAPI"],
                "tags": ["#api", "#backend"]
            }
        }
        
        result = extract_and_update_patterns(session_data)
        
        self.assertTrue(result["workflow_updated"])
        self.assertTrue(result["preferences_updated"])
        self.assertTrue(result["project_patterns_updated"])
    
    def test_workflow_patterns_update(self):
        """测试工作流程模式更新"""
        from extract_patterns import update_workflow_patterns, get_workflow_patterns
        
        session_data = {
            "session_summary": {
                "workflow_stages": ["implement", "test"]
            }
        }
        
        result = update_workflow_patterns(session_data)
        
        self.assertTrue(result["updated"])
        
        # 检查模式是否被保存
        patterns = get_workflow_patterns()
        self.assertIn("implement", patterns["stage_transitions"])
        self.assertIn("test", patterns["stage_transitions"]["implement"])
    
    def test_stage_transition_probability(self):
        """测试阶段转移概率计算"""
        from extract_patterns import update_workflow_patterns, get_workflow_patterns
        
        # 记录多次相同的转移
        for _ in range(5):
            session_data = {
                "session_summary": {
                    "workflow_stages": ["implement", "test"]
                }
            }
            update_workflow_patterns(session_data)
        
        patterns = get_workflow_patterns()
        
        # 检查概率
        prob = patterns["stage_transitions"]["implement"]["test"]["probability"]
        self.assertEqual(prob, 1.0)  # 100% 概率
    
    def test_preferences_update(self):
        """测试偏好数据更新"""
        from extract_patterns import update_preferences, get_preferences
        
        session_data = {
            "session_summary": {
                "technologies_used": ["Python", "FastAPI", "pytest"],
                "workflow_stages": ["implement", "test"],
                "tags": ["#api"]
            }
        }
        
        update_preferences(session_data)
        
        prefs = get_preferences()
        
        # 检查技术栈分类
        self.assertIn("python", prefs["tech_stack"]["languages"])
        self.assertIn("fastapi", prefs["tech_stack"]["frameworks"])
        self.assertIn("pytest", prefs["tech_stack"]["tools"])
    
    def test_project_type_inference(self):
        """测试项目类型推断"""
        from extract_patterns import infer_project_type
        
        # 后端项目
        result = infer_project_type(["#api", "#backend"], ["fastapi", "python"])
        self.assertEqual(result, "backend_api")
        
        # 前端项目
        result = infer_project_type(["#frontend"], ["vue", "typescript"])
        self.assertEqual(result, "frontend")
        
        # 全栈项目
        result = infer_project_type(["#fullstack"], [])
        self.assertEqual(result, "fullstack")
        
        # 工具/脚本
        result = infer_project_type(["#script", "#cli"], [])
        self.assertEqual(result, "tool_script")
        
        # 文档
        result = infer_project_type(["#doc", "#design"], [])
        self.assertEqual(result, "documentation")
        
        # 通用
        result = infer_project_type([], [])
        self.assertEqual(result, "general")
    
    def test_project_patterns_update(self):
        """测试项目模式更新"""
        from extract_patterns import update_project_patterns, get_project_patterns
        
        session_data = {
            "session_summary": {
                "workflow_stages": ["design", "implement"],
                "technologies_used": ["Python", "FastAPI"],
                "tags": ["#api"]
            }
        }
        
        update_project_patterns(session_data)
        
        patterns = get_project_patterns()
        
        self.assertIn("backend_api", patterns["patterns"])
        self.assertEqual(patterns["patterns"]["backend_api"]["count"], 1)
    
    def test_identify_common_sequences(self):
        """测试识别常见序列"""
        from extract_patterns import identify_common_sequences
        
        transitions = {
            "implement": {
                "test": {"count": 5, "probability": 0.8},
                "commit": {"count": 1, "probability": 0.2}
            },
            "test": {
                "commit": {"count": 3, "probability": 1.0}
            }
        }
        
        sequences = identify_common_sequences(transitions)
        
        self.assertTrue(len(sequences) > 0)
        # 最高频的应该是 implement → test
        self.assertEqual(sequences[0]["sequence"], ["implement", "test"])
    
    def test_technology_classification(self):
        """测试技术分类"""
        from extract_patterns import classify_technology
        
        # 语言
        self.assertEqual(classify_technology("python"), "languages")
        self.assertEqual(classify_technology("javascript"), "languages")
        self.assertEqual(classify_technology("typescript"), "languages")
        
        # 框架
        self.assertEqual(classify_technology("fastapi"), "frameworks")
        self.assertEqual(classify_technology("vue"), "frameworks")
        self.assertEqual(classify_technology("react"), "frameworks")
        
        # 工具
        self.assertEqual(classify_technology("pytest"), "tools")
        self.assertEqual(classify_technology("docker"), "tools")
    
    def test_empty_session_handling(self):
        """测试空会话处理"""
        from extract_patterns import update_workflow_patterns
        
        session_data = {
            "session_summary": {
                "workflow_stages": []
            }
        }
        
        result = update_workflow_patterns(session_data)
        
        self.assertFalse(result["updated"])
    
    def test_new_pattern_detection(self):
        """测试新模式检测"""
        from extract_patterns import update_workflow_patterns
        
        session_data = {
            "session_summary": {
                "workflow_stages": ["design", "implement"]
            }
        }
        
        result = update_workflow_patterns(session_data)
        
        # 第一次应该检测到新模式
        self.assertTrue(len(result.get("new_patterns", [])) > 0)


if __name__ == "__main__":
    unittest.main()
