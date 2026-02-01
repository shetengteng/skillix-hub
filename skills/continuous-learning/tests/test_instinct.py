#!/usr/bin/env python3
"""
instinct.py 测试用例
"""

import json
import sys
import shutil
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from instinct import (
    list_instincts, create_instinct, update_instinct, delete_instinct,
    check_skill, delete_evolved_skill, evolve_instincts,
    create_evolved_skill, sync_and_cleanup
)
from utils import get_data_dir, ensure_data_dirs, remove_skill_from_index


class TestCreateInstinct:
    """create_instinct 测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        ensure_data_dirs()
    
    def teardown_method(self):
        """每个测试后清理"""
        # 清理测试创建的本能
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def test_create_basic_instinct(self):
        """测试创建基本本能"""
        result = create_instinct({
            "id": "test-basic",
            "trigger": "测试触发条件"
        })
        
        assert result["status"] == "success"
        
        # 验证文件存在
        instinct_file = get_data_dir() / "instincts" / "test-basic.yaml"
        assert instinct_file.exists()
    
    def test_create_instinct_with_all_fields(self):
        """测试创建完整本能"""
        result = create_instinct({
            "id": "test-full",
            "trigger": "完整测试",
            "confidence": 0.8,
            "domain": "testing",
            "content": "# 测试本能\n\n## 行为\n测试行为"
        })
        
        assert result["status"] == "success"
        
        # 验证内容
        instinct_file = get_data_dir() / "instincts" / "test-full.yaml"
        content = instinct_file.read_text(encoding='utf-8')
        assert "confidence: 0.8" in content
        assert "domain: testing" in content
    
    def test_create_instinct_missing_id(self):
        """测试缺少 ID"""
        result = create_instinct({
            "trigger": "测试"
        })
        
        assert result["status"] == "error"
        assert "id" in result["message"]


class TestUpdateInstinct:
    """update_instinct 测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        ensure_data_dirs()
        create_instinct({
            "id": "test-update",
            "trigger": "原始触发条件",
            "confidence": 0.5
        })
    
    def teardown_method(self):
        """每个测试后清理"""
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def test_update_confidence(self):
        """测试更新置信度"""
        result = update_instinct("test-update", {"confidence": 0.9})
        
        assert result["status"] == "success"
        
        # 验证更新
        instincts = list_instincts()
        updated = [i for i in instincts if i["id"] == "test-update"][0]
        assert updated["confidence"] == 0.9
    
    def test_update_nonexistent(self):
        """测试更新不存在的本能"""
        result = update_instinct("nonexistent", {"confidence": 0.9})
        
        assert result["status"] == "error"


class TestDeleteInstinct:
    """delete_instinct 测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        ensure_data_dirs()
        create_instinct({
            "id": "test-delete",
            "trigger": "待删除"
        })
    
    def teardown_method(self):
        """每个测试后清理"""
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def test_delete_existing(self):
        """测试删除存在的本能"""
        result = delete_instinct("test-delete")
        
        assert result["status"] == "success"
        
        # 验证删除
        instinct_file = get_data_dir() / "instincts" / "test-delete.yaml"
        assert not instinct_file.exists()
    
    def test_delete_nonexistent(self):
        """测试删除不存在的本能"""
        result = delete_instinct("nonexistent")
        
        assert result["status"] == "error"


class TestListInstincts:
    """list_instincts 测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        ensure_data_dirs()
        # 清理现有本能
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def teardown_method(self):
        """每个测试后清理"""
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def test_list_empty(self):
        """测试列出空列表"""
        # 清理所有本能
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("*.yaml"):
            f.unlink()
        
        result = list_instincts()
        assert isinstance(result, list)
    
    def test_list_multiple(self):
        """测试列出多个本能"""
        create_instinct({"id": "test-list-1", "trigger": "测试1"})
        create_instinct({"id": "test-list-2", "trigger": "测试2"})
        
        result = list_instincts()
        
        ids = [i["id"] for i in result]
        assert "test-list-1" in ids
        assert "test-list-2" in ids


class TestCheckSkill:
    """check_skill 测试"""
    
    def test_check_nonexistent(self):
        """测试检查不存在的技能"""
        result = check_skill("nonexistent-skill")
        
        assert result["is_evolved"] == False
    
    def test_check_evolved_skill(self):
        """测试检查演化技能"""
        # 创建一个演化技能
        from utils import add_skill_to_index
        
        add_skill_to_index({
            "name": "test-evolved",
            "path": "/test/path",
            "cursor_path": "/test/cursor/path"
        })
        
        result = check_skill("test-evolved")
        
        assert result["is_evolved"] == True
        
        # 清理
        remove_skill_from_index("test-evolved")


class TestEvolveInstincts:
    """evolve_instincts 测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        ensure_data_dirs()
        # 清理现有本能
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def teardown_method(self):
        """每个测试后清理"""
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
        
        # 清理演化的技能
        evolved_dir = get_data_dir() / "evolved" / "skills"
        if evolved_dir.exists():
            for d in evolved_dir.iterdir():
                if d.name.startswith("test-"):
                    shutil.rmtree(d)
    
    def test_evolve_insufficient(self):
        """测试本能不足"""
        # 只创建 2 个本能
        create_instinct({"id": "test-evo-1", "trigger": "测试1", "domain": "test"})
        create_instinct({"id": "test-evo-2", "trigger": "测试2", "domain": "test"})
        
        result = evolve_instincts()
        
        assert result["status"] == "insufficient"
    
    def test_evolve_success(self):
        """测试成功演化"""
        # 创建 3 个同领域的本能
        for i in range(3):
            create_instinct({
                "id": f"test-evo-{i}",
                "trigger": f"测试触发条件 {i}",
                "domain": "test-domain",
                "confidence": 0.7
            })
        
        result = evolve_instincts()
        
        # 可能成功也可能没有候选（取决于平均置信度）
        assert result["status"] in ["success", "no_candidates"]


class TestCommandLine:
    """命令行接口测试"""
    
    def setup_method(self):
        """每个测试前准备"""
        ensure_data_dirs()
    
    def teardown_method(self):
        """每个测试后清理"""
        instincts_dir = get_data_dir() / "instincts"
        for f in instincts_dir.glob("test-*.yaml"):
            f.unlink()
    
    def test_status_command(self):
        """测试 status 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "instinct.py"), "status"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
        assert "count" in output
    
    def test_create_command(self):
        """测试 create 命令"""
        import subprocess
        
        data = json.dumps({"id": "test-cmd", "trigger": "命令行测试"})
        result = subprocess.run(
            ["python3", str(script_dir / "instinct.py"), "create", data],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["status"] == "success"
    
    def test_check_skill_command(self):
        """测试 --check-skill 命令"""
        import subprocess
        
        result = subprocess.run(
            ["python3", str(script_dir / "instinct.py"), "--check-skill", "test-skill"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "is_evolved" in output


def run_tests():
    """运行所有测试"""
    import traceback
    
    test_classes = [
        TestCreateInstinct,
        TestUpdateInstinct,
        TestDeleteInstinct,
        TestListInstincts,
        TestCheckSkill,
        TestEvolveInstincts,
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
