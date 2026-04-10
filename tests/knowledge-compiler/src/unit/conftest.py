"""Shared fixtures for knowledge-compiler tests."""

import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[4] / "skills" / "knowledge-compiler"
sys.path.insert(0, str(SKILL_DIR))


@pytest.fixture
def kc_root(tmp_path):
    """Create a minimal initialized knowledge-compiler project."""
    config = {
        "session_mode": "recommended",
        "sources": ["raw/designs", "raw/decisions", "raw/research", "raw/notes"],
        "output_dir": "wiki",
        "exclude": ["raw/assets"],
        "compile_options": {"parallel_topics": True, "max_parallel": 4},
        "quality": {"lint_mode": "quick"},
    }

    (tmp_path / ".kc-config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )

    for d in ["designs", "decisions", "research", "notes", "assets"]:
        (tmp_path / "raw" / d).mkdir(parents=True)

    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "concepts").mkdir()
    (wiki / "INDEX.md").write_text("# Wiki Index\n")
    (wiki / "schema.md").write_text("# Wiki Schema\n")
    (wiki / "log.md").write_text("# Compile Log\n")

    return tmp_path


@pytest.fixture
def sample_docs(kc_root):
    """Add sample documents to raw/."""
    docs = {}

    d1 = kc_root / "raw" / "research" / "transformer.md"
    d1.write_text(
        "# Transformer Architecture\n\n"
        "The Transformer model was introduced in Attention Is All You Need.\n"
        "It relies on self-attention mechanisms.\n"
    )
    docs["transformer"] = d1

    d2 = kc_root / "raw" / "research" / "rag.md"
    d2.write_text(
        "# RAG Overview\n\n"
        "Retrieval-Augmented Generation combines retriever with generator.\n"
        "It grounds LLM outputs in factual documents.\n"
    )
    docs["rag"] = d2

    d3 = kc_root / "raw" / "decisions" / "use-postgresql.md"
    d3.write_text(
        "# Architecture Decision: Use PostgreSQL\n\n"
        "We chose PostgreSQL over MongoDB.\n"
        "Our data is highly relational.\n"
    )
    docs["postgresql"] = d3

    return docs
