#!/usr/bin/env python3
"""Session Save 优化 E2 方案集成测试：覆盖各层联动和新增功能。"""
import json
import os
import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, run_script, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.config import SESSIONS_FILE
from core.utils import iso_now, today_str, ts_id, utcnow


class TestSaveFactTypeS(IsolatedWorkspaceCase):
    """save_fact.py 增加 S 类型 + 会话状态更新"""

    def test_save_fact_with_type_s(self):
        proc = run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--content", "阶段摘要：讨论了 API 重构方案",
                "--type", "S",
                "--entities", "session",
                "--confidence", "1.0",
                "--session", "test-conv-001",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        self.assertTrue(daily_file.exists())
        entry = json.loads(daily_file.read_text(encoding="utf-8").strip().split("\n")[-1])
        self.assertEqual(entry["memory_type"], "S")
        self.assertEqual(entry["type"], "fact")

    def test_save_fact_updates_session_state(self):
        run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--content", "技术决策",
                "--type", "W",
                "--session", "test-conv-002",
            ],
        )

        state_path = self.memory_dir / "session_state" / "test-conv-002.json"
        self.assertTrue(state_path.exists())
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["fact_count"], 1)

    def test_save_fact_type_s_updates_stage_count(self):
        run_script(
            "service/memory/save_fact.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--content", "阶段摘要：Phase1 完成",
                "--type", "S",
                "--session", "test-conv-003",
            ],
        )

        state_path = self.memory_dir / "session_state" / "test-conv-003.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state.get("stage_summary_count"), 1)
        self.assertEqual(state.get("fact_count", 0), 0)


