"""Shared fixtures for knowledge-base tests."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-base"
sys.path.insert(0, str(SKILL_DIR))


@pytest.fixture
def data_dir(tmp_path):
    """Create an isolated data directory with proper structure."""
    d = tmp_path / "knowledge-base-data"
    (d / "raw").mkdir(parents=True)
    (d / "wiki" / "concepts").mkdir(parents=True)
    (d / "wiki" / "categories").mkdir(parents=True)
    (d / "compile").mkdir(parents=True)
    (d / "raw" / "index.jsonl").touch()
    return d


@pytest.fixture
def sample_md(tmp_path):
    """Create a sample markdown file."""
    md = tmp_path / "sample.md"
    md.write_text("# Test Document\n\nSome content here.\n\n## Section\n\n- Item 1\n- Item 2\n")
    return md


@pytest.fixture
def sample_files(tmp_path):
    """Create a directory with multiple sample files."""
    design = tmp_path / "design" / "test-skill"
    design.mkdir(parents=True)
    for i in range(5):
        f = design / f"doc-{i}.md"
        f.write_text(f"# Document {i}\n\nContent of document {i}.\n")
    return design.parent


@pytest.fixture
def populated_index(data_dir, sample_files):
    """Create a data_dir with some entries already indexed."""
    from src.indexer import write_index, compute_hash
    entries = []
    design_dir = sample_files / "test-skill"
    for i, md in enumerate(sorted(design_dir.glob("*.md"))):
        entries.append({
            "id": f"kb-test-{i:03d}",
            "title": f"Document {i}",
            "type": "markdown",
            "path": str(md),
            "tags": ["test", f"doc{i}"],
            "category": "test-skill",
            "summary": "",
            "content_hash": compute_hash(str(md), "markdown"),
            "created_at": "2026-04-08T00:00:00Z",
            "updated_at": "2026-04-08T00:00:00Z",
            "compiled": False,
        })
    write_index(data_dir, entries)
    return entries
