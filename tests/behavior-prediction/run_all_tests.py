#!/usr/bin/env python3
"""
运行所有 Behavior Prediction Skill 测试
"""

import sys
import unittest
from pathlib import Path

# 添加脚本目录到路径
THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR / "src"

sys.path.insert(0, str(THIS_DIR.parent.parent / "skills" / "behavior-prediction" / "scripts"))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def run_all_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(SRC_DIR),
        pattern="test_*.py"
    )
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回退出码
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
