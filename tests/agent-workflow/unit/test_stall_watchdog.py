"""TC-SW-01: stall watchdog 触发 EXECUTOR_STALLED。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402
from lib.errors import ErrorCode  # noqa: E402

STALL_YAML = """
name: t-stall
executors:
  mock: { kind: mock }
nodes:
  - alias: hang
    type: agent_call
    executor: mock
    prompt: p
    output: x
"""


class StallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-sw-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"
        os.environ["AGENT_WORKFLOW_MOCK_HANG_STALL"] = "1"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        for key in ("AGENT_WORKFLOW_ENABLE_MOCK", "AGENT_WORKFLOW_MOCK_HANG_STALL"):
            os.environ.pop(key, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_stall_triggers_error_in_run(self) -> None:
        out = engine.start_action({"workflow": STALL_YAML, "caller": "ut"})
        self.assertEqual(out["action"], "failed")
        self.assertEqual(out["error"]["code"], ErrorCode.EXECUTOR_STALLED)


if __name__ == "__main__":
    unittest.main()
