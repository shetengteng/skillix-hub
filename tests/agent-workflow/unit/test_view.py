"""TC-VW: view 命令单测。"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402
from lib.errors import ErrorCode, WorkflowError  # noqa: E402
from lib.view import templates as view_templates  # noqa: E402
from lib.view.render import (  # noqa: E402
    render_overview_html,
    render_run_detail_html,
    view_action,
)

WAIT_YAML = """
name: t-view
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


class RenderTest(unittest.TestCase):
    def test_render_overview_with_empty(self) -> None:
        html = render_overview_html([], project_root="/tmp/x")
        self.assertIn("<!doctype html>", html)
        self.assertIn("no runs found", html)

    def test_render_overview_with_run(self) -> None:
        runs = [
            {
                "run_id": "wf-xyz",
                "workflow_name": "demo",
                "status": "completed",
                "history_count": 3,
                "last_alias": "final",
                "updated_at": "2026-05-27T10:00:00Z",
            }
        ]
        html = render_overview_html(runs, project_root="/x")
        self.assertIn("wf-xyz", html)
        self.assertIn("demo", html)
        self.assertIn("completed", html)
        self.assertIn("./wf-xyz.html", html)

    def test_render_run_detail_basic(self) -> None:
        state = {
            "run_id": "wf-xyz",
            "status": "completed",
            "caller": "ut",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:01Z",
            "vars": {"x": "y", "_secrets": ["x"]},
            "cursor": {"path": []},
            "history": [
                {"alias": "a", "type": "agent_call", "status": "completed",
                 "started_at": "t0", "ended_at": "t1", "duration_ms": 100},
            ],
        }
        workflow = {
            "name": "demo",
            "nodes": [
                {"alias": "a", "type": "agent_call", "executor": "mock", "output": "x"},
                {"alias": "loop1", "type": "loop", "condition": "{{x}} == y", "max_iterations": 3,
                 "body": [{"alias": "inner", "type": "sleep", "seconds": 1}]},
            ],
        }
        events = [{"ts": "t0", "type": "run_start", "run_id": "wf-xyz"}]
        html = render_run_detail_html(state, workflow, events)
        self.assertIn("wf-xyz", html)
        self.assertIn("alias", html.lower())
        # _secrets 字段不应出现在 vars 区域
        self.assertNotIn('"_secrets"', html)
        # 嵌套节点缩进
        self.assertIn("indented-1", html)


class ViewActionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-vw-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        os.environ.pop("AGENT_WORKFLOW_ENABLE_MOCK", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_view_single_run(self) -> None:
        out = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        run_id = out["run_id"]
        custom_path = self.tmp / "out" / "single.html"
        result = view_action({"run_id": run_id, "out": str(custom_path), "open": False})
        self.assertEqual(result["mode"], "run")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["opened"], False)
        path = Path(result["path"])
        self.assertTrue(path.exists())
        content = path.read_text("utf-8")
        self.assertIn(run_id, content)
        self.assertIn("wait_user", content)

    def test_view_overview_default(self) -> None:
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        result = view_action({"open": False})
        self.assertEqual(result["mode"], "overview")
        self.assertEqual(result["run_count"], 2)
        self.assertEqual(result["detail_count"], 2)
        idx = Path(result["path"])
        self.assertTrue(idx.exists())
        self.assertEqual(idx.name, "index.html")
        # 每个 run 都有详情 html
        details = sorted(p.name for p in idx.parent.iterdir() if p.suffix == ".html")
        self.assertEqual(len(details), 3)  # 1 index + 2 runs

    def test_view_run_not_found(self) -> None:
        with self.assertRaises(WorkflowError) as ctx:
            view_action({"run_id": "wf-does-not-exist", "open": False})
        self.assertEqual(ctx.exception.code, ErrorCode.RUN_NOT_FOUND)


class TemplateLoaderTest(unittest.TestCase):
    """T-VW-T: 模板加载器自身契约。"""

    def test_load_known_templates(self) -> None:
        for name in ("base.css", "run.css", "run.html", "overview.html",
                     "theme.js", "overview.js",
                     "fragments/node_row.html", "fragments/history_row.html",
                     "fragments/event_row.html", "fragments/run_row.html",
                     "fragments/theme_toggle.html"):
            content = view_templates.load(name)
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 0, f"template {name} is empty")

    def test_missing_template_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            view_templates.load("does-not-exist.html")

    def test_render_safe_substitute_keeps_unknown_placeholders(self) -> None:
        # 用 base.css 渲染一个没意义的占位，确保 safe_substitute 不抛 KeyError
        rendered = view_templates.render("base.css")  # base.css 不含 $var
        self.assertIn(":root", rendered)
        self.assertIn("--background", rendered)

    def test_no_inline_html_or_css_strings_in_render_py(self) -> None:
        """硬卡：render.py 不应再持有 _BASE_CSS / _RUN_DETAIL_CSS 等大块静态字符串常量。"""
        render_py = Path(__file__).resolve().parents[3] / "skills" / "agent-workflow" / "lib" / "view" / "render.py"
        content = render_py.read_text("utf-8")
        forbidden_constants = ["_BASE_CSS = ", "_RUN_DETAIL_CSS = ", "_OVERVIEW_JS = "]
        for ident in forbidden_constants:
            self.assertNotIn(
                ident, content,
                f"render.py 仍包含大块静态资源常量 {ident}；模板应抽到 templates/ 目录"
            )


if __name__ == "__main__":
    unittest.main()
