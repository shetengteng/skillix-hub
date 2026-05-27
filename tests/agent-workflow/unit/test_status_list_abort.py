"""TC-STA-01/02/03 + TC-LS-01/02/04 + TC-AB-01/02 + TC-EX-01。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402
from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.executors.registry import list_executors  # noqa: E402

WAIT_YAML = """
name: t-wait
executors:
  mock: { kind: mock }
nodes:
  - alias: pre
    type: agent_call
    executor: mock
    prompt: hi
    output: x
  - alias: ask
    type: wait_user
    message: ok?
    schema:
      type: object
      required: [approved]
      properties:
        approved: { type: boolean }
"""


class StatusListAbortTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-sla-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"
        os.environ["AGENT_WORKFLOW_MOCK_PRE"] = "x-val"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        for key in ("AGENT_WORKFLOW_ENABLE_MOCK", "AGENT_WORKFLOW_MOCK_PRE"):
            os.environ.pop(key, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_status_returns_last_payload(self) -> None:
        out = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "wait_user")
        s = engine.status_action({"run_id": run_id})
        self.assertEqual(s["status"], "waiting_user")
        self.assertEqual(s["last_payload"]["alias"], "ask")
        self.assertEqual(len(s["history"]), 1)
        self.assertEqual(s["history"][0]["alias"], "pre")

    def test_status_with_events(self) -> None:
        out = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        s = engine.status_action({"run_id": out["run_id"], "include_events": True})
        types = {e.get("type") for e in s.get("events", [])}
        self.assertIn("run_start", types)
        self.assertIn("node_start", types)
        self.assertIn("node_end", types)

    def test_list_default_current_scope(self) -> None:
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        listed = engine.list_action({"limit": 10})
        self.assertGreaterEqual(listed["count"], 2)

    def test_list_status_filter(self) -> None:
        out1 = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        # abort 第一个
        engine.abort_action({"run_id": out1["run_id"], "reason": "ut"})
        listed_w = engine.list_action({"status": "waiting_user"})
        listed_a = engine.list_action({"status": "aborted"})
        self.assertTrue(any(r["run_id"] == out1["run_id"] for r in listed_a["runs"]))
        self.assertFalse(any(r["run_id"] == out1["run_id"] for r in listed_w["runs"]))

    def test_list_table_format(self) -> None:
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        listed = engine.list_action({"format": "table", "limit": 5})
        self.assertIn("table", listed)
        text = listed["table"]
        self.assertIn("RUN_ID", text)
        self.assertIn("STATUS", text)

    def test_abort_twice_yields_terminal_error(self) -> None:
        out = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        first = engine.abort_action({"run_id": out["run_id"], "reason": "ut"})
        self.assertEqual(first["status"], "aborted")
        with self.assertRaises(WorkflowError) as ctx:
            engine.abort_action({"run_id": out["run_id"]})
        self.assertEqual(ctx.exception.code, ErrorCode.RUN_ALREADY_TERMINAL)

    def test_status_not_found(self) -> None:
        with self.assertRaises(WorkflowError) as ctx:
            engine.status_action({"run_id": "wf-does-not-exist"})
        self.assertEqual(ctx.exception.code, ErrorCode.RUN_NOT_FOUND)


class ExecutorsTest(unittest.TestCase):
    def test_executors_action_returns_4_builtins(self) -> None:
        out = list_executors({})
        names = {e["name"] for e in out["executors"]}
        self.assertEqual(names, {"caller", "claude", "codex", "mock"})


if __name__ == "__main__":
    unittest.main()
