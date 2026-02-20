#!/usr/bin/env python3
"""Hook 增强功能的单元测试：stop status 放宽、sessionEnd 兜底检测、load 日志增强"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, run_script, SCRIPTS_DIR  # noqa: E402

sys.path.insert(0, str(SCRIPTS_DIR))

from service.config import SESSIONS_FILE
from service.hooks.audit_response import detect_signals
from service.hooks.audit_tool_use import should_skip, detect_tool_action
from service.hooks.audit_thought import detect_thought_signals
from core.utils import today_str, iso_now


class TestStopHookStatusFilter(IsolatedWorkspaceCase):
    """验证 stop Hook 放宽 status 过滤：completed 和 aborted 都应触发"""

    def _run_stop_hook(self, status):
        event = {
            "status": status,
            "conversation_id": "test-conv-123",
            "workspace_roots": [self.workspace],
        }
        return run_script(
            "service/hooks/prompt_session_save.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )

    def test_completed_triggers_save(self):
        result = self._run_stop_hook("completed")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("followup_message", output)
        self.assertIn("[Session Save]", output["followup_message"])

    def test_aborted_triggers_save(self):
        result = self._run_stop_hook("aborted")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("followup_message", output)
        self.assertIn("[Session Save]", output["followup_message"])

    def test_error_does_not_trigger(self):
        result = self._run_stop_hook("error")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("followup_message", output)

    def test_empty_status_does_not_trigger(self):
        result = self._run_stop_hook("")
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("followup_message", output)


class TestSessionSaveTemplate(IsolatedWorkspaceCase):
    """验证 Session Save 模板包含逐条提取事实的指令"""

    def test_template_requires_fact_extraction(self):
        event = {
            "status": "completed",
            "conversation_id": "test-conv-456",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/prompt_session_save.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        output = json.loads(result.stdout)
        msg = output["followup_message"]
        self.assertIn("逐条提取关键事实", msg)
        self.assertIn("必须执行", msg)
        self.assertIn("save_fact", msg)


class TestSessionEndSummaryCheck(IsolatedWorkspaceCase):
    """验证 sessionEnd 兜底检测：未保存摘要时写入 warning"""

    def test_warning_when_no_summary(self):
        event = {
            "conversation_id": "test-conv-no-summary",
            "reason": "completed",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/sync_and_cleanup.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = []
            for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    entries.append(json.loads(line))
            warnings = [e for e in entries if e.get("type") == "warning"]
            self.assertTrue(len(warnings) > 0, "Should have warning entry for missing summary")
            self.assertIn("未保存摘要", warnings[0]["content"])

    def test_no_warning_when_summary_exists(self):
        sessions_path = self.memory_dir / SESSIONS_FILE
        summary = {
            "id": "sum-test",
            "session_id": "test-conv-with-summary",
            "topic": "测试会话",
            "summary": "测试摘要",
            "timestamp": iso_now(),
        }
        sessions_path.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")

        event = {
            "conversation_id": "test-conv-with-summary",
            "reason": "completed",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/sync_and_cleanup.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = []
            for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    entries.append(json.loads(line))
            warnings = [e for e in entries if e.get("type") == "warning"]
            self.assertEqual(len(warnings), 0, "Should have no warning when summary exists")


class TestAuditResponseSignalDetection(unittest.TestCase):
    """验证 afterAgentResponse 的信号检测逻辑"""

    def test_detects_memory_claim(self):
        signals = detect_signals("关于测试目录的原则，我记下来了，继续处理下一个任务。")
        types = [s["type"] for s in signals]
        self.assertIn("memory_claim", types)

    def test_detects_principle(self):
        signals = detect_signals("这个规范是：测试文件必须放在 tests/ 目录下。")
        types = [s["type"] for s in signals]
        self.assertIn("principle", types)

    def test_detects_decision(self):
        signals = detect_signals("经过讨论，我们决定使用 PostgreSQL 作为主数据库。")
        types = [s["type"] for s in signals]
        self.assertIn("decision", types)

    def test_detects_important_marker(self):
        signals = detect_signals("重要：这个配置不能修改，否则会导致生产事故。")
        types = [s["type"] for s in signals]
        self.assertIn("important_marker", types)

    def test_detects_commit_action(self):
        signals = detect_signals("已 commit 并 push 完成。")
        types = [s["type"] for s in signals]
        self.assertIn("commit_action", types)

    def test_no_signal_in_normal_text(self):
        signals = detect_signals("这是一段普通的代码说明文本，没有任何特殊信号。")
        self.assertEqual(len(signals), 0)

    def test_multiple_signals(self):
        signals = detect_signals("我记下来了这个规范，已经 commit push 完成。")
        types = [s["type"] for s in signals]
        self.assertIn("memory_claim", types)
        self.assertIn("principle", types)
        self.assertIn("commit_action", types)


class TestAuditResponseHook(IsolatedWorkspaceCase):
    """验证 afterAgentResponse Hook 脚本的完整执行"""

    def test_writes_audit_entry_on_signal(self):
        event = {
            "text": "关于测试目录的原则，我记下来了。",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/audit_response.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        self.assertTrue(daily_file.exists())
        entries = []
        for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
            if line:
                entries.append(json.loads(line))
        audits = [e for e in entries if e.get("type") == "audit"]
        self.assertTrue(len(audits) > 0)
        self.assertIn("memory_claim", audits[0]["signals"])

    def test_no_audit_on_normal_text(self):
        event = {
            "text": "这是一段普通的回复文本。",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/audit_response.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = []
            for line in daily_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    entries.append(json.loads(line))
            audits = [e for e in entries if e.get("type") == "audit"]
            self.assertEqual(len(audits), 0)

    def test_empty_text_skips(self):
        event = {"text": "", "workspace_roots": [self.workspace]}
        result = run_script(
            "service/hooks/audit_response.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output, {})


class TestToolUseSkipPatterns(unittest.TestCase):
    """验证 postToolUse 的命令跳过逻辑"""

    def test_skips_save_fact(self):
        self.assertTrue(should_skip("python3 /path/to/save_fact.py --content test"))

    def test_skips_save_summary(self):
        self.assertTrue(should_skip("python3 save_summary.py --topic test"))

    def test_skips_distill(self):
        self.assertTrue(should_skip("python3 distill_to_memory.py"))

    def test_does_not_skip_git(self):
        self.assertFalse(should_skip("git commit -m 'test'"))

    def test_does_not_skip_npm(self):
        self.assertFalse(should_skip("npm install express"))


class TestToolUseActionDetection(unittest.TestCase):
    """验证 postToolUse 的操作检测逻辑"""

    def test_detects_git_commit(self):
        action, extracted = detect_tool_action(
            "git commit -m 'fix bug'",
            "[main abc1234] fix bug\n 1 file changed",
        )
        self.assertEqual(action, "git_commit")
        self.assertIsNotNone(extracted)

    def test_detects_git_push(self):
        action, _ = detect_tool_action("git push origin main", "")
        self.assertEqual(action, "git_push")

    def test_detects_npm_install(self):
        action, _ = detect_tool_action("npm install express", "added 50 packages")
        self.assertEqual(action, "dependency_install")

    def test_ignores_normal_command(self):
        action, _ = detect_tool_action("ls -la", "total 100\n...")
        self.assertIsNone(action)


class TestToolUseHook(IsolatedWorkspaceCase):
    """验证 postToolUse Hook 脚本的完整执行"""

    def test_records_git_commit(self):
        event = {
            "tool_name": "Shell",
            "tool_input": {"command": "git commit -m 'test commit'"},
            "tool_output": "[main abc1234] test commit\n 1 file changed",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/audit_tool_use.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]
            audits = [e for e in entries if e.get("type") == "audit" and e.get("action") == "git_commit"]
            self.assertTrue(len(audits) > 0)

    def test_skips_non_shell_tool(self):
        event = {
            "tool_name": "Read",
            "tool_input": {"path": "/some/file"},
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/audit_tool_use.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output, {})


class TestThoughtSignalDetection(unittest.TestCase):
    """验证 afterAgentThought 的信号检测逻辑"""

    def test_detects_intent_to_remember(self):
        signals = detect_thought_signals("这个信息需要记住，后续会用到。")
        types = [s["type"] for s in signals]
        self.assertIn("intent_to_remember", types)

    def test_detects_user_preference(self):
        signals = detect_thought_signals("用户偏好使用 TypeScript 而不是 JavaScript。")
        types = [s["type"] for s in signals]
        self.assertIn("user_preference", types)

    def test_detects_architecture_decision(self):
        signals = detect_thought_signals("这是一个架构决策，需要使用微服务模式。")
        types = [s["type"] for s in signals]
        self.assertIn("architecture_decision", types)

    def test_detects_principle(self):
        signals = detect_thought_signals("用户明确了这个规范，测试文件的位置有要求。")
        types = [s["type"] for s in signals]
        self.assertIn("principle", types)

    def test_no_signal_in_normal_thought(self):
        signals = detect_thought_signals("让我分析一下这段代码的逻辑，看看是否有 bug。")
        self.assertEqual(len(signals), 0)

    def test_skips_short_text(self):
        signals = detect_thought_signals("短文本")
        self.assertEqual(len(signals), 0)


class TestThoughtHook(IsolatedWorkspaceCase):
    """验证 afterAgentThought Hook 脚本的完整执行"""

    def test_records_thought_signal(self):
        event = {
            "text": "这个信息需要记住，用户偏好使用中文回答，这是一个重要的架构决策。",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/audit_thought.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        if daily_file.exists():
            entries = [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]
            audits = [e for e in entries if e.get("type") == "audit" and e.get("source") == "thought"]
            self.assertTrue(len(audits) > 0)

    def test_skips_normal_thought(self):
        event = {
            "text": "让我分析一下这段代码的逻辑，看看是否有 bug，然后修复它。",
            "workspace_roots": [self.workspace],
        }
        result = run_script(
            "service/hooks/audit_thought.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )
        self.assertEqual(result.returncode, 0)


class TestFlushMemoryTemplate(IsolatedWorkspaceCase):
    """验证 preCompact Hook 生成的 [Memory Flush] 提示词"""

    def _run_flush_hook(self, event):
        return run_script(
            "service/hooks/flush_memory.py",
            self.workspace,
            stdin_data=json.dumps(event),
        )

    def test_generates_flush_prompt(self):
        event = {
            "context_usage_percent": 85,
            "message_count": 42,
            "conversation_id": "conv-flush-001",
            "workspace_roots": [self.workspace],
        }
        result = self._run_flush_hook(event)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("user_message", output)
        msg = output["user_message"]
        self.assertIn("[Memory Flush]", msg)
        self.assertIn("85", msg)
        self.assertIn("42", msg)
        self.assertIn("save_fact", msg)

    def test_includes_save_fact_command(self):
        event = {
            "context_usage_percent": 90,
            "message_count": 10,
            "conversation_id": "conv-flush-002",
            "workspace_roots": [self.workspace],
        }
        result = self._run_flush_hook(event)
        output = json.loads(result.stdout)
        msg = output["user_message"]
        self.assertIn("save_fact.py", msg)
        self.assertIn("--content", msg)
        self.assertIn("--type", msg)

    def test_disabled_memory_returns_empty(self):
        disable_dir = Path(self.workspace) / ".cursor" / "skills"
        disable_dir.mkdir(parents=True, exist_ok=True)
        (disable_dir / ".memory-disable").touch()

        event = {
            "context_usage_percent": 85,
            "message_count": 42,
            "conversation_id": "conv-disabled",
            "workspace_roots": [self.workspace],
        }
        result = self._run_flush_hook(event)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("user_message", output)

    def test_handles_missing_fields_gracefully(self):
        event = {"workspace_roots": [self.workspace]}
        result = self._run_flush_hook(event)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertIn("user_message", output)
        self.assertIn("[Memory Flush]", output["user_message"])


class TestAuditResponseEdgeCases(unittest.TestCase):
    """audit_response 信号检测的边界情况"""

    def test_empty_string(self):
        self.assertEqual(detect_signals(""), [])

    def test_very_long_text(self):
        text = "普通文本" * 1000 + "我记下来了" + "普通文本" * 1000
        signals = detect_signals(text)
        types = [s["type"] for s in signals]
        self.assertIn("memory_claim", types)

    def test_matches_limited_to_three(self):
        text = "记下来了 记下来了 记下来了 记下来了 记下来了"
        signals = detect_signals(text)
        for s in signals:
            self.assertLessEqual(len(s["matches"]), 3)

    def test_chinese_colon_variant(self):
        signals = detect_signals("重要：这是关键信息")
        types = [s["type"] for s in signals]
        self.assertIn("important_marker", types)

    def test_english_colon_variant(self):
        signals = detect_signals("重要:这是关键信息")
        types = [s["type"] for s in signals]
        self.assertIn("important_marker", types)


class TestToolUseEdgeCases(unittest.TestCase):
    """audit_tool_use 的边界情况"""

    def test_skips_sync_index(self):
        self.assertTrue(should_skip("python3 sync_index.py --project-path /tmp"))

    def test_skips_userinput(self):
        self.assertTrue(should_skip("tt userinput.py"))

    def test_detects_pip_install(self):
        action, _ = detect_tool_action("pip install requests", "Successfully installed requests-2.28.0")
        self.assertEqual(action, "dependency_install")

    def test_detects_yarn_install(self):
        action, _ = detect_tool_action("yarn install", "")
        self.assertEqual(action, "dependency_install")

    def test_empty_command(self):
        action, _ = detect_tool_action("", "")
        self.assertIsNone(action)

    def test_git_commit_extracts_hash(self):
        action, extracted = detect_tool_action(
            "git commit -m 'add feature'",
            "[main abc1234] add feature\n 3 files changed",
        )
        self.assertEqual(action, "git_commit")
        self.assertIsNotNone(extracted)
        self.assertIn("abc1234", extracted)


class TestThoughtSignalEdgeCases(unittest.TestCase):
    """audit_thought 信号检测的边界情况"""

    def test_empty_string(self):
        self.assertEqual(detect_thought_signals(""), [])

    def test_exactly_20_chars(self):
        text = "a" * 20
        self.assertEqual(detect_thought_signals(text), [])

    def test_detects_key_finding(self):
        signals = detect_thought_signals("这是一个关键发现，我们需要重新考虑整个方案的设计。")
        types = [s["type"] for s in signals]
        self.assertIn("key_finding", types)

    def test_multiple_thought_signals(self):
        text = "用户偏好使用 Python，这是一个架构决策，需要记住这个关键发现。"
        signals = detect_thought_signals(text)
        types = [s["type"] for s in signals]
        self.assertTrue(len(types) >= 2)


if __name__ == "__main__":
    unittest.main()
