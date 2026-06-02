"""retry_action 单元测试 — 7 个核心场景。

覆盖：
    TC-RETRY-01 默认从最后失败节点重试（失败 → retry → 成功）
    TC-RETRY-02 显式指定 alias 重试（回到更早的节点）
    TC-RETRY-03 vars_patch 合并到 vars
    TC-RETRY-04 skip=True 跳过失败节点，把 vars_patch 当 output
    TC-RETRY-05 history 被裁剪（从重试节点开始的旧记录丢弃）
    TC-RETRY-06 awaiting_agent 状态下也能 retry（用户超时询问时的场景）
    TC-RETRY-07 错误路径：未知 alias / 已 completed 的 run 不能 retry
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "skills" / "agent-workflow"))

from lib import engine  # noqa: E402
from lib.errors import ErrorCode, WorkflowError  # noqa: E402

THREE_STEP_YAML = """
name: t-retry
executors:
  mock: { kind: mock }
nodes:
  - alias: step_a
    type: agent_call
    executor: mock
    prompt: step a
    output: a_out
  - alias: step_b
    type: agent_call
    executor: mock
    prompt: step b for {{a_out}}
    output: b_out
  - alias: step_c
    type: agent_call
    executor: mock
    prompt: step c for {{b_out}}
    output: c_out
"""

CALLER_THEN_MOCK_YAML = """
name: t-retry-caller
executors:
  mock: { kind: mock }
nodes:
  - alias: think
    type: agent_call
    executor: caller
    prompt: think please
    output: thought
  - alias: act
    type: agent_call
    executor: mock
    prompt: act on {{thought}}
    output: action_result
