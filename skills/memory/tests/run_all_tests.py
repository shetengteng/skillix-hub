#!/usr/bin/env python3
"""运行所有 Memory Skill 测试"""

import sys
import subprocess
from pathlib import Path

def main():
    """运行所有测试"""
    test_dir = Path(__file__).resolve().parent
    
    test_files = [
        "test_utils.py",
        "test_save_memory.py",
        "test_search_memory.py",
        "test_delete_memory.py",
        "test_view_memory.py"
    ]
    
    total_passed = 0
    total_failed = 0
    
    print("=" * 60)
    print("Memory Skill 测试套件")
    print("=" * 60)
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"\n⚠️  测试文件不存在: {test_file}")
            continue
        
        print(f"\n{'='*60}")
        print(f"运行: {test_file}")
        print("=" * 60)
        
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=str(test_dir),
            capture_output=False
        )
        
        if result.returncode == 0:
            total_passed += 1
        else:
            total_failed += 1
    
    print("\n" + "=" * 60)
    print("总体结果")
    print("=" * 60)
    print(f"测试文件通过: {total_passed}/{len(test_files)}")
    
    if total_failed > 0:
        print(f"测试文件失败: {total_failed}")
        return 1
    
    print("\n✅ 所有测试通过！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
