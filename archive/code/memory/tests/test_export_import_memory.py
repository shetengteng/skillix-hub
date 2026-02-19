#!/usr/bin/env python3
"""测试 export_memory.py 和 import_memory.py 导出导入功能"""

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
    
    # 清理当前目录下可能产生的导出文件
    current_dir = Path(__file__).resolve().parent
    for f in current_dir.glob("memory-export-*.json"):
        try:
            f.unlink()
        except Exception:
            pass


class TestExportMemory:
    """测试导出记忆功能"""
    
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
    
    def test_export_empty(self):
        """测试导出空数据"""
        from export_memory import export_memories
        
        result = export_memories()
        
        assert result["success"] == True
        assert result["total_memories"] == 0
    
    def test_export_with_memories(self):
        """测试导出有记忆的数据"""
        from export_memory import export_memories
        
        # 创建记忆
        self._create_test_memory("主题1", ["要点1"])
        self._create_test_memory("主题2", ["要点2"])
        
        # 导出
        output_file = self.test_dir / "export.json"
        result = export_memories(output_path=str(output_file))
        
        assert result["success"] == True
        assert result["total_memories"] == 2
        assert output_file.exists()
        
        # 验证导出内容
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["version"] == "1.0"
        assert len(data["index"]["entries"]) == 2
        assert data["statistics"]["total_memories"] == 2
    
    def test_export_with_content(self):
        """测试导出包含内容"""
        from export_memory import export_memories
        
        # 创建记忆
        self._create_test_memory("内容测试")
        
        # 导出（包含内容）
        output_file = self.test_dir / "export.json"
        result = export_memories(output_path=str(output_file), include_content=True)
        
        assert result["success"] == True
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["daily_files"]) > 0
    
    def test_export_without_content(self):
        """测试导出不包含内容"""
        from export_memory import export_memories
        
        # 创建记忆
        self._create_test_memory("内容测试")
        
        # 导出（不包含内容）
        output_file = self.test_dir / "export.json"
        result = export_memories(output_path=str(output_file), include_content=False)
        
        assert result["success"] == True
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["daily_files"]) == 0
    
    def test_export_date_range(self):
        """测试按日期范围导出"""
        from export_memory import export_memories
        
        # 创建记忆
        self._create_test_memory("今日主题")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 导出今天的记忆
        output_file = self.test_dir / "export.json"
        result = export_memories(
            output_path=str(output_file),
            date_from=today,
            date_to=today
        )
        
        assert result["success"] == True
        assert result["total_memories"] == 1
    
    def test_export_default_filename(self):
        """测试默认文件名"""
        from export_memory import export_memories
        
        # 创建记忆
        self._create_test_memory("测试")
        
        # 导出（不指定文件名）
        result = export_memories()
        
        assert result["success"] == True
        assert "memory-export-" in result["output_file"]


