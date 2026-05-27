"""T10.4 + caller 接力：start → 关闭 caller → 新进程 list → status → advance 续跑。"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402

CALLER_HANDOFF_YAML = """
name: t-handoff
executors:
  mock: { kind: mock }
nodes:
  - alias: design
    type: agent_call
    executor: caller
    prompt: "draft design for handoff test"
    output: design_doc
  - alias: implement
    type: agent_call
    executor: mock
    prompt: "implement {{design_doc}}"
    output: code
"""

TOOL_PATH = Path(__file__).resolve().parents[3] / "skills" / "agent-workflow" / "tool.py"


def _run_cli(action: str, params: dict, *, cwd: Path, env: dict) -> dict:
    import json

    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(TOOL_PATH), action, json.dumps(params)],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        timeout=15,
    )
    text = proc.stdout.decode("utf-8", "replace") or proc.stderr.decode("utf-8", "replace")
    return json.loads(text)


class CallerHandoffTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-ho-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"
        os.environ["AGENT_WORKFLOW_MOCK_IMPLEMENT"] = "code-ok"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        os.environ.pop("AGENT_WORKFLOW_ENABLE_MOCK", None)
        os.environ.pop("AGENT_WORKFLOW_MOCK_IMPLEMENT", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_in_process_handoff(self) -> None:
        """同一 Python 进程：start → status → advance；模拟 caller 抓到 payload 后接力。"""
        out = engine.start_action({"workflow": CALLER_HANDOFF_YAML, "caller": "caller-A"})
        self.assertEqual(out["action"], "execute_agent")
        run_id = out["run_id"]

        # 模拟"原 caller 死掉"，新 caller 用 list 找到运行中的 run
        listed = engine.list_action({"status": "awaiting_agent", "limit": 5})
        self.assertGreaterEqual(listed["count"], 1)
        self.assertTrue(any(r["run_id"] == run_id for r in listed["runs"]))

        # 新 caller 拿 status 恢复上下文
        status = engine.status_action({"run_id": run_id})
        self.assertEqual(status["status"], "awaiting_agent")
        self.assertEqual(status["last_payload"]["alias"], "design")
        prompt = status["last_payload"]["prompt"]
        self.assertIn("draft design", prompt)

        # 新 caller 假装 LLM 回答，调 advance
        result = engine.advance_action({"run_id": run_id, "result": "design-doc-v1"})
        self.assertEqual(result["action"], "completed")
        self.assertEqual(result["vars"]["design_doc"], "design-doc-v1")
        self.assertEqual(result["vars"]["code"], "code-ok")

    def test_cross_process_handoff(self) -> None:
        """跨进程：用 subprocess 跑 tool.py CLI，模拟真实 caller 进程切换。"""
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent.parent)}

        started = _run_cli(
            "start",
            {"workflow": CALLER_HANDOFF_YAML, "caller": "proc-A"},
            cwd=self.tmp,
            env=env,
        )
        self.assertEqual(started["result"]["action"], "execute_agent")
        run_id = started["result"]["run_id"]

        # 模拟新进程：list → status → advance
        listed = _run_cli("list", {"status": "awaiting_agent"}, cwd=self.tmp, env=env)
        self.assertGreaterEqual(listed["result"]["count"], 1)
        run_ids = [r["run_id"] for r in listed["result"]["runs"]]
        self.assertIn(run_id, run_ids)

        status = _run_cli("status", {"run_id": run_id}, cwd=self.tmp, env=env)
        self.assertEqual(status["result"]["last_payload"]["alias"], "design")

        result = _run_cli(
            "advance",
            {"run_id": run_id, "result": "design-cross-proc"},
            cwd=self.tmp,
            env=env,
        )
        self.assertEqual(result["result"]["action"], "completed")
        self.assertEqual(result["result"]["vars"]["design_doc"], "design-cross-proc")


if __name__ == "__main__":
    unittest.main()
