import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.template import evaluate_condition, redact_secrets, render  # noqa: E402


class RenderTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(render("hi {{name}}", {"name": "alice"}), "hi alice")

    def test_dot_path(self):
        self.assertEqual(
            render("v={{n.x}}", {"n": {"x": 7}}, strict_vars=False), "v=7"
        )

    def test_strict_undefined_raises(self):
        with self.assertRaises(WorkflowError) as ctx:
            render("{{missing}}", {})
        self.assertEqual(ctx.exception.code, ErrorCode.VAR_NOT_IN_SCOPE)

    def test_non_strict_leaves_placeholder(self):
        self.assertEqual(
            render("{{x}}={{y}}", {"x": 1}, strict_vars=False), "1={{y}}"
        )

    def test_redact(self):
        out = redact_secrets("token=abc123 trailer", ["abc123"])
        self.assertIn("***REDACTED***", out)
        self.assertNotIn("abc123", out)


class ConditionTest(unittest.TestCase):
    def test_eq(self):
        self.assertTrue(evaluate_condition("{{x}} == 1", {"x": 1}))
        self.assertFalse(evaluate_condition("{{x}} == 2", {"x": 1}))

    def test_and_or(self):
        self.assertTrue(evaluate_condition("{{a}} > 0 && {{b}} == 'ok'", {"a": 1, "b": "ok"}))
        self.assertTrue(evaluate_condition("{{a}} == 0 || {{b}} == 'ok'", {"a": 1, "b": "ok"}))
        self.assertFalse(evaluate_condition("{{a}} == 0 && {{b}} == 'ok'", {"a": 1, "b": "ok"}))

    def test_not(self):
        self.assertTrue(evaluate_condition("!({{x}} == 0)", {"x": 1}))

    def test_bool_literals(self):
        self.assertTrue(evaluate_condition("{{x}} == true", {"x": True}))
        self.assertTrue(evaluate_condition("{{x}} == false", {"x": False}))

    def test_undefined_raises(self):
        with self.assertRaises(WorkflowError) as ctx:
            evaluate_condition("{{missing}} == 1", {})
        self.assertEqual(ctx.exception.code, ErrorCode.VAR_NOT_IN_SCOPE)

    def test_rejects_python_eval(self):
        for bad in ["__import__('os')", "1+1", "x**2"]:
            with self.assertRaises(WorkflowError):
                evaluate_condition(bad, {"x": 2})


if __name__ == "__main__":
    unittest.main()
