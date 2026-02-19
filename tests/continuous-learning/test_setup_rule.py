#!/usr/bin/env python3
"""
setup_rule.py 测试用例
"""

import json
import sys
import shutil
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from setup_rule import (
    setup_rule, remove_rule, check_rule, update_rule,
    get_rule_config, detect_assistant_type, get_project_root
)


class TestGetRuleConfig:
    """get_rule_config 测试"""
    
    def test_cursor_config(self):
        """测试 Cursor 配置"""
        config = get_rule_config("cursor")
        
        assert config["dir_name"] == ".cursor"
        assert config["file_name"] == "continuous-learning.mdc"
        assert "template" in config
    
    def test_claude_config(self):
        """测试 Claude 配置"""
        config = get_rule_config("claude")
        
        assert config["dir_name"] == ".claude"
        assert config["file_name"] == "continuous-learning.md"
    
    def test_generic_config(self):
        """测试通用配置"""
        config = get_rule_config("generic")
        
        assert config["dir_name"] == ".ai"
        assert config["file_name"] == "continuous-learning.md"
    
    def test_unknown_fallback(self):
        """测试未知类型回退到通用"""
        config = get_rule_config("unknown")
        
        assert config["dir_name"] == ".ai"


class TestDetectAssistantType:
    """detect_assistant_type 测试"""
    
    def test_detect(self):
        """测试检测助手类型"""
        result = detect_assistant_type()
        
        # 应该返回有效的类型
        assert result in ["cursor", "claude", "generic"]


class TestGetProjectRoot:
    """get_project_root 测试"""
    
    def test_get_root(self):
        """测试获取项目根目录"""
        root = get_project_root()
        
        assert root.exists()
        # 应该包含 .cursor 或 .git
        has_marker = (root / ".cursor").exists() or (root / ".git").exists()
        # 如果没有找到，返回当前目录
        assert has_marker or root == Path.cwd()


class TestSetupRule:
    """setup_rule 测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        # 备份可能存在的规则文件
        self.backup_files = []
        
        for location in ["global", "project"]:
            for assistant_type in ["cursor", "claude", "generic"]:
                config = get_rule_config(assistant_type)
                if location == "global":
                    base_dir = Path.home() / config["dir_name"]
                else:
                    base_dir = get_project_root() / config["dir_name"]
                
                rule_file = base_dir / config["rules_dir"] / config["file_name"]
                if rule_file.exists():
                    backup_path = rule_file.with_suffix(".backup")
                    shutil.copy(rule_file, backup_path)
                    self.backup_files.append((rule_file, backup_path))
    
    def teardown_method(self):
        """每个测试后恢复"""
        # 恢复备份的文件
        for rule_file, backup_path in self.backup_files:
            if backup_path.exists():
                shutil.copy(backup_path, rule_file)
                backup_path.unlink()
    
    def test_setup_project_rule(self):
        """测试设置项目级规则"""
        result = setup_rule(location="project", assistant_type="cursor", force=True)
        
        assert result["success"] == True
        assert "rule_file" in result
        
        # 验证文件存在
        rule_file = Path(result["rule_file"])
        assert rule_file.exists()
        
        # 清理
        rule_file.unlink()
    
    def test_setup_without_force(self):
        """测试不覆盖已存在的规则"""
        # 先创建一个规则
        result1 = setup_rule(location="project", assistant_type="cursor", force=True)
        assert result1["success"] == True
        
        # 再次创建（不强制）
        result2 = setup_rule(location="project", assistant_type="cursor", force=False)
        assert result2["success"] == False
        
        # 清理
        Path(result1["rule_file"]).unlink()


class TestRemoveRule:
    """remove_rule 测试"""
    
    def test_remove_existing(self):
        """测试移除存在的规则"""
        # 先创建
        setup_result = setup_rule(location="project", assistant_type="cursor", force=True)
        assert setup_result["success"] == True
        
        # 移除
        result = remove_rule(location="project", assistant_type="cursor")
        
        assert result["success"] == True
        
        # 验证文件不存在
        rule_file = Path(setup_result["rule_file"])
        assert not rule_file.exists()
    
    def test_remove_nonexistent(self):
        """测试移除不存在的规则"""
        # 确保规则不存在
        remove_rule(location="project", assistant_type="generic")
        
        # 再次移除
        result = remove_rule(location="project", assistant_type="generic")
        
        assert result["success"] == False


class TestCheckRule:
    """check_rule 测试"""
    
    def test_check_nonexistent(self):
        """测试检查不存在的规则"""
        # 确保规则不存在
        remove_rule(location="project", assistant_type="generic")
        
        result = check_rule(location="project", assistant_type="generic")
        
        assert result["success"] == True
        assert result["exists"] == False
        assert result["enabled"] == False
    
    def test_check_existing(self):
        """测试检查存在的规则"""
        # 先创建
        setup_rule(location="project", assistant_type="cursor", force=True)
        
        result = check_rule(location="project", assistant_type="cursor")
        
        assert result["success"] == True
        assert result["exists"] == True
        assert result["enabled"] == True
        
        # 清理
        remove_rule(location="project", assistant_type="cursor")


class TestUpdateRule:
    """update_rule 测试"""
    
    def test_update_existing(self):
        """测试更新存在的规则"""
        # 先创建
        setup_rule(location="project", assistant_type="cursor", force=True)
        
        # 更新
        result = update_rule(location="project", assistant_type="cursor")
        
        assert result["success"] == True
        
        # 清理
        remove_rule(location="project", assistant_type="cursor")
    
    def test_update_nonexistent(self):
        """测试更新不存在的规则"""
        # 确保规则不存在
        remove_rule(location="project", assistant_type="generic")
        
        result = update_rule(location="project", assistant_type="generic")
        
        assert result["success"] == False


class TestCommandLine:
    """命令行接口测试"""
    
    def test_check_command(self):
        """测试 check 命令"""
        import subprocess
        
        data = json.dumps({"action": "check", "location": "project"})
        result = subprocess.run(
            ["python3", str(script_dir / "setup_rule.py"), data],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] == True
    
    def test_enable_disable_command(self):
        """测试 enable/disable 命令"""
        import subprocess
        
        # Enable
        data = json.dumps({"action": "enable", "location": "project", "force": True})
        result = subprocess.run(
            ["python3", str(script_dir / "setup_rule.py"), data],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] == True
        
        # Disable
        data = json.dumps({"action": "disable", "location": "project"})
        result = subprocess.run(
            ["python3", str(script_dir / "setup_rule.py"), data],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["success"] == True
    
    def test_invalid_action(self):
        """测试无效操作"""
        import subprocess
        
        data = json.dumps({"action": "invalid"})
        result = subprocess.run(
            ["python3", str(script_dir / "setup_rule.py"), data],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert output["success"] == False


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestGetRuleConfig,
        TestDetectAssistantType,
        TestGetProjectRoot,
        TestSetupRule,
        TestRemoveRule,
        TestCheckRule,
        TestUpdateRule,
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