class TestSaveSummaryE2(IsolatedWorkspaceCase):
    """save_summary.py 增加 --source + 幂等控制"""

    def test_save_summary_with_source(self):
        proc = run_script(
            "service/memory/save_summary.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--topic", "API 重构",
                "--summary", "决定使用 RESTful API",
                "--source", "layer1_rules",
                "--session", "sum-conv-001",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")

        sessions_path = self.memory_dir / "sessions.jsonl"
        entry = json.loads(sessions_path.read_text(encoding="utf-8").strip().split("\n")[-1])
        self.assertEqual(entry["source"], "layer1_rules")

    def test_save_summary_idempotent(self):
        args = [
            "--project-path", self.workspace,
            "--topic", "幂等测试",
            "--summary", "同一会话不重复保存",
            "--session", "sum-conv-002",
        ]
        proc1 = run_script("service/memory/save_summary.py", self.workspace, args=args)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        out1 = json.loads(proc1.stdout)
        self.assertEqual(out1["status"], "ok")

        proc2 = run_script("service/memory/save_summary.py", self.workspace, args=args)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        out2 = json.loads(proc2.stdout)
        self.assertEqual(out2["status"], "skipped")

        sessions_path = self.memory_dir / "sessions.jsonl"
        lines = [l for l in sessions_path.read_text(encoding="utf-8").strip().split("\n") if l]
        self.assertEqual(len(lines), 1)

    def test_save_summary_without_session_still_works(self):
        proc = run_script(
            "service/memory/save_summary.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--topic", "无 session",
                "--summary", "手动保存",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["status"], "ok")

    def test_save_summary_layer4_stop_source(self):
        proc = run_script(
            "service/memory/save_summary.py",
            self.workspace,
            args=[
                "--project-path", self.workspace,
                "--topic", "兜底保存",
                "--summary", "通过 stop hook 保存",
                "--source", "layer4_stop",
                "--session", "sum-conv-003",
            ],
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        sessions_path = self.memory_dir / "sessions.jsonl"
        entry = json.loads(sessions_path.read_text(encoding="utf-8").strip())
        self.assertEqual(entry["source"], "layer4_stop")


class TestHasSessionData(IsolatedWorkspaceCase):
    """prompt_session_save.py 的 has_session_data 测试"""

    def test_returns_false_when_no_data(self):
        from service.hooks.prompt_session_save import has_session_data
        self.assertFalse(has_session_data(str(self.memory_dir), "no-data-conv"))

    def test_returns_true_when_summary_saved_in_state(self):
        from service.hooks.prompt_session_save import has_session_data
        from service.memory.session_state import mark_summary_saved

        mark_summary_saved(str(self.memory_dir), "has-summary-conv", "layer1_rules")
        self.assertTrue(has_session_data(str(self.memory_dir), "has-summary-conv"))

    def test_returns_true_when_facts_exist_in_state(self):
        from service.hooks.prompt_session_save import has_session_data
        from service.memory.session_state import update_fact_count

        update_fact_count(str(self.memory_dir), "has-fact-conv", "W")
        self.assertTrue(has_session_data(str(self.memory_dir), "has-fact-conv"))

    def test_returns_true_when_facts_in_daily(self):
        from service.hooks.prompt_session_save import has_session_data

        daily_dir = self.memory_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{today_str()}.jsonl"
        entry = {
            "id": "log-test",
            "type": "fact",
            "content": "测试事实",
            "source": {"session": "daily-fact-conv"},
            "timestamp": iso_now(),
        }
        daily_file.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

        self.assertTrue(has_session_data(str(self.memory_dir), "daily-fact-conv"))

    def test_returns_false_for_different_session_facts(self):
        from service.hooks.prompt_session_save import has_session_data

        daily_dir = self.memory_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{today_str()}.jsonl"
        entry = {
            "id": "log-other",
            "type": "fact",
            "content": "其他会话事实",
            "source": {"session": "other-conv"},
            "timestamp": iso_now(),
        }
        daily_file.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

        self.assertFalse(has_session_data(str(self.memory_dir), "my-conv"))


class TestFlushMemoryStageTemplate(IsolatedWorkspaceCase):
    """flush_memory.py 模板包含阶段摘要要求"""

    def test_flush_template_contains_type_s(self):
        from service.hooks.flush_memory import FLUSH_TEMPLATE
        self.assertIn("--type S", FLUSH_TEMPLATE)
        self.assertIn("阶段摘要", FLUSH_TEMPLATE)


class TestAutoGenerateSummary(IsolatedWorkspaceCase):
    """sync_and_cleanup.py 的 auto_generate_summary 测试"""

    def test_generates_summary_from_facts(self):
        from service.hooks.sync_and_cleanup import auto_generate_summary

        daily_dir = self.memory_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{today_str()}.jsonl"
        facts = [
            {"id": "f1", "type": "fact", "content": "决定使用 PostgreSQL",
             "source": {"session": "auto-conv"}, "timestamp": iso_now()},
            {"id": "f2", "type": "fact", "content": "配置了 CI/CD 流水线",
             "source": {"session": "auto-conv"}, "timestamp": iso_now()},
        ]
        with open(daily_file, "w", encoding="utf-8") as f:
            for fact in facts:
                f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        event = {"conversation_id": "auto-conv"}
        auto_generate_summary(str(self.memory_dir), event)

        sessions_path = self.memory_dir / "sessions.jsonl"
        self.assertTrue(sessions_path.exists())
        entry = json.loads(sessions_path.read_text(encoding="utf-8").strip())
        self.assertEqual(entry["source"], "layer3_auto")
        self.assertTrue(entry["auto_generated"])
        self.assertIn("PostgreSQL", entry["summary"])

    def test_skips_when_summary_already_saved(self):
        from service.hooks.sync_and_cleanup import auto_generate_summary
        from service.memory.session_state import mark_summary_saved

        mark_summary_saved(str(self.memory_dir), "already-saved-conv", "layer1_rules")

        event = {"conversation_id": "already-saved-conv"}
        auto_generate_summary(str(self.memory_dir), event)

        sessions_path = self.memory_dir / "sessions.jsonl"
        self.assertFalse(sessions_path.exists())

    def test_skips_when_no_facts(self):
        from service.hooks.sync_and_cleanup import auto_generate_summary

        event = {"conversation_id": "empty-conv"}
        auto_generate_summary(str(self.memory_dir), event)

        sessions_path = self.memory_dir / "sessions.jsonl"
        self.assertFalse(sessions_path.exists())

    def test_generates_from_stage_summaries(self):
        from service.hooks.sync_and_cleanup import auto_generate_summary

        daily_dir = self.memory_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{today_str()}.jsonl"
        entries = [
            {"id": "s1", "type": "fact", "memory_type": "S",
             "content": "阶段摘要：完成 API 设计",
             "source": {"session": "stage-conv"}, "timestamp": iso_now()},
            {"id": "s2", "type": "fact", "memory_type": "S",
             "content": "阶段摘要：实现数据层",
             "source": {"session": "stage-conv"}, "timestamp": iso_now()},
        ]
        with open(daily_file, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

        auto_generate_summary(str(self.memory_dir), {"conversation_id": "stage-conv"})

        sessions_path = self.memory_dir / "sessions.jsonl"
        entry = json.loads(sessions_path.read_text(encoding="utf-8").strip())
        self.assertIn("→", entry["summary"])


class TestTruncateSessions(IsolatedWorkspaceCase):
    """sync_and_cleanup.py 的 truncate_sessions 测试"""

    def test_truncates_when_over_limit(self):
        from service.hooks.sync_and_cleanup import truncate_sessions

        sessions_path = self.memory_dir / "sessions.jsonl"
        with open(sessions_path, "w", encoding="utf-8") as f:
            for i in range(20):
                entry = {"id": f"sum-{i}", "topic": f"话题{i}", "timestamp": iso_now()}
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        truncate_sessions(str(self.memory_dir), keep_last=10)

        from storage.jsonl import read_jsonl
        entries = read_jsonl(str(sessions_path))
        self.assertEqual(len(entries), 10)
        self.assertEqual(entries[0]["id"], "sum-10")
        self.assertEqual(entries[-1]["id"], "sum-19")

    def test_noop_when_under_limit(self):
        from service.hooks.sync_and_cleanup import truncate_sessions

        sessions_path = self.memory_dir / "sessions.jsonl"
        with open(sessions_path, "w", encoding="utf-8") as f:
            for i in range(5):
                entry = {"id": f"sum-{i}", "topic": f"话题{i}", "timestamp": iso_now()}
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        truncate_sessions(str(self.memory_dir), keep_last=10)

        from storage.jsonl import read_jsonl
        entries = read_jsonl(str(sessions_path))
        self.assertEqual(len(entries), 5)

    def test_noop_when_no_file(self):
        from service.hooks.sync_and_cleanup import truncate_sessions
        truncate_sessions(str(self.memory_dir), keep_last=10)


class TestCleanOldSessionStates(IsolatedWorkspaceCase):
    """sync_and_cleanup.py 的 clean_old_session_states 测试"""

    def test_removes_old_state_files(self):
        from service.hooks.sync_and_cleanup import clean_old_session_states

        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)

        old_time = (utcnow() - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        (state_dir / "old-session.json").write_text(
            json.dumps({"session_id": "old", "created_at": old_time}),
            encoding="utf-8",
        )

        recent_time = iso_now()
        (state_dir / "recent-session.json").write_text(
            json.dumps({"session_id": "recent", "created_at": recent_time}),
            encoding="utf-8",
        )

        clean_old_session_states(str(self.memory_dir), retain_days=7)

        self.assertFalse((state_dir / "old-session.json").exists())
        self.assertTrue((state_dir / "recent-session.json").exists())

    def test_noop_when_no_state_dir(self):
        from service.hooks.sync_and_cleanup import clean_old_session_states
        clean_old_session_states(str(self.memory_dir), retain_days=7)

    def test_ignores_non_json_files(self):
        from service.hooks.sync_and_cleanup import clean_old_session_states

        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / ".some-lock.lock").write_text("lock", encoding="utf-8")

        clean_old_session_states(str(self.memory_dir), retain_days=7)
        self.assertTrue((state_dir / ".some-lock.lock").exists())


class TestLogSessionMetrics(IsolatedWorkspaceCase):
    """sync_and_cleanup.py 的 log_session_metrics 测试"""

    def test_writes_metrics_entry(self):
        from service.hooks.sync_and_cleanup import log_session_metrics
        from service.memory.session_state import mark_summary_saved, update_fact_count

        sid = "metrics-conv-001"
        update_fact_count(str(self.memory_dir), sid, "W")
        update_fact_count(str(self.memory_dir), sid, "W")
        update_fact_count(str(self.memory_dir), sid, "S")
        mark_summary_saved(str(self.memory_dir), sid, "layer1_rules")

        log_session_metrics(str(self.memory_dir), {"conversation_id": sid})

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        entries = [json.loads(l) for l in daily_file.read_text(encoding="utf-8").strip().split("\n") if l]
        metrics = [e for e in entries if e.get("type") == "session_metrics"]
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0]["summary_source"], "layer1_rules")
        self.assertEqual(metrics[0]["fact_count"], 2)
        self.assertEqual(metrics[0]["stage_summary_count"], 1)
        self.assertTrue(metrics[0]["summary_saved"])

    def test_noop_when_no_state(self):
        from service.hooks.sync_and_cleanup import log_session_metrics

        log_session_metrics(str(self.memory_dir), {"conversation_id": "no-state-conv"})

        daily_file = self.memory_dir / "daily" / f"{today_str()}.jsonl"
        self.assertFalse(daily_file.exists())


