"""view_action 命令对外 contract 测试（v1.5.3 SPA 改造后）。

v1.5.3 起 view 子系统改为 SPA：Python 端只输出 ``data.js``（``window.__AW_DATA__``），
浏览器侧 JS 渲染。本测试覆盖：
- view_action 返回字段（mode / run_id / run_count / path / url / opened）
- overview 模式下 index.html + _assets/* 全部生成
- single-run 模式下 url 含 ``#<run_id>`` 锚点
- 静态资源（CSS/JS/HTML shell）固定复制到 _assets/ 与根目录
- run_id 不存在时返回 RUN_NOT_FOUND
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402
from lib.view.render import view_action  # noqa: E402

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

EXPECTED_ASSETS = (
    "base.css", "overview.css", "run.css",
    "theme.js", "overview.js", "workflow.js",
    "data.js",
)


class ViewActionContractTest(unittest.TestCase):
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

    def test_overview_returns_index_path(self) -> None:
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        result = view_action({"open": False})
        self.assertEqual(result["mode"], "overview")
        self.assertIsNone(result["run_id"])
        self.assertEqual(result["run_count"], 2)
        self.assertFalse(result["opened"])
        path = Path(result["path"])
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "index.html")

    def test_single_run_url_has_hash_anchor(self) -> None:
        out = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        run_id = out["run_id"]
        result = view_action({"run_id": run_id, "open": False})
        self.assertEqual(result["mode"], "run")
        self.assertEqual(result["run_id"], run_id)
        self.assertTrue(result["url"].endswith(f"#{run_id}"))
        self.assertTrue(Path(result["path"]).name == "workflow.html")

    def test_static_assets_and_data_js_emitted(self) -> None:
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        result = view_action({"open": False})
        views_dir = Path(result["views_dir"])
        for shell in ("index.html", "workflow.html"):
            self.assertTrue((views_dir / shell).exists(), f"missing shell: {shell}")
        for asset in EXPECTED_ASSETS:
            self.assertTrue((views_dir / "_assets" / asset).exists(), f"missing asset: {asset}")

    def test_data_js_contains_runs_array(self) -> None:
        out = engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        run_id = out["run_id"]
        result = view_action({"open": False})
        data_text = Path(result["data_path"]).read_text("utf-8")
        # data.js 形如：`// comment\nwindow.__AW_DATA__ = {...};\n`
        self.assertIn("window.__AW_DATA__", data_text)
        json_str = data_text.split("=", 1)[1].rstrip().rstrip(";").strip()
        payload = json.loads(json_str)
        self.assertIn("runs", payload)
        self.assertTrue(any(r["run_id"] == run_id for r in payload["runs"]))

    def test_custom_out_directory(self) -> None:
        engine.start_action({"workflow": WAIT_YAML, "caller": "ut"})
        custom = self.tmp / "my-views"
        result = view_action({"out": str(custom), "open": False})
        self.assertEqual(result["views_dir"], str(custom))
        self.assertTrue((custom / "index.html").exists())

    def test_missing_run_id_is_tolerated(self) -> None:
        """v1.5.3 SPA: 不存在的 run_id 不抛错，data.js 里也不会有它（前端显示 not found）。"""
        result = view_action({"run_id": "wf-does-not-exist", "open": False})
        self.assertEqual(result["mode"], "run")
        self.assertEqual(result["run_id"], "wf-does-not-exist")
        self.assertTrue(result["url"].endswith("#wf-does-not-exist"))
        data_text = Path(result["data_path"]).read_text("utf-8")
        json_str = data_text.split("=", 1)[1].rstrip().rstrip(";").strip()
        payload = json.loads(json_str)
        self.assertFalse(any(r["run_id"] == "wf-does-not-exist" for r in payload["runs"]))


if __name__ == "__main__":
    unittest.main()
