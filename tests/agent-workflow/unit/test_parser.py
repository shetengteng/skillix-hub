import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.parser import parse_yaml, validate_action  # noqa: E402


GOOD_YAML = """
name: t-good
nodes:
  - alias: a
    type: agent_call
    executor: caller
    prompt: "hi"
    output: greet
"""

BAD_L1_YAML = """
name: t-bad
nodes:
  - alias: a
    type: agent_call
    executor: caller
    prompt: "missing close
    output: x
"""

BAD_L2_YAML = """
name: t-bad
nodes:
  - alias: a
    type: agent_call
    executor: caller
    prompt: "hi"
"""

BAD_L3_YAML = """
name: t-bad
nodes:
  - alias: a
    type: agent_call
    executor: caller
    prompt: "ref {{undefined}}"
    output: result
"""


class L1Test(unittest.TestCase):
    def test_good_yaml(self):
        self.assertEqual(parse_yaml(GOOD_YAML)["name"], "t-good")

    def test_l1_failure(self):
        with self.assertRaises(WorkflowError) as ctx:
            parse_yaml(BAD_L1_YAML)
        self.assertEqual(ctx.exception.code, ErrorCode.YAML_PARSE_ERROR)


class L2Test(unittest.TestCase):
    def test_missing_output(self):
        with self.assertRaises(WorkflowError) as ctx:
            validate_action({"workflow": BAD_L2_YAML, "allow_missing_executors": True})
        self.assertEqual(ctx.exception.code, ErrorCode.WORKFLOW_INVALID)
        violations = ctx.exception.extras.get("violations") or []
        codes = {v["code"] for v in violations}
        self.assertIn(ErrorCode.NODE_OUTPUT_REQUIRED, codes)


class L3Test(unittest.TestCase):
    def test_undefined_var(self):
        with self.assertRaises(WorkflowError) as ctx:
            validate_action({"workflow": BAD_L3_YAML, "allow_missing_executors": True})
        violations = ctx.exception.extras.get("violations") or []
        codes = {v["code"] for v in violations}
        self.assertIn(ErrorCode.VAR_NOT_IN_SCOPE, codes)


class HappyPathTest(unittest.TestCase):
    def test_validate_ok(self):
        out = validate_action({"workflow": GOOD_YAML, "allow_missing_executors": True})
        self.assertEqual(out["summary"]["name"], "t-good")
        self.assertEqual(out["summary"]["node_count"], 1)
        self.assertIn("caller", out["summary"]["executors_used"])


if __name__ == "__main__":
    unittest.main()
