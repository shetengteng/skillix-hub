"""索引管理模块单元测试。"""

import json
import sys
import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))

from src.indexer import (
    read_index, write_index, generate_id, detect_type,
    compute_hash, extract_title, infer_category,
)


class TestReadWriteIndex:
    def test_empty_index(self, data_dir):
        entries = read_index(data_dir)
        assert entries == []

    def test_write_and_read(self, data_dir):
        entries = [
            {"id": "kb-001", "title": "Test", "type": "markdown", "path": "/a.md"},
            {"id": "kb-002", "title": "Test2", "type": "image", "path": "/b.png"},
        ]
        write_index(data_dir, entries)
        got = read_index(data_dir)
        assert len(got) == 2
        assert got[0]["id"] == "kb-001"
        assert got[1]["id"] == "kb-002"

    def test_corrupted_line_skipped(self, data_dir):
        index_file = data_dir / "raw" / "index.jsonl"
        index_file.write_text(
            '{"id": "ok"}\n'
            'NOT VALID JSON\n'
            '{"id": "ok2"}\n'
        )
        got = read_index(data_dir)
        assert len(got) == 2

    def test_overwrite(self, data_dir):
        write_index(data_dir, [{"id": "first"}])
        write_index(data_dir, [{"id": "second"}, {"id": "third"}])
        got = read_index(data_dir)
        assert len(got) == 2
        assert got[0]["id"] == "second"


class TestGenerateId:
    def test_format(self):
        id1 = generate_id()
        assert id1.startswith("kb-")
        parts = id1.split("-")
        assert len(parts) == 4

    def test_unique(self):
        ids = {generate_id() for _ in range(10)}
        assert len(ids) == 10


class TestDetectType:
    def test_markdown(self, tmp_path):
        f = tmp_path / "test.md"
        f.touch()
        assert detect_type(str(f)) == "markdown"

    def test_image(self, tmp_path):
        f = tmp_path / "photo.png"
        f.touch()
        assert detect_type(str(f)) == "image"

    def test_dataset(self, tmp_path):
        f = tmp_path / "data.csv"
        f.touch()
        assert detect_type(str(f)) == "dataset"

    def test_repo(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").mkdir()
        assert detect_type(str(repo)) == "repo"

    def test_directory(self, tmp_path):
        d = tmp_path / "somedir"
        d.mkdir()
        assert detect_type(str(d)) == "directory"

    def test_known_text_extension(self, tmp_path):
        f = tmp_path / "readme.txt"
        f.touch()
        assert detect_type(str(f)) == "text"

    def test_code_extension(self, tmp_path):
        f = tmp_path / "main.py"
        f.touch()
        assert detect_type(str(f)) == "code"

    def test_config_extension(self, tmp_path):
        f = tmp_path / "config.yaml"
        f.touch()
        assert detect_type(str(f)) == "config"

    def test_unknown_text_file_defaults_text(self, tmp_path):
        f = tmp_path / "data.xyz"
        f.write_text("some text content")
        assert detect_type(str(f)) == "text"

    def test_unknown_binary_defaults_binary(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x00\x01\x02\x03")
        assert detect_type(str(f)) == "binary"


class TestComputeHash:
    def test_markdown_hash(self, sample_md):
        h = compute_hash(str(sample_md), "markdown")
        assert len(h) == 8
        assert h.isalnum()

    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("same content")
        f2.write_text("same content")
        assert compute_hash(str(f1), "markdown") == compute_hash(str(f2), "markdown")

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("content A")
        f2.write_text("content B")
        assert compute_hash(str(f1), "markdown") != compute_hash(str(f2), "markdown")

    def test_nonexistent_returns_empty(self):
        assert compute_hash("/nonexistent/path.md", "markdown") == ""

    def test_image_hash_uses_stat(self, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(b"\x89PNG" + b"\x00" * 100)
        h = compute_hash(str(f), "image")
        assert len(h) == 8


class TestExtractTitle:
    def test_from_h1(self, sample_md):
        title = extract_title(str(sample_md), "markdown")
        assert title == "Test Document"

    def test_fallback_to_stem(self, tmp_path):
        f = tmp_path / "no-heading.md"
        f.write_text("just text\nno heading\n")
        title = extract_title(str(f), "markdown")
        assert title == "no-heading"

    def test_nonexistent(self):
        title = extract_title("/nonexistent.md", "markdown")
        assert title == "nonexistent"

    def test_image_uses_stem(self, tmp_path):
        f = tmp_path / "photo.png"
        f.touch()
        assert extract_title(str(f), "image") == "photo"


class TestInferCategory:
    def test_from_design_path(self):
        assert infer_category("/project/design/memory/doc.md") == "memory"

    def test_from_nested_design(self):
        assert infer_category("/a/b/design/skill-store/2026-01-01.md") == "skill-store"

    def test_no_design_dir(self):
        assert infer_category("/a/b/docs/readme.md") == "uncategorized"

    def test_design_file_directly(self):
        assert infer_category("/project/design/overview.md") == "uncategorized"
