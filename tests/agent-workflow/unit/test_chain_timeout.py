"""T10.3 + TC-CT-01/02: chain_timeout 触发 → action="continue"，再 advance 续跑。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402

LONG_CHAIN_YAML = """
name: t-chain
description: 10 个 mock 节点 + chain_timeout 极小 → 必触发 continue
config:
  chain_timeout_ms: 1
executors:
  mock: { kind: mock }
nodes:
  - { alias: n1,  type: agent_call, executor: mock, prompt: p, output: v1 }
  - { alias: n2,  type: agent_call, executor: mock, prompt: p, output: v2 }
  - { alias: n3,  type: agent_call, executor: mock, prompt: p, output: v3 }
  - { alias: n4,  type: agent_call, executor: mock, prompt: p, output: v4 }
  - { alias: n5,  type: agent_call, executor: mock, prompt: p, output: v5 }
  - { alias: n6,  type: agent_call, executor: mock, prompt: p, output: v6 }
  - { alias: n7,  type: agent_call, executor: mock, prompt: p, output: v7 }
  - { alias: n8,  type: agent_call, executor: mock, prompt: p, output: v8 }
  - { alias: n9,  type: agent_call, executor: mock, prompt: p, output: v9 }
  - { alias: n10, type: agent_call, executor: mock, prompt: p, output: v10 }
"""


class ChainTimeoutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-ct-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        os.environ.pop("AGENT_WORKFLOW_ENABLE_MOCK", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_continue_then_resume(self) -> None:
        out = engine.start_action({"workflow": LONG_CHAIN_YAML, "caller": "ut"})
        # 由于 chain_timeout=1ms，很可能在前几个节点之后就 continue
        self.assertIn(out["action"], ("continue", "completed"))
        run_id = out["run_id"]
        continued = out["action"] == "continue"
        if continued:
            self.assertEqual(out["status"], "awaiting_agent")
            self.assertEqual(out.get("reason"), "chain_timeout")

        # 持续 advance 直到完成（最多 20 次防失控）
        safety_cap = 20
        for _ in range(safety_cap):
            if out["action"] == "completed":
                break
            out = engine.advance_action({"run_id": run_id})
        self.assertEqual(out["action"], "completed")
        self.assertEqual(out["status"], "completed")
        # 所有 10 个 output 都应写入 vars
        for i in range(1, 11):
            self.assertIn(f"v{i}", out["vars"])


if __name__ == "__main__":
    unittest.main()
