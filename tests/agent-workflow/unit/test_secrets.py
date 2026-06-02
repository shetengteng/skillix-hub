"""T20.8 secrets：$ENV 展开 + events/audit/history 脱敏。"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine, store  # noqa: E402
from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.template import collect_secret_values, expand_env_in_vars  # noqa: E402

SECRET_YAML = """
name: t-secret
executors:
  mock: { kind: mock }
vars:
  api_key: "$ENV:UT_SECRET_API_KEY"
  user: "alice"
  _secrets: ["api_key"]
nodes:
  - alias: call
    type: agent_call
    executor: mock
    prompt: "key={{api_key}} user={{user}}"
    output: result
"""


class ExpandEnvTest(unittest.TestCase):
    def test_expand_basic(self) -> None:
        os.environ["UT_X"] = "secret-x"
        try:
            out = expand_env_in_vars({"a": "$ENV:UT_X", "b": "literal"})
            self.assertEqual(out["a"], "secret-x")
            self.assertEqual(out["b"], "literal")
        finally:
            os.environ.pop("UT_X", None)

    def test_expand_missing_raises(self) -> None:
        os.environ.pop("UT_MISSING", None)
        with self.assertRaises(WorkflowError) as ctx:
            expand_env_in_vars({"a": "$ENV:UT_MISSING"})
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)

    def test_collect_secret_values(self) -> None:
        out = collect_secret_values({"api_key": "sk-abc", "user": "alice", "_secrets": ["api_key"]})
        self.assertEqual(out, ["sk-abc"])

    def test_collect_secret_values_dedupe_and_sort(self) -> None:
        out = collect_secret_values(
            {
                "a": "longer-secret-value",
                "b": "short",
                "c": "longer-secret-value",
                "_secrets": ["a", "b", "c"],
            }
        )
        # 去重 + 按长度倒序
        self.assertEqual(out, ["longer-secret-value", "short"])


class SecretsE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-sec-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        # 把 store 全局 base 重定向到 tmp（避免污染用户真实的 ~/.config/agent-workflow/）
        self._original_global_base = store.GLOBAL_BASE
        store.GLOBAL_BASE = self.tmp / ".agent-workflow"
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"
        os.environ["UT_SECRET_API_KEY"] = "sk-supersecret-XYZ"
        os.environ["AGENT_WORKFLOW_MOCK_CALL"] = "got sk-supersecret-XYZ ok"

    def tearDown(self) -> None:
        store.GLOBAL_BASE = self._original_global_base
        os.chdir(self._cwd)
        for k in (
            "AGENT_WORKFLOW_ENABLE_MOCK",
            "UT_SECRET_API_KEY",
            "AGENT_WORKFLOW_MOCK_CALL",
        ):
            os.environ.pop(k, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_secret_is_redacted_in_events_and_audit(self) -> None:
        out = engine.start_action({"workflow": SECRET_YAML, "caller": "ut"})
        self.assertEqual(out["action"], "completed")
        run_dir = self.tmp / ".agent-workflow" / "runs" / out["run_id"]

        events = (run_dir / "events.ndjson").read_text("utf-8")
        audit = (run_dir / "audit.log").read_text("utf-8")
        # events / audit 不应包含 secret 明文（mock executor 默认不打印 stdout，
        # 但即便后续写入 prompt/result 等场景也必须脱敏）
        self.assertNotIn("sk-supersecret-XYZ", events)
        self.assertNotIn("sk-supersecret-XYZ", audit)

    def test_secret_is_redacted_in_history(self) -> None:
        out = engine.start_action({"workflow": SECRET_YAML, "caller": "ut"})
        state_file = self.tmp / ".agent-workflow" / "runs" / out["run_id"] / "state.json"
        state = json.loads(state_file.read_text("utf-8"))
        history = state.get("history") or []
        self.assertGreater(len(history), 0)
        for entry in history:
            blob = json.dumps(entry, ensure_ascii=False)
            self.assertNotIn("sk-supersecret-XYZ", blob)


if __name__ == "__main__":
    unittest.main()
