"""TC-PR-01..06 : project_root 6 级 fallback resolver 单元测试。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib.project_root import (  # noqa: E402
    MARKERS_BY_AUTHORITY,
    ProjectRootDecision,
    SOURCE_CALLER_EXPLICIT,
    SOURCE_ENV,
    SOURCE_FALLBACK_CWD,
    SOURCE_IDE_LABEL,
    SOURCE_MARKER_PREFIX,
    SOURCE_WORKFLOW_YAML,
    resolve_project_root,
)


class ResolverTest(unittest.TestCase):
    """6 级 fallback 必须按设计文档 §4.1 顺序解析。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-pr-")).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # Layer 1: caller_param 最高优先级
    # ------------------------------------------------------------------

    def test_layer1_caller_param_wins(self) -> None:
        """caller 显式传 project_root，无视 workflow.project_root / env / IDE label / cwd marker。"""
        # 同时设置 layer 2/3/4/5 应被命中的条件
        workflow = {"project_root": str(self.tmp / "yaml-root")}
        env = {
            "AGENT_WORKFLOW_PROJECT_ROOT": str(self.tmp / "env-root"),
            "CURSOR_WORKSPACE_LABEL": "ide-root",
            "PWD": str(self.tmp / "ide-root"),
        }
        # 在 cwd 做一个 .git marker
        git_root = self.tmp / "git-root"
        git_root.mkdir()
        (git_root / ".git").mkdir()

        decision = resolve_project_root(
            caller_param=str(self.tmp / "caller-root"),
            workflow=workflow,
            env=env,
            cwd=git_root,
        )
        self.assertEqual(decision.source, SOURCE_CALLER_EXPLICIT)
        self.assertEqual(decision.path, (self.tmp / "caller-root").expanduser())

    # ------------------------------------------------------------------
    # Layer 2: workflow.project_root
    # ------------------------------------------------------------------

    def test_layer2_workflow_yaml_wins_over_env(self) -> None:
        yaml_root = self.tmp / "yaml-root"
        yaml_root.mkdir()
        decision = resolve_project_root(
            caller_param=None,
            workflow={"project_root": str(yaml_root)},
            env={"AGENT_WORKFLOW_PROJECT_ROOT": str(self.tmp / "env-root")},
            cwd=self.tmp,
        )
        self.assertEqual(decision.source, SOURCE_WORKFLOW_YAML)
        self.assertEqual(decision.path, yaml_root.resolve())

    def test_layer2_workflow_yaml_ignored_when_empty(self) -> None:
        """workflow.project_root 是空字符串或非 str → 跳过此层。"""
        env_root = self.tmp / "env-root"
        env_root.mkdir()
        decision = resolve_project_root(
            caller_param=None,
            workflow={"project_root": "   "},  # whitespace-only
            env={"AGENT_WORKFLOW_PROJECT_ROOT": str(env_root)},
            cwd=self.tmp,
        )
        self.assertEqual(decision.source, SOURCE_ENV)
        self.assertEqual(decision.path, env_root.resolve())

    # ------------------------------------------------------------------
    # Layer 3: AGENT_WORKFLOW_PROJECT_ROOT env
    # ------------------------------------------------------------------

    def test_layer3_env_wins_over_ide(self) -> None:
        env_root = self.tmp / "env-root"
        env_root.mkdir()
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={
                "AGENT_WORKFLOW_PROJECT_ROOT": str(env_root),
                "CURSOR_WORKSPACE_LABEL": "ide-root",
                "PWD": str(self.tmp / "ide-root"),
            },
            cwd=self.tmp,
        )
        self.assertEqual(decision.source, SOURCE_ENV)
        self.assertEqual(decision.path, env_root.resolve())

    # ------------------------------------------------------------------
    # Layer 4: IDE workspace label
    # ------------------------------------------------------------------

    def test_layer4_cursor_workspace_label(self) -> None:
        """CURSOR_WORKSPACE_LABEL=foo + cwd 在 /x/foo/bar/ → project_root = /x/foo。"""
        workspace = self.tmp / "my-workspace"
        nested = workspace / "subdir" / "leaf"
        nested.mkdir(parents=True)
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={
                "CURSOR_WORKSPACE_LABEL": "my-workspace",
                "PWD": str(nested),
            },
            cwd=nested,
        )
        self.assertEqual(decision.source, SOURCE_IDE_LABEL)
        self.assertEqual(decision.path, workspace.resolve())

    def test_layer4_vscode_workspace_folders(self) -> None:
        """VSCODE_WORKSPACE_FOLDERS 是 JSON 数组，取第一个。"""
        workspace = self.tmp / "vs-workspace"
        workspace.mkdir()
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={
                "VSCODE_WORKSPACE_FOLDERS": f'["{workspace}", "/some/other/path"]',
            },
            cwd=self.tmp,
        )
        self.assertEqual(decision.source, SOURCE_IDE_LABEL)
        self.assertEqual(decision.path, workspace.resolve())

    def test_layer4_cursor_label_no_match_falls_through(self) -> None:
        """CURSOR_WORKSPACE_LABEL 设了但 cwd 路径里找不到同名目录 → 跳到 layer 5。"""
        marker_dir = self.tmp / "git-root"
        marker_dir.mkdir()
        (marker_dir / ".git").mkdir()
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={
                "CURSOR_WORKSPACE_LABEL": "totally-unrelated-label",
                "PWD": str(marker_dir),
            },
            cwd=marker_dir,
        )
        self.assertEqual(decision.source, f"{SOURCE_MARKER_PREFIX}.git")
        self.assertEqual(decision.path, marker_dir.resolve())

    # ------------------------------------------------------------------
    # Layer 5: marker 向上搜索（按权威性排序）
    # ------------------------------------------------------------------

    def test_layer5_git_marker_wins(self) -> None:
        """.git 在 outer 层，package.json 在 inner 层 → 选 outer（git 权威性更高）。"""
        outer = self.tmp / "outer"
        inner = outer / "inner"
        leaf = inner / "leaf"
        leaf.mkdir(parents=True)
        (outer / ".git").mkdir()
        (inner / "package.json").write_text("{}", "utf-8")
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={},
            cwd=leaf,
        )
        # 权威性：.git > package.json。MARKERS_BY_AUTHORITY 把 .git 排第一，
        # 所以先搜 .git 命中 outer 后立即停。
        self.assertEqual(decision.source, f"{SOURCE_MARKER_PREFIX}.git")
        self.assertEqual(decision.path, outer.resolve())

    def test_layer5_package_json_when_no_git(self) -> None:
        """无 .git 时退到 package.json。"""
        root = self.tmp / "node-proj"
        leaf = root / "src" / "utils"
        leaf.mkdir(parents=True)
        (root / "package.json").write_text("{}", "utf-8")
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={},
            cwd=leaf,
        )
        self.assertEqual(decision.source, f"{SOURCE_MARKER_PREFIX}package.json")
        self.assertEqual(decision.path, root.resolve())

    def test_layer5_claude_md_marker(self) -> None:
        """CLAUDE.md 也能被识别为项目根。"""
        root = self.tmp / "claude-proj"
        leaf = root / "subdir"
        leaf.mkdir(parents=True)
        (root / "CLAUDE.md").write_text("# project rules", "utf-8")
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={},
            cwd=leaf,
        )
        self.assertEqual(decision.source, f"{SOURCE_MARKER_PREFIX}CLAUDE.md")
        self.assertEqual(decision.path, root.resolve())

    # ------------------------------------------------------------------
    # Layer 6: 最终 fallback
    # ------------------------------------------------------------------

    def test_layer6_fallback_cwd(self) -> None:
        """所有 marker 都找不到 → fallback 到 cwd，行为等价于今天。"""
        isolated = self.tmp / "isolated"
        isolated.mkdir()
        # 注意：不要在 self.tmp 或它的祖先放任何 marker。
        # 由于 tmp 自己可能在 /private/var/folders/... 路径下，理论上不会有
        # MARKERS_BY_AUTHORITY 里的任何文件，但我们仍要确认 resolver 不会
        # 把祖先目录里偶然存在的 marker 当作结果。
        decision = resolve_project_root(
            caller_param=None,
            workflow=None,
            env={},
            cwd=isolated,
        )
        # 接受两种正常结果：fallback_cwd（理想），或在某些系统上祖先有 marker
        # 时退到 marker。我们至少要保证不抛异常、不返回 None。
        self.assertIsInstance(decision, ProjectRootDecision)
        self.assertTrue(
            decision.source == SOURCE_FALLBACK_CWD
            or decision.source.startswith(SOURCE_MARKER_PREFIX)
        )

    # ------------------------------------------------------------------
    # 行为不变性：不传任何参数也不应该抛
    # ------------------------------------------------------------------

    def test_no_params_returns_valid_decision(self) -> None:
        """resolve_project_root() 不传任何参数 → 走 os.environ + Path.cwd()，必须返回有效 Decision。"""
        decision = resolve_project_root()
        self.assertIsInstance(decision, ProjectRootDecision)
        self.assertIsInstance(decision.path, Path)
        self.assertTrue(decision.source)  # 非空字符串

    # ------------------------------------------------------------------
    # MARKERS_BY_AUTHORITY 顺序保护测试 — .git 必须排第一
    # ------------------------------------------------------------------

    def test_git_marker_first_in_authority_order(self) -> None:
        """权威性顺序的 invariant：.git 必须是第一个，否则单 repo 误判风险高。"""
        self.assertEqual(MARKERS_BY_AUTHORITY[0], ".git")


if __name__ == "__main__":
    unittest.main()
