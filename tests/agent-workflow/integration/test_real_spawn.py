"""真实 SpawnExecutor 集成测试。
- python3 echo：永远跑（保证 spawn 闭环本身正确）
- claude -p：opt-in，需设置 AGENT_WORKFLOW_REAL_CLAUDE=1 才跑
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# tests/agent-workflow/integration/test_real_spawn.py
# parents[0]=integration / parents[1]=agent-workflow / parents[2]=tests / parents[3]=<repo>
TOOL = Path(__file__).resolve().parents[3] / "skills" / "agent-workflow" / "tool.py"

PY_FLOW = """
name: it-spawn-py
executors:
  echo-llm:
    kind: spawn
    cmd: ["python3", "-c", "import sys; data=sys.stdin.read(); print(f'len={len(data)}')"]
    input_mode: stdin
    output_parser: text
    stall_timeout_ms: 10000

config:
  chain_timeout_ms: 30000

nodes:
  - alias: ping
    type: agent_call
    executor: echo-llm
    prompt: "hello world"
    output: result
"""

CLAUDE_FLOW = """
name: it-spawn-claude
executors:
  claude:
    kind: spawn
    cmd: ["claude", "-p"]
    input_mode: stdin
    stall_timeout_ms: 30000
    timeout_ms: 60000

config:
  chain_timeout_ms: 90000

nodes:
  - alias: ask
    type: agent_call
    executor: claude
    prompt: "Reply with exactly the single word: PONG"
    output: answer
"""


class RealSpawnTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-it-"))
        (self.tmp / "pyproject.toml").write_text("[project]\nname='it'\n", "utf-8")
        self._cwd = Path.cwd()
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, action: str, params: dict) -> dict:
        out = subprocess.run(
            ["python3", str(TOOL), action, json.dumps(params)],
            cwd=str(self.tmp),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(out.returncode, 0, msg=out.stderr)
        return json.loads(out.stdout)

    def test_python_spawn_round_trip(self) -> None:
        resp = self._run("start", {"workflow": PY_FLOW, "caller": "it"})
        self.assertIsNone(resp.get("error"))
        result = resp["result"]
        self.assertEqual(result["action"], "completed")
        # echo-llm stdout 形如 "len=11"
        self.assertTrue(
            result["vars"]["result"].startswith("len="),
            msg=result["vars"],
        )

    @unittest.skipUnless(
        os.environ.get("AGENT_WORKFLOW_REAL_CLAUDE") == "1" and shutil.which("claude"),
        "claude 真实调用 opt-in：设置 AGENT_WORKFLOW_REAL_CLAUDE=1 启用",
    )
    def test_real_claude_pong(self) -> None:
        resp = self._run("start", {"workflow": CLAUDE_FLOW, "caller": "it"})
        self.assertIsNone(resp.get("error"))
        answer = resp["result"]["vars"]["answer"]
        # 兼容 "PONG" / "PONG.\n" / 带其它包装
        self.assertIn("PONG", answer.upper())


AGENT_CTX_FLOW = """
name: it-agent-ctx-spawn
description: 用 cat 作 echo-back spawn executor，验证 stdin 是否真拼了 agent 前缀。
executors:
  echo_cat:
    kind: spawn
    cmd: ["cat"]
    input_mode: stdin
    output_parser: text
    stall_timeout_ms: 10000

nodes:
  - alias: roleonly
    type: agent_call
    executor: echo_cat
    agent:
      role: "You are SENIOR ARCHITECT."
    prompt: "the original task"
    output: out_role_only

  - alias: roleandskills
    type: agent_call
    executor: echo_cat
    agent:
      role: "You are CODE REVIEWER."
      skills:
        - "kb-search"
        - "git-diff"
    prompt: "review the code"
    output: out_role_skills

  - alias: noagent
    type: agent_call
    executor: echo_cat
    prompt: "no agent here"
    output: out_no_agent
"""


@unittest.skipUnless(
    shutil.which("cat"),
    "本测试用 POSIX `cat` 作 echo-back spawn executor；非 POSIX 平台跳过",
)
class AgentContextSpawnE2ETest(unittest.TestCase):
    """v1.5.4 agent 上下文真实 spawn 集成：
    把 stdin 用 cat 原样回吐，验证 SpawnExecutor 确实把 agent.role/skills 拼到 stdin 前。
    覆盖 3 个 case：仅 role / role+skills / 无 agent（向后兼容）。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-it-ag-"))
        (self.tmp / "pyproject.toml").write_text("[project]\nname='it'\n", "utf-8")
        self._cwd = Path.cwd()
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_spawn_receives_agent_prefix(self) -> None:
        out = subprocess.run(
            ["python3", str(TOOL), "start",
             json.dumps({"workflow": AGENT_CTX_FLOW, "caller": "it-ag"})],
            cwd=str(self.tmp),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(out.returncode, 0, msg=out.stderr)
        resp = json.loads(out.stdout)
        self.assertIsNone(resp.get("error"))
        result = resp["result"]
        self.assertEqual(result["action"], "completed")
        v = result["vars"]

        role_only = v["out_role_only"]
        self.assertIn("=== Role ===\nYou are SENIOR ARCHITECT.", role_only)
        self.assertIn("=== Task ===\nthe original task", role_only)
        self.assertNotIn("=== Skills", role_only)

        role_skills = v["out_role_skills"]
        self.assertIn("=== Role ===\nYou are CODE REVIEWER.", role_skills)
        self.assertIn("=== Skills (advisory) ===\n- kb-search\n- git-diff", role_skills)
        self.assertIn("=== Task ===\nreview the code", role_skills)

        no_agent = v["out_no_agent"]
        self.assertEqual(no_agent, "no agent here")
        self.assertNotIn("=== Role", no_agent)
        self.assertNotIn("=== Task", no_agent)


if __name__ == "__main__":
    unittest.main()
