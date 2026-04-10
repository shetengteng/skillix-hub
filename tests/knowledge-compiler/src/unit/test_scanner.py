"""Tests for scanner.py (Phase 1)."""

import json
import time
from pathlib import Path

from src.scanner import scan


class TestScan:
    def test_scan_new_files(self, kc_root, sample_docs):
        result = scan(kc_root)
        assert len(result.new_files) == 3
        assert len(result.changed_files) == 0
        assert len(result.deleted_files) == 0

    def test_scan_no_changes_after_compile(self, kc_root, sample_docs):
        result = scan(kc_root)
        state = {
            "last_compiled": "2026-04-10",
            "files": {},
        }
        for f in result.new_files:
            rel = str(f.relative_to(kc_root))
            state["files"][rel] = {"mtime": f.stat().st_mtime, "topics": []}

        (kc_root / ".compile-state.json").write_text(json.dumps(state))

        result2 = scan(kc_root)
        assert len(result2.new_files) == 0
        assert len(result2.changed_files) == 0
        assert len(result2.unchanged_files) == 3

    def test_scan_changed_file(self, kc_root, sample_docs):
        result = scan(kc_root)
        state = {
            "last_compiled": "2026-04-10",
            "files": {},
        }
        for f in result.new_files:
            rel = str(f.relative_to(kc_root))
            state["files"][rel] = {"mtime": f.stat().st_mtime, "topics": []}

        (kc_root / ".compile-state.json").write_text(json.dumps(state))

        time.sleep(0.1)
        sample_docs["transformer"].write_text("# Updated\n\nNew content.\n")

        result2 = scan(kc_root)
        assert len(result2.changed_files) == 1
        assert result2.changed_files[0].name == "transformer.md"

    def test_scan_deleted_file(self, kc_root, sample_docs):
        result = scan(kc_root)
        state = {
            "last_compiled": "2026-04-10",
            "files": {},
        }
        for f in result.new_files:
            rel = str(f.relative_to(kc_root))
            state["files"][rel] = {"mtime": f.stat().st_mtime, "topics": []}

        (kc_root / ".compile-state.json").write_text(json.dumps(state))
        sample_docs["rag"].unlink()

        result2 = scan(kc_root)
        assert len(result2.deleted_files) == 1
        assert "rag.md" in result2.deleted_files[0]

    def test_scan_full_mode(self, kc_root, sample_docs):
        result = scan(kc_root)
        state = {
            "last_compiled": "2026-04-10",
            "files": {},
        }
        for f in result.new_files:
            rel = str(f.relative_to(kc_root))
            state["files"][rel] = {"mtime": f.stat().st_mtime, "topics": []}

        (kc_root / ".compile-state.json").write_text(json.dumps(state))

        result2 = scan(kc_root, full=True)
        assert len(result2.changed_files) == 3
        assert len(result2.new_files) == 0

    def test_scan_excludes_assets(self, kc_root):
        (kc_root / "raw" / "assets" / "image.md").write_text("# Not a real doc\n")
        result = scan(kc_root)
        for f in result.new_files:
            assert "assets" not in str(f)

    def test_scan_summary(self, kc_root, sample_docs):
        result = scan(kc_root)
        summary = result.summary()
        assert "3 new" in summary

    def test_has_changes(self, kc_root, sample_docs):
        result = scan(kc_root)
        assert result.has_changes is True

    def test_no_changes(self, kc_root):
        result = scan(kc_root)
        assert result.has_changes is False
