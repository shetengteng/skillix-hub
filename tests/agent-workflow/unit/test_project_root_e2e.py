"""TC-PR-E2E-01..06 : project_root 链路端到端测试。

覆盖：
- caller 显式传 project_root → state.project_root + source 正确落盘
- workflow.project_root 字段 → caller 不传时回落到 YAML 值
- AGENT_WORKFLOW_PROJECT_ROOT env → 第三优先级
- spec.cwd 显式声明 → SpawnExecutor.cwd 被设置
- cmd 数组中 {{cwd}} / {{project_root}} 占位符被替换
- 老 state.json（不含 project_root 字段）能正常 status / resume（向后兼容）
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
from lib.executors.registry import get_executor  # noqa: E402
from lib.store import GLOBAL_BASE  # noqa: E402

MOCK_YAML_BASIC = """
name: ut-pr-basic
executors:
  mock: { kind: mock }
nodes:
  - alias: only_node
    type: agent_call
    executor: mock
    prompt: "hi"
    output: result
"""

def _yaml_with_project_root(project_root: str) -> str:
    """构造带 workflow.project_root 字段的 YAML（避免 str.format 与 YAML `{}` 冲突）。"""
    return (
        "name: ut-pr-yaml\n"
        f'project_root: "{project_root}"\n'
        "executors:\n"
        "  mock: { kind: mock }\n"
        "nodes:\n"
        "  - alias: only_node\n"
        "    type: agent_call\n"
        "    executor: mock\n"
        '    prompt: "hi"\n'
        "    output: result\n"
    )


class ProjectRootE2ETest(unittest.TestCase):
    """端到端验证：start_action 调用 resolver → 落 state → status 能读出。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-pr-e2e-")).resolve()
        self._original_cwd = Path.cwd()
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"
        os.environ["AGENT_WORKFLOW_MOCK_ONLY_NODE"] = "done"
        self._created_runs: list[str] = []

    def tearDown(self) -> None:
        os.chdir(self._original_cwd)
        for key in (
            "AGENT_WORKFLOW_ENABLE_MOCK",
            "AGENT_WORKFLOW_MOCK_ONLY_NODE",
            "AGENT_WORKFLOW_PROJECT_ROOT",
        ):
            os.environ.pop(key, None)
        # 清理本次测试创建的 run 目录（不污染全局）
        runs_root = GLOBAL_BASE / "runs"
        for run_id in self._created_runs:
            shutil.rmtree(runs_root / run_id, ignore_errors=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _record_run(self, result: dict) -> str:
        run_id = result["run_id"]
        self._created_runs.append(run_id)
        return run_id

    # ------------------------------------------------------------------
    # caller 显式传 project_root
    # ------------------------------------------------------------------

    def test_caller_explicit_project_root_lands_in_state(self) -> None:
        target = self.tmp / "explicit-target"
        target.mkdir()
        result = engine.start_action(
            {
                "workflow": MOCK_YAML_BASIC,
                "caller": "ut",
                "project_root": str(target),
            }
        )
        run_id = self._record_run(result)
        # 走完整条链
        self.assertEqual(result["action"], "completed")
        # status 应能读出 project_root + source
        status = engine.status_action({"run_id": run_id})
        self.assertEqual(status["project_root"], str(target.resolve()))
        self.assertEqual(status["project_root_source"], "caller_explicit")

    # ------------------------------------------------------------------
    # workflow.project_root（YAML 层声明）
    # ------------------------------------------------------------------

    def test_workflow_yaml_project_root_used_when_caller_silent(self) -> None:
        yaml_target = self.tmp / "yaml-target"
        yaml_target.mkdir()
        yaml = _yaml_with_project_root(str(yaml_target))
        result = engine.start_action({"workflow": yaml, "caller": "ut"})
        run_id = self._record_run(result)
        status = engine.status_action({"run_id": run_id})
        self.assertEqual(status["project_root"], str(yaml_target.resolve()))
        self.assertEqual(status["project_root_source"], "workflow_yaml")

    # ------------------------------------------------------------------
    # caller > workflow.project_root（优先级验证）
    # ------------------------------------------------------------------

    def test_caller_wins_over_workflow_yaml(self) -> None:
        yaml_target = self.tmp / "yaml-target"
        yaml_target.mkdir()
        caller_target = self.tmp / "caller-target"
        caller_target.mkdir()
        yaml = _yaml_with_project_root(str(yaml_target))
        result = engine.start_action(
            {
                "workflow": yaml,
                "caller": "ut",
                "project_root": str(caller_target),
            }
        )
        run_id = self._record_run(result)
        status = engine.status_action({"run_id": run_id})
        self.assertEqual(status["project_root"], str(caller_target.resolve()))
        self.assertEqual(status["project_root_source"], "caller_explicit")

    # ------------------------------------------------------------------
    # env 变量层
    # ------------------------------------------------------------------

    def test_env_project_root_when_no_caller_no_yaml(self) -> None:
        env_target = self.tmp / "env-target"
        env_target.mkdir()
        os.environ["AGENT_WORKFLOW_PROJECT_ROOT"] = str(env_target)
        result = engine.start_action({"workflow": MOCK_YAML_BASIC, "caller": "ut"})
        run_id = self._record_run(result)
        status = engine.status_action({"run_id": run_id})
        self.assertEqual(status["project_root"], str(env_target.resolve()))
        self.assertEqual(status["project_root_source"], "env")

    # ------------------------------------------------------------------
    # 向后兼容：老 state.json 没有 project_root 字段也能正常 status
    # ------------------------------------------------------------------

    def test_legacy_state_without_project_root_field(self) -> None:
        """模拟老版本创建的 state.json（无 project_root / source 字段），status 不能崩。"""
        result = engine.start_action({"workflow": MOCK_YAML_BASIC, "caller": "ut"})
        run_id = self._record_run(result)
        # 手动篡改 state.json 删除新字段，模拟从 v1.6 升级上来的老 run
        state_path = GLOBAL_BASE / "runs" / run_id / "state.json"
        state = json.loads(state_path.read_text("utf-8"))
        state.pop("project_root", None)
        state.pop("project_root_source", None)
        state_path.write_text(json.dumps(state), "utf-8")
        # status 必须能读，且字段为 None（不抛异常）
        status = engine.status_action({"run_id": run_id})
        self.assertIsNone(status["project_root"])
        self.assertIsNone(status["project_root_source"])


class CmdTemplateRenderingTest(unittest.TestCase):
    """patch ⑦：registry 在构造 SpawnExecutor 时渲染 cmd 数组中的 cwd 占位符。

    这是 codex --cd / cursor-agent --workspace 双通道的关键单元测试。
    """

    def test_cmd_placeholders_rendered_from_run_context(self) -> None:
        """spec.cwd 未声明 + run_context.project_root=/tmp/A → {{cwd}} 替换为 /tmp/A。"""
        workflow_executors = {
            "codex": {
                "kind": "spawn",
                "cmd": ["codex", "exec", "--skip-git-repo-check", "--cd", "{{cwd}}"],
            }
        }
        executor = get_executor(
            "codex",
            workflow_executors=workflow_executors,
            run_context={"project_root": "/tmp/A"},
        )
        # SpawnExecutor 把 cmd 存到 self.cmd
        self.assertEqual(
            executor.cmd,
            ["codex", "exec", "--skip-git-repo-check", "--cd", "/tmp/A"],
        )
        # spec.cwd 没声明 → executor.cwd 仍为 None（运行时 fallback 到 run_context）
        self.assertIsNone(executor.cwd)

    def test_spec_cwd_overrides_run_context_for_cmd_render(self) -> None:
        """spec.cwd 显式声明优先于 run_context.project_root 用于 cmd 渲染。"""
        workflow_executors = {
            "cursor-agent": {
                "kind": "spawn",
                "cmd": [
                    "cursor-agent",
                    "-p",
                    "--force",
                    "--trust",
                    "--workspace",
                    "{{project_root}}",
                ],
                "cwd": "/spec/cwd/value",
            }
        }
        executor = get_executor(
            "cursor-agent",
            workflow_executors=workflow_executors,
            run_context={"project_root": "/tmp/run-ctx"},
        )
        # spec.cwd 优先：cmd 里 {{project_root}} 被替换为 /spec/cwd/value
        self.assertEqual(
            executor.cmd,
            [
                "cursor-agent",
                "-p",
                "--force",
                "--trust",
                "--workspace",
                "/spec/cwd/value",
            ],
        )
        # SpawnExecutor.cwd 也是 spec.cwd
        self.assertEqual(executor.cwd, Path("/spec/cwd/value").expanduser())

    def test_no_cwd_no_placeholder_render(self) -> None:
        """都没声明 + cmd 不含占位符 → 原样返回，不破坏现有 YAML。"""
        workflow_executors = {
            "claude": {
                "kind": "spawn",
                "cmd": ["claude", "-p", "--dangerously-skip-permissions"],
            }
        }
        executor = get_executor(
            "claude",
            workflow_executors=workflow_executors,
            run_context=None,
        )
        self.assertEqual(
            executor.cmd,
            ["claude", "-p", "--dangerously-skip-permissions"],
        )
        self.assertIsNone(executor.cwd)

    def test_placeholders_in_cmd_with_no_cwd_kept_as_is(self) -> None:
        """spec 没 cwd + run_context 也没 project_root → 占位符原样保留（显式表明配置错误）。"""
        workflow_executors = {
            "codex": {
                "kind": "spawn",
                "cmd": ["codex", "exec", "--cd", "{{cwd}}"],
            }
        }
        executor = get_executor(
            "codex",
            workflow_executors=workflow_executors,
            run_context={"project_root": ""},
        )
        # 不替换，让运行时显式报错（比悄悄空着更安全）
        self.assertEqual(
            executor.cmd,
            ["codex", "exec", "--cd", "{{cwd}}"],
        )


if __name__ == "__main__":
    unittest.main()