class TestLoadMemoryFilterS(IsolatedWorkspaceCase):
    """load_memory.py 过滤 S 类型"""

    def test_excludes_stage_summaries_from_context(self):
        from service.hooks.load_memory import load_context

        daily_dir = self.memory_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{today_str()}.jsonl"
        entries = [
            {"id": "f1", "type": "fact", "memory_type": "W",
             "content": "使用 PostgreSQL", "timestamp": iso_now(), "confidence": 0.9},
            {"id": "f2", "type": "fact", "memory_type": "S",
             "content": "阶段摘要：完成了 API 设计", "timestamp": iso_now(), "confidence": 1.0},
            {"id": "f3", "type": "fact", "memory_type": "O",
             "content": "用户偏好 TypeScript", "timestamp": iso_now(), "confidence": 0.9},
        ]
        with open(daily_file, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

        context = load_context(self.workspace)
        self.assertIn("PostgreSQL", context)
        self.assertIn("TypeScript", context)
        self.assertNotIn("阶段摘要", context)


class TestDistillExcludeS(IsolatedWorkspaceCase):
    """distill_to_memory.py 排除 S 类型"""

    def test_select_candidates_excludes_type_s(self):
        from service.memory.distill_to_memory import select_candidates, DISTILL_DEFAULTS

        daily_dir = self.memory_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        old_time = (utcnow() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        daily_file = daily_dir / "2026-02-19.jsonl"
        entries = [
            {"id": "f1", "type": "fact", "memory_type": "W",
             "content": "决定使用 PostgreSQL 替代 MySQL",
             "confidence": 0.95, "timestamp": old_time},
            {"id": "f2", "type": "fact", "memory_type": "S",
             "content": "阶段摘要：讨论了数据库选型",
             "confidence": 1.0, "timestamp": old_time},
        ]
        with open(daily_file, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

        candidates = select_candidates(str(daily_dir), set(), DISTILL_DEFAULTS)

        ids = [c["id"] for c in candidates]
        self.assertIn("f1", ids)
        self.assertNotIn("f2", ids)


if __name__ == "__main__":
    unittest.main(verbosity=2)
