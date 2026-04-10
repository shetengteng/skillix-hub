"""state.py 单元测试。"""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"))

from src.state import update_compile_state, append_log, compute_concept_states


def _setup_kb(tmp_path, articles=None, state_data=None, source_files=None):
    """设置测试知识库。"""
    wiki_dir = tmp_path / "wiki"
    concepts_dir = wiki_dir / "concepts"
    concepts_dir.mkdir(parents=True)

    (tmp_path / ".kc-config.json").write_text('{"sources":["raw"]}', encoding="utf-8")

    if state_data:
        (tmp_path / ".compile-state.json").write_text(
            json.dumps(state_data), encoding="utf-8")
    else:
        (tmp_path / ".compile-state.json").write_text("{}", encoding="utf-8")

    if source_files:
        for rel_path, content in source_files.items():
            p = tmp_path / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

    if articles:
        for slug, content in articles.items():
            (concepts_dir / f"{slug}.md").write_text(content, encoding="utf-8")


class TestUpdateCompileState:
    def test_saves_state(self, tmp_path):
        _setup_kb(tmp_path, source_files={"raw/test.md": "content"})

        src = tmp_path / "raw" / "test.md"
        update_compile_state(tmp_path, [src], {"test-topic": [src]})

        state = json.loads((tmp_path / ".compile-state.json").read_text())
        assert "last_compiled" in state
        assert "raw/test.md" in state["files"]
        assert "test-topic" in state["files"]["raw/test.md"]["topics"]

    def test_updates_mtime(self, tmp_path):
        _setup_kb(tmp_path, source_files={"raw/test.md": "content"})

        src = tmp_path / "raw" / "test.md"
        update_compile_state(tmp_path, [src], {})

        state = json.loads((tmp_path / ".compile-state.json").read_text())
        assert state["files"]["raw/test.md"]["mtime"] > 0


class TestAppendLog:
    def test_creates_log(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)

        append_log(tmp_path, "3 new", 3, 3)

        log = (wiki_dir / "log.md").read_text(encoding="utf-8")
        assert "compile" in log
        assert "3 new" in log

    def test_appends_to_existing(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "log.md").write_text("# Compile Log\n\n## Previous\n", encoding="utf-8")

        append_log(tmp_path, "2 changed", 2, 0, "Hard: 5 pass / 0 fail")

        log = (wiki_dir / "log.md").read_text(encoding="utf-8")
        assert "Previous" in log
        assert "2 changed" in log
        assert "Hard: 5 pass" in log


class TestComputeConceptStates:
    def test_ok_concept(self, tmp_path):
        article = """---
id: "test"
title: "Test"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Test

## Summary
<!-- coverage: high -->
Content.
"""
        _setup_kb(tmp_path,
            articles={"test": article},
            source_files={"raw/test.md": "content"},
            state_data={"files": {"raw/test.md": {"mtime": 9999999999, "topics": ["test"]}}})

        states = compute_concept_states(tmp_path)
        assert len(states) == 1
        assert states[0].status == "ok"

    def test_orphan_concept(self, tmp_path):
        article = """---
id: "orphan"
title: "Orphan"
sources: []
created: "2026-04-10"
updated: "2026-04-10"
---

# Orphan

## Summary
<!-- coverage: low -->
Content.
"""
        _setup_kb(tmp_path, articles={"orphan": article})

        states = compute_concept_states(tmp_path)
        assert states[0].status == "orphan"

    def test_weak_concept(self, tmp_path):
        article = """---
id: "weak"
title: "Weak"
sources:
  - raw/test.md
created: "2026-04-10"
updated: "2026-04-10"
---

# Weak

## Summary
<!-- coverage: low -->
Low.

## Details
<!-- coverage: low -->
Low.

## More
<!-- coverage: low -->
Low.
"""
        _setup_kb(tmp_path,
            articles={"weak": article},
            source_files={"raw/test.md": "content"},
            state_data={"files": {"raw/test.md": {"mtime": 9999999999, "topics": ["weak"]}}})

        states = compute_concept_states(tmp_path)
        assert states[0].status == "weak"

    def test_aging_concept(self, tmp_path):
        article = """---
id: "old"
title: "Old"
sources:
  - raw/test.md
created: "2025-01-01"
updated: "2025-01-01"
---

# Old

## Summary
<!-- coverage: high -->
Old content.
"""
        _setup_kb(tmp_path,
            articles={"old": article},
            source_files={"raw/test.md": "content"},
            state_data={"files": {"raw/test.md": {"mtime": 9999999999, "topics": ["old"]}}})

        states = compute_concept_states(tmp_path)
        assert states[0].status == "aging"
