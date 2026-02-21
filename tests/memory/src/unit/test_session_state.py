#!/usr/bin/env python3
"""service/memory/session_state.py 单元测试。"""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from test_common import IsolatedWorkspaceCase, SCRIPTS_DIR

sys.path.insert(0, str(SCRIPTS_DIR))

from service.memory.session_state import (
    read_session_state,
    is_summary_saved,
    mark_summary_saved,
    update_fact_count,
    save_summary_atomic,
    SaveResult,
    _state_path,
    _sessions_lock_path,
)


class TestReadSessionState(IsolatedWorkspaceCase):

    def test_returns_empty_dict_when_no_file(self):
        state = read_session_state(str(self.memory_dir), "nonexistent-session")
        self.assertEqual(state, {})

    def test_reads_existing_state_file(self):
        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "session_id": "test-session",
            "summary_saved": True,
            "summary_source": "layer1_rules",
            "fact_count": 3,
        }
        (state_dir / "test-session.json").write_text(
            json.dumps(state, ensure_ascii=False), encoding="utf-8"
        )

        result = read_session_state(str(self.memory_dir), "test-session")
        self.assertEqual(result["session_id"], "test-session")
        self.assertTrue(result["summary_saved"])
        self.assertEqual(result["fact_count"], 3)

    def test_returns_empty_dict_on_corrupt_json(self):
        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "bad-session.json").write_text("not json", encoding="utf-8")

        result = read_session_state(str(self.memory_dir), "bad-session")
        self.assertEqual(result, {})


class TestIsSummarySaved(IsolatedWorkspaceCase):

    def test_returns_false_when_no_state(self):
        self.assertFalse(is_summary_saved(str(self.memory_dir), "no-session"))

    def test_returns_true_when_saved(self):
        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "saved-session.json").write_text(
            json.dumps({"summary_saved": True}), encoding="utf-8"
        )
        self.assertTrue(is_summary_saved(str(self.memory_dir), "saved-session"))

    def test_returns_false_when_not_saved(self):
        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "unsaved-session.json").write_text(
            json.dumps({"summary_saved": False}), encoding="utf-8"
        )
        self.assertFalse(is_summary_saved(str(self.memory_dir), "unsaved-session"))


class TestMarkSummarySaved(IsolatedWorkspaceCase):

    def test_creates_state_file(self):
        mark_summary_saved(str(self.memory_dir), "new-session", "layer1_rules")

        state_path = self.memory_dir / "session_state" / "new-session.json"
        self.assertTrue(state_path.exists())

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertTrue(state["summary_saved"])
        self.assertEqual(state["summary_source"], "layer1_rules")
        self.assertEqual(state["session_id"], "new-session")

    def test_updates_existing_state_file(self):
        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "existing-session.json").write_text(
            json.dumps({
                "session_id": "existing-session",
                "summary_saved": False,
                "fact_count": 5,
                "created_at": "2026-02-21T10:00:00Z",
            }),
            encoding="utf-8",
        )

        mark_summary_saved(str(self.memory_dir), "existing-session", "layer4_stop")

        state = json.loads((state_dir / "existing-session.json").read_text(encoding="utf-8"))
        self.assertTrue(state["summary_saved"])
        self.assertEqual(state["summary_source"], "layer4_stop")
        self.assertEqual(state["fact_count"], 5)


class TestUpdateFactCount(IsolatedWorkspaceCase):

    def test_creates_state_and_increments_fact_count(self):
        update_fact_count(str(self.memory_dir), "fact-session", "W")

        state_path = self.memory_dir / "session_state" / "fact-session.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["fact_count"], 1)
        self.assertFalse(state["summary_saved"])

    def test_increments_stage_summary_count_for_type_s(self):
        update_fact_count(str(self.memory_dir), "stage-session", "S")

        state_path = self.memory_dir / "session_state" / "stage-session.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state.get("stage_summary_count"), 1)
        self.assertEqual(state.get("fact_count", 0), 0)

    def test_increments_multiple_times(self):
        sid = "multi-fact-session"
        update_fact_count(str(self.memory_dir), sid, "W")
        update_fact_count(str(self.memory_dir), sid, "W")
        update_fact_count(str(self.memory_dir), sid, "S")

        state_path = self.memory_dir / "session_state" / f"{sid}.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["fact_count"], 2)
        self.assertEqual(state["stage_summary_count"], 1)

    def test_noop_when_no_session_id(self):
        update_fact_count(str(self.memory_dir), "", "W")
        state_dir = self.memory_dir / "session_state"
        if state_dir.exists():
            self.assertEqual(len(list(state_dir.glob("*.json"))), 0)


class TestSaveSummaryAtomic(IsolatedWorkspaceCase):

    def _setup_sessions_file(self):
        sessions_path = self.memory_dir / "sessions.jsonl"
        return str(sessions_path)

    def test_saves_when_no_prior_state(self):
        sessions_path = self._setup_sessions_file()
        written = []

        def write_fn():
            written.append(True)
            with open(sessions_path, "a") as f:
                f.write('{"test": true}\n')

        result = save_summary_atomic(str(self.memory_dir), "atomic-session", "layer1_rules", write_fn)

        self.assertEqual(result.status, SaveResult.SAVED)
        self.assertTrue(result.ok)
        self.assertEqual(len(written), 1)

        state = read_session_state(str(self.memory_dir), "atomic-session")
        self.assertTrue(state["summary_saved"])
        self.assertEqual(state["summary_source"], "layer1_rules")

    def test_skips_when_already_saved(self):
        state_dir = self.memory_dir / "session_state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "dup-session.json").write_text(
            json.dumps({"session_id": "dup-session", "summary_saved": True, "summary_source": "layer1_rules"}),
            encoding="utf-8",
        )

        written = []
        result = save_summary_atomic(
            str(self.memory_dir), "dup-session", "layer4_stop",
            lambda: written.append(True),
        )

        self.assertEqual(result.status, SaveResult.EXISTS)
        self.assertFalse(result.ok)
        self.assertEqual(len(written), 0)

    def test_idempotent_concurrent_calls(self):
        sessions_path = self._setup_sessions_file()
        written = []

        def write_fn():
            written.append(True)
            with open(sessions_path, "a") as f:
                f.write('{"test": true}\n')

        r1 = save_summary_atomic(str(self.memory_dir), "idem-session", "layer1_rules", write_fn)
        r2 = save_summary_atomic(str(self.memory_dir), "idem-session", "layer4_stop", write_fn)

        self.assertEqual(r1.status, SaveResult.SAVED)
        self.assertEqual(r2.status, SaveResult.EXISTS)
        self.assertEqual(len(written), 1)

    def test_result_to_dict(self):
        r = SaveResult(SaveResult.ERROR, "lock_timeout: test")
        d = r.to_dict()
        self.assertEqual(d["status"], "error")
        self.assertEqual(d["reason"], "lock_timeout: test")


if __name__ == "__main__":
    unittest.main(verbosity=2)
