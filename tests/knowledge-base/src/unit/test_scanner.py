"""内容扫描模块单元测试。"""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))

from src.scanner import (
    scan_entry, detect_changes, build_pending_list,
    update_hashes,
)
from src.indexer import read_index, write_index


class TestScanEntry:
    def test_markdown_entry(self, sample_md):
        entry = {
            "id": "kb-001", "title": "Test", "type": "markdown",
            "path": str(sample_md), "tags": [], "category": "test",
        }
        result = scan_entry(entry)
        assert result["status"] == "ok"
        assert "Test Document" in result["content_preview"]

    def test_nonexistent_path(self):
        entry = {
            "id": "kb-bad", "title": "Bad", "type": "markdown",
            "path": "/nonexistent/file.md", "tags": [], "category": "test",
        }
        result = scan_entry(entry)
        assert result["status"] == "invalid"

    def test_link_type_allows_missing_path(self):
        entry = {
            "id": "kb-link", "title": "Link", "type": "link",
            "path": "https://example.com", "tags": [], "category": "test",
        }
        result = scan_entry(entry)
        assert result["status"] == "ok"
        assert "外部链接" in result["content_preview"]

    def test_image_entry(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG" + b"\x00" * 50)
        entry = {
            "id": "kb-img", "title": "Image", "type": "image",
            "path": str(img), "tags": [], "category": "test",
        }
        result = scan_entry(entry)
        assert result["status"] == "ok"
        assert "图片" in result["content_preview"]


class TestDetectChanges:
    def test_all_new(self, data_dir, populated_index):
        changes = detect_changes(data_dir)
        assert len(changes["new"]) == 5
        assert len(changes["changed"]) == 0
        assert len(changes["unchanged"]) == 0

    def test_compiled_unchanged(self, data_dir, populated_index):
        entries = read_index(data_dir)
        for e in entries:
            e["compiled"] = True
        write_index(data_dir, entries)

        changes = detect_changes(data_dir)
        assert len(changes["new"]) == 0

    def test_invalid_paths(self, data_dir):
        entries = [
            {"id": "kb-gone", "title": "Gone", "type": "markdown",
             "path": "/nonexistent/path.md", "compiled": True, "content_hash": "x"},
        ]
        write_index(data_dir, entries)
        changes = detect_changes(data_dir)
        assert len(changes["invalid"]) == 1


class TestBuildPendingList:
    def test_incremental(self, data_dir, populated_index):
        pending = build_pending_list(data_dir, full=False)
        assert len(pending) == 5

    def test_full_rebuild(self, data_dir, populated_index):
        entries = read_index(data_dir)
        entries[0]["compiled"] = True
        write_index(data_dir, entries)

        pending_inc = build_pending_list(data_dir, full=False)
        pending_full = build_pending_list(data_dir, full=True)
        assert len(pending_inc) == 4
        assert len(pending_full) == 5

    def test_empty_index(self, data_dir):
        pending = build_pending_list(data_dir, full=False)
        assert pending == []


class TestUpdateHashes:
    def test_updates_changed_entries(self, data_dir, sample_files):
        from src.indexer import compute_hash
        md = sample_files / "test-skill" / "doc-0.md"
        entries = [{
            "id": "kb-0", "type": "markdown", "path": str(md),
            "content_hash": "old_hash",
        }]
        write_index(data_dir, entries)

        updated = update_hashes(data_dir)
        assert updated == 1

        entries = read_index(data_dir)
        assert entries[0]["content_hash"] != "old_hash"
