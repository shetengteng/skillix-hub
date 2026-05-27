"""端到端：start → resume → completed（全程 mock）。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine, store  # noqa: E402

MOCK_YAML = """
name: ut-mock
vars:
  topic: "engine-tests"
executors:
  mock: { kind: mock }
nodes:
  - alias: research
    type: agent_call
    executor: mock
    prompt: "do {{topic}}"
    output: notes
  - alias: ask
    type: wait_user
    message: "approve {{notes}}?"
    schema:
      type: object
      required: [approved]
      properties:
        approved: { type: boolean }
        feedback: { type: string, default: "" }
  - alias: final
    type: agent_call
    executor: mock
    prompt: "final {{ask.approved}} {{notes}}"
    output: report
"""


class EngineE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-test-"))
        # 把项目根锚定到 tmp（detect 会找 .git 之类，没有则 fallback 到 cwd），所以直接 chdir
        self._original_cwd = Path.cwd()
        # 创建一个 marker 让 project root 落在 tmp
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"
        os.environ["AGENT_WORKFLOW_MOCK_RESEARCH"] = "n1 n2"
        os.environ["AGENT_WORKFLOW_MOCK_FINAL"] = "FINAL_OK"

    def tearDown(self) -> None:
        os.chdir(self._original_cwd)
        for key in [
            "AGENT_WORKFLOW_ENABLE_MOCK",
            "AGENT_WORKFLOW_MOCK_RESEARCH",
            "AGENT_WORKFLOW_MOCK_FINAL",
        ]:
            os.environ.pop(key, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_round_trip(self) -> None:
        out = engine.start_action({"workflow": MOCK_YAML, "caller": "unit-test"})
        self.assertEqual(out["action"], "wait_user")
        self.assertEqual(out["payload"]["alias"], "ask")
        self.assertIn("n1 n2", out["payload"]["message"])
        run_id = out["run_id"]

        # status 应给出 last_payload
        status = engine.status_action({"run_id": run_id})
        self.assertEqual(status["status"], "waiting_user")
        self.assertEqual(status["last_payload"]["alias"], "ask")

        resumed = engine.resume_action(
            {"run_id": run_id, "input": {"approved": True, "feedback": ""}}
        )
        self.assertEqual(resumed["action"], "completed")
        self.assertEqual(resumed["vars"]["report"], "FINAL_OK")
        self.assertEqual(resumed["vars"]["ask"]["approved"], True)

        listed = engine.list_action({"limit": 5, "format": "table"})
        self.assertEqual(listed["count"], 1)
        self.assertIn(run_id, listed["table"])

    def test_resume_input_schema_violation(self) -> None:
        out = engine.start_action({"workflow": MOCK_YAML, "caller": "unit-test"})
        run_id = out["run_id"]
        from lib.errors import ErrorCode, WorkflowError  # noqa: WPS433

        with self.assertRaises(WorkflowError) as ctx:
            engine.resume_action({"run_id": run_id, "input": {"approved": "nope"}})
        self.assertEqual(ctx.exception.code, ErrorCode.SCHEMA_VIOLATION)


if __name__ == "__main__":
    unittest.main()
