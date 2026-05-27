"""TC-SL-01/02 + sleep 边界。"""
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402
from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.nodes import sleep as sleep_mod  # noqa: E402


class SleepResolveTest(unittest.TestCase):
    def test_literal_number(self) -> None:
        self.assertEqual(sleep_mod.resolve_seconds({"seconds": 2.5}, {}), 2.5)

    def test_template(self) -> None:
        self.assertEqual(sleep_mod.resolve_seconds({"seconds": "{{n}}"}, {"n": 7}), 7.0)

    def test_below_min(self) -> None:
        with self.assertRaises(WorkflowError) as ctx:
            sleep_mod.resolve_seconds({"seconds": -1}, {})
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)

    def test_above_max(self) -> None:
        with self.assertRaises(WorkflowError) as ctx:
            sleep_mod.resolve_seconds({"seconds": 600}, {})
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)


SLEEP_YAML = """
name: t-sleep
executors:
  mock: { kind: mock }
nodes:
  - alias: a
    type: agent_call
    executor: mock
    prompt: a
    output: va
  - alias: pause
    type: sleep
    seconds: 0
  - alias: b
    type: agent_call
    executor: mock
    prompt: b
    output: vb
"""


class SleepE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-sl-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        os.environ.pop("AGENT_WORKFLOW_ENABLE_MOCK", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sleep_zero_passes_through(self) -> None:
        t0 = time.monotonic()
        out = engine.start_action({"workflow": SLEEP_YAML, "caller": "ut"})
        elapsed = time.monotonic() - t0
        self.assertEqual(out["action"], "completed")
        self.assertLess(elapsed, 2.0)  # 0 秒 sleep 不应阻塞
        status = engine.status_action({"run_id": out["run_id"], "include_events": True})
        types = [e["type"] for e in status["events"]]
        self.assertIn("sleep_start", types)
        self.assertIn("sleep_end", types)


if __name__ == "__main__":
    unittest.main()
