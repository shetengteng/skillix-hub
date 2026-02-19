#!/usr/bin/env python3
"""
运行所有测试
"""

import sys
import subprocess
from pathlib import Path

# 测试文件列表
TEST_FILES = [
    "test_utils.py",
    "test_observe.py",
    "test_analyze.py",
    "test_instinct.py",
    "test_setup_rule.py"
]


def run_all_tests():
    """运行所有测试"""
    tests_dir = Path(__file__).parent
    
    total_passed = 0
    total_failed = 0
    failed_tests = []
    
    print("=" * 60)
    print("Continuous Learning Skill - 测试套件")
    print("=" * 60)
    print()
    
    for test_file in TEST_FILES:
        test_path = tests_dir / test_file
        
        if not test_path.exists():
            print(f"⚠️  跳过 {test_file}（文件不存在）")
            continue
        
        print(f"📋 运行 {test_file}")
        print("-" * 40)
        
        result = subprocess.run(
            ["python3", str(test_path)],
            capture_output=True,
            text=True
        )
        
        # 打印输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # 解析结果
        if result.returncode == 0:
            # 从输出中提取通过/失败数
            for line in result.stdout.split('\n'):
                if "通过:" in line and "失败:" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "通过:" in part:
                            total_passed += int(part.split(":")[1].strip())
                        if "失败:" in part:
                            total_failed += int(part.split(":")[1].strip())
        else:
            failed_tests.append(test_file)
        
        print()
    
    # 打印总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总通过: {total_passed}")
    print(f"总失败: {total_failed}")
    
    if failed_tests:
        print(f"\n失败的测试文件:")
        for f in failed_tests:
            print(f"  - {f}")
    
    if total_failed == 0 and not failed_tests:
        print("\n✅ 所有测试通过！")
        return True
    else:
        print("\n❌ 存在失败的测试")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
