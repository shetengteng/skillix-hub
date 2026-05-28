"""agent_call 节点 agent 上下文（role + skills）覆盖：

- caller payload 透传（含/不含 agent 两种 case）
- spawn _apply_agent_prefix 拼接（仅 role / role+skills / skills 空 / agent=None）
- _prepare_agent 中 role 的 {{var}} 渲染
- schema 校验合法 / 非法 case
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib.errors import WorkflowError  # noqa: E402
from lib.executors.base import _apply_agent_prefix  # noqa: E402
from lib.executors.caller import CallerExecutor  # noqa: E402
from lib.nodes.agent_call import _prepare_agent  # noqa: E402
from lib.parser import validate_action  # noqa: E402


class CallerPayloadAgentTest(unittest.TestCase):
    def test_caller_payload_includes_agent_when_present(self) -> None:
        exe = CallerExecutor()
        outcome = exe.execute(
            prompt="hello",
            node={"alias": "n1", "output": "x"},
            vars_={},
            run_context={},
            agent={"role": "You are an architect.", "skills": ["a", "b"]},
        )
        self.assertEqual(outcome.kind, "needs_caller")
        self.assertIn("agent", outcome.payload)
        self.assertEqual(outcome.payload["agent"]["role"], "You are an architect.")
        self.assertEqual(outcome.payload["agent"]["skills"], ["a", "b"])

    def test_caller_payload_omits_agent_when_absent(self) -> None:
        exe = CallerExecutor()
        outcome = exe.execute(
            prompt="hello",
            node={"alias": "n1", "output": "x"},
            vars_={},
            run_context={},
        )
        self.assertNotIn("agent", outcome.payload)

    def test_caller_payload_omits_agent_when_empty_dict(self) -> None:
        exe = CallerExecutor()
        outcome = exe.execute(
            prompt="hello",
            node={"alias": "n1", "output": "x"},
            vars_={},
            run_context={},
            agent={},
        )
        self.assertNotIn("agent", outcome.payload)


class SpawnAgentPrefixTest(unittest.TestCase):
    def test_role_only_prefix(self) -> None:
        out = _apply_agent_prefix("the task", {"role": "You are an architect."})
        self.assertIn("=== Role ===\nYou are an architect.", out)
        self.assertIn("=== Task ===\nthe task", out)
        self.assertNotIn("=== Skills", out)

    def test_role_and_skills_prefix(self) -> None:
        out = _apply_agent_prefix(
            "the task",
            {"role": "You are X.", "skills": ["k1", "k2"]},
        )
        self.assertIn("=== Role ===\nYou are X.", out)
        self.assertIn("=== Skills (advisory) ===\n- k1\n- k2", out)
        self.assertTrue(out.endswith("=== Task ===\nthe task"))

    def test_skills_only_prefix(self) -> None:
        out = _apply_agent_prefix("the task", {"skills": ["only"]})
        self.assertIn("=== Skills (advisory) ===\n- only", out)
        self.assertIn("=== Task ===\nthe task", out)
        self.assertNotIn("=== Role", out)

    def test_none_agent_passthrough(self) -> None:
        self.assertEqual(_apply_agent_prefix("the task", None), "the task")

    def test_empty_role_and_skills_passthrough(self) -> None:
        self.assertEqual(_apply_agent_prefix("the task", {}), "the task")
        self.assertEqual(_apply_agent_prefix("the task", {"role": "   ", "skills": []}), "the task")


class PrepareAgentTest(unittest.TestCase):
    def test_renders_role_vars(self) -> None:
        node = {"agent": {"role": "You are a {{persona}}.", "skills": ["s1"]}}
        result = _prepare_agent(node, {"persona": "architect"})
        self.assertEqual(result["role"], "You are a architect.")
        self.assertEqual(result["skills"], ["s1"])

    def test_returns_none_when_no_agent_key(self) -> None:
        self.assertIsNone(_prepare_agent({}, {}))

    def test_returns_none_for_empty_agent(self) -> None:
        self.assertIsNone(_prepare_agent({"agent": {}}, {}))

    def test_filters_blank_skills(self) -> None:
        node = {"agent": {"skills": ["valid", "", "  ", None, "valid2"]}}
        result = _prepare_agent(node, {})
        self.assertEqual(result["skills"], ["valid", "valid2"])


class SchemaValidationAgentTest(unittest.TestCase):
    BASE_WORKFLOW = {
        "name": "agent-schema-test",
        "nodes": [
            {
                "alias": "n1",
                "type": "agent_call",
                "executor": "caller",
                "prompt": "hello",
                "output": "x",
            }
        ],
    }

    def _validate(self, agent_value: object) -> dict:
        import copy
        wf = copy.deepcopy(self.BASE_WORKFLOW)
        wf["nodes"][0]["agent"] = agent_value
        return validate_action({"workflow": wf, "allow_missing_executors": True})

    def _expect_invalid(self, agent_value: object) -> None:
        import copy
        wf = copy.deepcopy(self.BASE_WORKFLOW)
        wf["nodes"][0]["agent"] = agent_value
        with self.assertRaises(WorkflowError) as cm:
            validate_action({"workflow": wf, "allow_missing_executors": True})
        err = cm.exception.to_dict()
        self.assertTrue(
            err.get("violations"),
            f"expected violations for agent={agent_value!r}, got {err!r}",
        )

    def test_valid_role_only(self) -> None:
        result = self._validate({"role": "You are X."})
        self.assertEqual(result["violations"], [])

    def test_valid_role_and_skills(self) -> None:
        result = self._validate({"role": "X", "skills": ["a", "b"]})
        self.assertEqual(result["violations"], [])

    def test_invalid_empty_agent(self) -> None:
        self._expect_invalid({})

    def test_invalid_unknown_field(self) -> None:
        self._expect_invalid({"role": "X", "unknown": "bad"})

    def test_invalid_skills_type(self) -> None:
        self._expect_invalid({"skills": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()