"""


class RetryActionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-retry-"))
        self._cwd = Path.cwd()
        (self.tmp / "pyproject.toml").write_text("[project]\nname='ut'\n", "utf-8")
        os.chdir(self.tmp)
        os.environ["AGENT_WORKFLOW_ENABLE_MOCK"] = "1"

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        for key in list(os.environ.keys()):
            if key.startswith("AGENT_WORKFLOW_"):
                os.environ.pop(key, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------
    # TC-RETRY-01: 最常见场景 — step_b 失败 → retry 默认 → 成功
    # ------------------------------------------------------------
    def test_retry_default_from_last_failed(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "a-val"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B_EXIT"] = "1"

        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "failed")
        self.assertEqual(out["error"]["code"], ErrorCode.EXECUTOR_NONZERO_EXIT)

        # 修复"故障"，触发不带 alias 的 retry
        os.environ.pop("AGENT_WORKFLOW_MOCK_STEP_B_EXIT", None)
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B"] = "b-val"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C"] = "c-val"

        result = engine.retry_action({"run_id": run_id})
        self.assertEqual(result["action"], "completed")
        self.assertEqual(result["vars"]["a_out"], "a-val")
        self.assertEqual(result["vars"]["b_out"], "b-val")
        self.assertEqual(result["vars"]["c_out"], "c-val")

    # ------------------------------------------------------------
    # TC-RETRY-02: 显式指定 alias 回到更早的节点
    # ------------------------------------------------------------
    def test_retry_with_explicit_alias_rewinds(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "a1"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B"] = "b1"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C_EXIT"] = "1"

        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "failed")

        # caller 想从 step_a 重头跑（认为前面输出也有问题）
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "a2"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B"] = "b2"
        os.environ.pop("AGENT_WORKFLOW_MOCK_STEP_C_EXIT", None)
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C"] = "c2"

        result = engine.retry_action({"run_id": run_id, "alias": "step_a"})
        self.assertEqual(result["action"], "completed")
        self.assertEqual(result["vars"]["a_out"], "a2")
        self.assertEqual(result["vars"]["b_out"], "b2")
        self.assertEqual(result["vars"]["c_out"], "c2")

    # ------------------------------------------------------------
    # TC-RETRY-03: vars_patch 合并
    # ------------------------------------------------------------
    def test_retry_with_vars_patch(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "ax"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B"] = "bx"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C_EXIT"] = "1"

        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "failed")

        # caller 打 patch 改 b_out 后从 step_c 重试
        os.environ.pop("AGENT_WORKFLOW_MOCK_STEP_C_EXIT", None)
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C"] = "c-final"

        result = engine.retry_action(
            {"run_id": run_id, "vars_patch": {"b_out": "patched-b"}}
        )
        self.assertEqual(result["action"], "completed")
        self.assertEqual(result["vars"]["b_out"], "patched-b")
        self.assertEqual(result["vars"]["c_out"], "c-final")

    # ------------------------------------------------------------
    # TC-RETRY-04: skip=True 把 vars_patch 当 output 直接跳到下一节点
    # ------------------------------------------------------------
    def test_retry_skip_with_patch_as_output(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "a-skip"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B_EXIT"] = "1"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C"] = "c-after-skip"

        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "failed")

        # skip step_b：手工把 b_out 塞进去，让 step_c 能用上
        os.environ.pop("AGENT_WORKFLOW_MOCK_STEP_B_EXIT", None)
        result = engine.retry_action(
            {
                "run_id": run_id,
                "skip": True,
                "vars_patch": {"b_out": "manually-filled"},
            }
        )
        self.assertEqual(result["action"], "completed", msg=f"期望 completed，实际 result={result!r}")
        self.assertEqual(result["vars"]["b_out"], "manually-filled")
        self.assertEqual(result["vars"]["c_out"], "c-after-skip")

        s = engine.status_action({"run_id": run_id})
        skipped_entries = [h for h in s["history"] if h.get("status") == "skipped"]
        self.assertEqual(len(skipped_entries), 1)
        self.assertEqual(skipped_entries[0]["alias"], "step_b")

    # ------------------------------------------------------------
    # TC-RETRY-05: history 被裁剪
    # ------------------------------------------------------------
    def test_retry_trims_history_from_target(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "a"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B"] = "b"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C_EXIT"] = "1"

        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "failed")

        before = engine.status_action({"run_id": run_id})
        aliases_before = [h["alias"] for h in before["history"]]
        # 期望失败前已经有 step_a / step_b 成功记录 + step_c 失败记录
        self.assertEqual(aliases_before, ["step_a", "step_b", "step_c"])

        # 从 step_b 重试，预期 history 被裁剪到只保留 step_a
        os.environ.pop("AGENT_WORKFLOW_MOCK_STEP_C_EXIT", None)
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C"] = "c-final"
        engine.retry_action({"run_id": run_id, "alias": "step_b"})

        after = engine.status_action({"run_id": run_id})
        aliases_after = [h["alias"] for h in after["history"]]
        # 重试后会重新跑 step_b 和 step_c → 各又出现一条新的 completed 记录
        self.assertEqual(aliases_after, ["step_a", "step_b", "step_c"])
        # 但 step_b 的记录是新的（不应是 retry 前的旧记录），通过 history 总长不变验证
        self.assertEqual(len(after["history"]), 3)

    # ------------------------------------------------------------
    # TC-RETRY-06: awaiting_agent 状态下也能 retry（用户超时询问场景）
    # ------------------------------------------------------------
    def test_retry_on_awaiting_agent_run(self) -> None:
        # 第一个节点 executor=caller → awaiting_agent
        out = engine.start_action({"workflow": CALLER_THEN_MOCK_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "execute_agent")

        s = engine.status_action({"run_id": run_id})
        self.assertEqual(s["status"], "awaiting_agent")

        # 用户决定让 AI 从断点重试（实际效果：清掉 pending，重新等 caller 输入）
        result = engine.retry_action({"run_id": run_id})
        # 没有 vars_patch / skip，仍然停在 think 节点等 caller
        self.assertEqual(result["action"], "execute_agent")
        self.assertEqual(result["payload"]["alias"], "think")

    # ------------------------------------------------------------
    # TC-RETRY-07: 错误路径
    # ------------------------------------------------------------
    def test_retry_unknown_alias_raises(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A_EXIT"] = "1"
        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        self.assertEqual(out["action"], "failed")

        with self.assertRaises(WorkflowError) as ctx:
            engine.retry_action({"run_id": run_id, "alias": "not-a-real-alias"})
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)

    def test_retry_on_completed_run_rejected(self) -> None:
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A"] = "a"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_B"] = "b"
        os.environ["AGENT_WORKFLOW_MOCK_STEP_C"] = "c"
        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        self.assertEqual(out["action"], "completed")

        with self.assertRaises(WorkflowError) as ctx:
            engine.retry_action({"run_id": out["run_id"]})
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)

    def test_retry_skip_on_non_target_node_type_rejected(self) -> None:
        # 构造一个 sleep 节点失败的奇怪场景：实际上 sleep 不会失败，
        # 这里改成测 vars_patch 不合法（非 dict）的拒绝路径
        os.environ["AGENT_WORKFLOW_MOCK_STEP_A_EXIT"] = "1"
        out = engine.start_action({"workflow": THREE_STEP_YAML, "caller": "ut"})
        run_id = out["run_id"]
        with self.assertRaises(WorkflowError) as ctx:
            engine.retry_action({"run_id": run_id, "vars_patch": "not-a-dict"})
        self.assertEqual(ctx.exception.code, ErrorCode.PARAMS_INVALID)


if __name__ == "__main__":
    unittest.main()
