#!/usr/bin/env python3
"""外部独立测试的共享工具。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
TEST_ROOT = THIS_DIR.parent
REPO_ROOT = TEST_ROOT.parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "memory-skill"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
TESTDATA_ROOT = TEST_ROOT / "testdata"
RUNTIME_ROOT = TESTDATA_ROOT / "runtime"

RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

_SANDBOX_LOG_DIR = str(TESTDATA_ROOT / "logs")
os.makedirs(_SANDBOX_LOG_DIR, exist_ok=True)
os.environ["MEMORY_LOG_DIR"] = _SANDBOX_LOG_DIR

sys.path.insert(0, str(SCRIPTS_DIR))


def run_script(script_name, workspace, stdin_data=None, args=None, timeout=180):
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)]
    if args:
        cmd.extend(args)
    env = os.environ.copy()
    env["MEMORY_LOG_DIR"] = str(Path(workspace) / ".cursor" / "skills" / "memory-data" / "logs")
    return subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        cwd=workspace,
        env=env,
        timeout=timeout,
    )


class IsolatedWorkspaceCase(unittest.TestCase):
    """每个测试使用独立工作区，避免与现有测试交叉。"""

    def setUp(self):
        self.workspace = tempfile.mkdtemp(
            prefix=f"standalone-{uuid.uuid4().hex[:8]}-",
            dir=str(RUNTIME_ROOT),
        )
        self.memory_dir = Path(self.workspace) / ".cursor" / "skills" / "memory-data"
        (self.memory_dir / "daily").mkdir(parents=True, exist_ok=True)
        (self.memory_dir / "MEMORY.md").write_text(
            "# 核心记忆\n\n## 用户偏好\n- 语言：中文\n\n## 项目背景\n- 项目：standalone-test\n\n## 重要决策\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.workspace, ignore_errors=True)

    def load_json(self, text):
        return json.loads(text)

