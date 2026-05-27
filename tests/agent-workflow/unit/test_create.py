"""TC-CR-01/02/03 + TC-VA-04/05/06 : create + validate L2/L4 边界。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib.builder.scaffold import create_action  # noqa: E402
from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.parser import validate_action  # noqa: E402


class CreateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-cr-"))
        self._cwd = Path.cwd()
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_list_templates(self) -> None:
        out = create_action({"action": "list_templates"})
        names = {t["name"] for t in out["templates"]}
        for required in {"research-and-implement", "cross-llm-pipeline", "code-review", "iterative-refine"}:
            self.assertIn(required, names)

    def test_from_template(self) -> None:
        out = create_action(
            {
                "action": "from_template",
                "template": "research-and-implement",
                "out": str(self.tmp / "wf.yaml"),
            }
        )
        path = Path(out["path"])
        self.assertTrue(path.exists())
        # 直接 validate 产物应通过
        validated = validate_action({"workflow": str(path), "allow_missing_executors": True})
        self.assertEqual(validated["violations"], [])

    def test_from_template_no_overwrite(self) -> None:
        target = self.tmp / "wf.yaml"
        target.write_text("placeholder", "utf-8")
        with self.assertRaises(WorkflowError) as ctx:
            create_action(
                {
                    "action": "from_template",
                    "template": "code-review",
                    "out": str(target),
                }
            )
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)

    def test_scaffold(self) -> None:
        out = create_action(
            {
                "action": "scaffold",
                "name": "demo",
                "out": str(self.tmp / "demo.yaml"),
                "nodes": [
                    {
                        "alias": "x",
                        "type": "agent_call",
                        "executor": "caller",
                        "prompt": "hi",
                        "output": "y",
                    }
                ],
            }
        )
        path = Path(out["path"])
        self.assertTrue(path.exists())
        result = validate_action({"workflow": str(path), "allow_missing_executors": True})
        self.assertEqual(result["summary"]["node_count"], 1)


class ValidateBoundaryTest(unittest.TestCase):
    def test_l2_unknown_executor_is_allowed_at_l2(self) -> None:
        """L2 schema 不限制 executor 名字（只限制是否字符串），但 L4 会拒绝。"""
        yaml_text = """
name: t-unknown
nodes:
  - alias: n
    type: agent_call
    executor: does-not-exist
    prompt: hi
    output: x
"""
        # L2 应通过；L4 应失败
        with self.assertRaises(WorkflowError) as ctx:
            validate_action({"workflow": yaml_text})
        codes = {v["code"] for v in ctx.exception.extras.get("violations") or []}
        self.assertIn(ErrorCode.EXECUTOR_NOT_FOUND, codes)

    def test_l4_skip_with_allow_missing(self) -> None:
        yaml_text = """
name: t-skip
nodes:
  - alias: n
    type: agent_call
    executor: does-not-exist
    prompt: hi
    output: x
"""
        out = validate_action({"workflow": yaml_text, "allow_missing_executors": True})
        self.assertEqual(out["violations"], [])
        self.assertIn("does-not-exist", out["summary"]["executors_used"])

    def test_loop_max_iterations_out_of_range(self) -> None:
        yaml_text = """
name: t-loop-range
nodes:
  - alias: l
    type: loop
    condition: "{{x}} == 1"
    max_iterations: 999
    body:
      - { alias: x, type: agent_call, executor: caller, prompt: p, output: x }
"""
        with self.assertRaises(WorkflowError) as ctx:
            validate_action({"workflow": yaml_text, "allow_missing_executors": True})
        violations = ctx.exception.extras.get("violations") or []
        self.assertGreater(len(violations), 0)
        self.assertTrue(
            all(v["level"] == "L2" for v in violations),
            f"expected L2 schema violations, got {violations}",
        )

    def test_sleep_seconds_out_of_range(self) -> None:
        yaml_text = """
name: t-sleep-range
nodes:
  - alias: s
    type: sleep
    seconds: 9999
"""
        with self.assertRaises(WorkflowError) as ctx:
            validate_action({"workflow": yaml_text, "allow_missing_executors": True})
        violations = ctx.exception.extras.get("violations") or []
        self.assertGreater(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