class TestImportMemory:
    """测试导入记忆功能"""
    
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
    
    def _create_export_file(self, entries=None, daily_files=None):
        """创建测试导出文件"""
        if entries is None:
            entries = [
                {
                    "id": "2026-01-29-001",
                    "date": "2026-01-29",
                    "session": 1,
                    "keywords": ["test"],
                    "summary": "测试主题",
                    "tags": [],
                    "line_range": [1, 10]
                }
            ]
        if daily_files is None:
            daily_files = {
                "2026-01-29": "# 2026-01-29 对话记忆\n\n## Session 1\n\n### 主题\n测试主题\n"
            }
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "source": {"location": "project"},
            "statistics": {"total_memories": len(entries)},
            "index": {"version": "1.0", "entries": entries},
            "daily_files": daily_files
        }
        
        export_file = self.test_dir / "import.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False)
        
        return str(export_file)
    
    def test_import_basic(self):
        """测试基本导入"""
        from import_memory import import_memories
        from utils import load_index
        
        export_file = self._create_export_file()
        result = import_memories(export_file)
        
        assert result["success"] == True
        assert result["imported_count"] == 1
        
        # 验证索引
        index = load_index()
        assert len(index["entries"]) == 1
    
    def test_import_merge_mode(self):
        """测试合并导入模式"""
        from import_memory import import_memories
        from save_memory import save_memory
        from utils import load_index
        
        # 先创建一个记忆
        save_memory(topic="现有主题", key_info=["现有要点"])
        
        # 创建不同 ID 的导入数据
        entries = [
            {
                "id": "2026-01-28-001",  # 不同的 ID
                "date": "2026-01-28",
                "session": 1,
                "keywords": ["test"],
                "summary": "导入主题",
                "tags": [],
                "line_range": [1, 10]
            }
        ]
        daily_files = {
            "2026-01-28": "# 2026-01-28 对话记忆\n\n## Session 1\n\n### 主题\n导入主题\n"
        }
        export_file = self._create_export_file(entries=entries, daily_files=daily_files)
        
        result = import_memories(export_file, mode="merge")
        
        assert result["success"] == True
        
        # 验证两个记忆都存在
        index = load_index()
        assert len(index["entries"]) == 2
    
    def test_import_replace_mode(self):
        """测试替换导入模式"""
        from import_memory import import_memories
        from save_memory import save_memory
        from utils import load_index
        
        # 先创建一个记忆
        save_memory(topic="现有主题", key_info=["现有要点"])
        
        # 替换导入
        export_file = self._create_export_file()
        result = import_memories(export_file, mode="replace")
        
        assert result["success"] == True
        
        # 验证只有导入的记忆
        index = load_index()
        assert len(index["entries"]) == 1
        assert index["entries"][0]["summary"] == "测试主题"
    
    def test_import_skip_existing(self):
        """测试跳过已存在的记忆"""
        from import_memory import import_memories
        from utils import load_index, save_index, initialize_data_dir
        
        # 先创建一个同 ID 的记忆
        initialize_data_dir()
        index = load_index()
        index["entries"].append({
            "id": "2026-01-29-001",
            "date": "2026-01-29",
            "summary": "原有主题"
        })
        save_index(index)
        
        # 导入（不覆盖）
        export_file = self._create_export_file()
        result = import_memories(export_file, overwrite_existing=False)
        
        assert result["success"] == True
        assert result["skipped_count"] == 1
        
        # 验证原有记忆未被覆盖
        index = load_index()
        assert index["entries"][0]["summary"] == "原有主题"
    
    def test_import_overwrite_existing(self):
        """测试覆盖已存在的记忆"""
        from import_memory import import_memories
        from utils import load_index, save_index, initialize_data_dir
        
        # 先创建一个同 ID 的记忆
        initialize_data_dir()
        index = load_index()
        index["entries"].append({
            "id": "2026-01-29-001",
            "date": "2026-01-29",
            "summary": "原有主题"
        })
        save_index(index)
        
        # 导入（覆盖）
        export_file = self._create_export_file()
        result = import_memories(export_file, overwrite_existing=True)
        
        assert result["success"] == True
        assert result["overwritten_count"] == 1
        
        # 验证记忆已被覆盖
        index = load_index()
        assert index["entries"][0]["summary"] == "测试主题"
    
    def test_import_nonexistent_file(self):
        """测试导入不存在的文件"""
        from import_memory import import_memories
        
        result = import_memories("/nonexistent/file.json")
        
        assert result["success"] == False
        assert "不存在" in result["message"]
    
    def test_import_invalid_json(self):
        """测试导入无效 JSON"""
        from import_memory import import_memories
        
        invalid_file = self.test_dir / "invalid.json"
        invalid_file.write_text("not valid json")
        
        result = import_memories(str(invalid_file))
        
        assert result["success"] == False
        assert "JSON" in result["message"]
    
    def test_import_invalid_version(self):
        """测试导入不支持的版本"""
        from import_memory import import_memories
        
        export_file = self.test_dir / "invalid_version.json"
        with open(export_file, 'w') as f:
            json.dump({"version": "99.0"}, f)
        
        result = import_memories(str(export_file))
        
        assert result["success"] == False
        assert "版本" in result["message"]


class TestExportImportRoundtrip:
    """测试导出导入往返"""
    
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
    
    def test_roundtrip(self):
        """测试导出后再导入"""
        from save_memory import save_memory
        from export_memory import export_memories
        from import_memory import import_memories
        from utils import load_index
        
        # 创建记忆
        save_memory(topic="往返测试1", key_info=["要点1"])
        save_memory(topic="往返测试2", key_info=["要点2"])
        
        # 导出
        export_file = self.test_dir / "roundtrip.json"
        export_result = export_memories(output_path=str(export_file))
        assert export_result["success"] == True
        assert export_result["total_memories"] == 2
        
        # 清空数据
        index = load_index()
        index["entries"] = []
        from utils import save_index
        save_index(index)
        
        # 导入
        import_result = import_memories(str(export_file))
        assert import_result["success"] == True
        assert import_result["imported_count"] == 2
        
        # 验证数据完整
        index = load_index()
        assert len(index["entries"]) == 2


class TestExportImportDisabled:
    """测试禁用状态下的导出导入"""
    
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
    
    def test_export_when_disabled(self):
        """测试禁用时导出失败"""
        from export_memory import export_memories
        
        result = export_memories()
        
        assert result["success"] == False
        assert "禁用" in result["message"]
    
    def test_import_when_disabled(self):
        """测试禁用时导入失败"""
        from import_memory import import_memories
        
        # 创建一个有效的导入文件
        export_file = self.test_dir / "import.json"
        with open(export_file, 'w') as f:
            json.dump({
                "version": "1.0",
                "index": {"entries": []},
                "daily_files": {}
            }, f)
        
        result = import_memories(str(export_file))
        
        assert result["success"] == False
        assert "禁用" in result["message"]


def run_tests():
    """运行所有测试"""
    test_classes = [
        TestExportMemory,
        TestImportMemory,
        TestExportImportRoundtrip,
        TestExportImportDisabled
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
