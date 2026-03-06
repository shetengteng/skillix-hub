#!/usr/bin/env python3
"""Static validation tests for prompt-helper Skill.

Verifies document structure integrity, cross-references, and design constraints
(Context Anchors, State Checkpoints) defined in the feasibility report.
"""

import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = TESTS_DIR.parent.parent / "skills" / "prompt-helper"

passed = 0
failed = 0


def assert_true(condition, msg):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")


EXPECTED_DOCS = [
    "guide-structure.md",
    "guide-scenario.md",
    "guide-output.md",
    "guide-example.md",
    "guide-info-passing.md",
    "workflow-edit.md",
    "workflow-audit.md",
    "workflow-diagnose.md",
    "checklists.md",
]

WORKFLOW_DOCS = [
    "workflow-edit.md",
    "workflow-audit.md",
]


def test_skill_md_exists():
    """SKILL.md must exist as the main entry point."""
    print("\n--- test_skill_md_exists ---")
    assert_true((SKILL_DIR / "SKILL.md").is_file(), "SKILL.md exists")


def test_docs_directory_exists():
    """docs/ directory must exist."""
    print("\n--- test_docs_directory_exists ---")
    assert_true((SKILL_DIR / "docs").is_dir(), "docs/ directory exists")


def test_all_submodules_exist():
    """All expected submodule files must exist in docs/."""
    print("\n--- test_all_submodules_exist ---")
    for doc in EXPECTED_DOCS:
        path = SKILL_DIR / "docs" / doc
        assert_true(path.is_file(), f"docs/{doc} exists")


def test_no_unexpected_files():
    """docs/ should not contain files outside the expected set."""
    print("\n--- test_no_unexpected_files ---")
    actual = {f.name for f in (SKILL_DIR / "docs").iterdir() if f.is_file()}
    expected = set(EXPECTED_DOCS)
    unexpected = actual - expected
    assert_true(len(unexpected) == 0, f"No unexpected files in docs/ (found: {unexpected or 'none'})")


def test_skill_md_has_frontmatter():
    """SKILL.md must have YAML frontmatter with name and description."""
    print("\n--- test_skill_md_has_frontmatter ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert_true(content.startswith("---"), "SKILL.md starts with frontmatter delimiter")
    assert_true("name: prompt-helper" in content, "frontmatter contains name: prompt-helper")
    assert_true("description:" in content, "frontmatter contains description field")


def test_skill_md_has_routes():
    """SKILL.md must define all 5 functional routes."""
    print("\n--- test_skill_md_has_routes ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for i in range(1, 6):
        assert_true(f"### 路由 {i}" in content, f"Route {i} defined in SKILL.md")


def test_skill_md_has_submodule_loading_rules():
    """SKILL.md must contain submodule loading rules with ${SKILL_DIR}."""
    print("\n--- test_skill_md_has_submodule_loading_rules ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert_true("子模块加载规则" in content, "Submodule loading rules section exists")
    assert_true("${SKILL_DIR}" in content, "${SKILL_DIR} variable referenced")


def test_skill_md_index_table_completeness():
    """SKILL.md index table must reference all docs/ files."""
    print("\n--- test_skill_md_index_table_completeness ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for doc in EXPECTED_DOCS:
        assert_true(f"`{doc}`" in content, f"Index table references {doc}")


def test_route_submodule_references():
    """Each route's referenced submodule file must exist."""
    print("\n--- test_route_submodule_references ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    refs = re.findall(r"`docs/([\w-]+\.md)`", content)
    for ref in refs:
        path = SKILL_DIR / "docs" / ref
        assert_true(path.is_file(), f"Route reference docs/{ref} exists on disk")


def test_context_anchors():
    """Every submodule must have a Context Anchor at the top."""
    print("\n--- test_context_anchors ---")
    for doc in EXPECTED_DOCS:
        content = (SKILL_DIR / "docs" / doc).read_text(encoding="utf-8")
        has_anchor = "核心原则提醒" in content
        assert_true(has_anchor, f"docs/{doc} has Context Anchor")


def test_state_checkpoints_in_workflows():
    """Workflow submodules must contain State Checkpoint markers."""
    print("\n--- test_state_checkpoints_in_workflows ---")
    checkpoint_pattern = re.compile(r"\[(Phase|Step)\s+\d+\s+Completed\]")
    for doc in WORKFLOW_DOCS:
        content = (SKILL_DIR / "docs" / doc).read_text(encoding="utf-8")
        matches = checkpoint_pattern.findall(content)
        assert_true(len(matches) >= 2, f"docs/{doc} has >= 2 State Checkpoints (found {len(matches)})")


def test_facet_types_inline():
    """SKILL.md must inline all 6 Facet type definitions."""
    print("\n--- test_facet_types_inline ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    facet_types = ["定义型", "知识型", "场景型", "策略型", "边界型", "规范型"]
    for ft in facet_types:
        assert_true(ft in content, f"Facet type '{ft}' inlined in SKILL.md")


def test_three_universal_principles():
    """SKILL.md must state the 3 universal principles."""
    print("\n--- test_three_universal_principles ---")
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert_true("定义与执行分离" in content, "Principle 1: 定义与执行分离")
    assert_true("一次定义，多处引用" in content, "Principle 2: 一次定义，多处引用")
    assert_true("耦合程度决定位置" in content, "Principle 3: 耦合程度决定位置")


def test_no_broken_internal_references():
    """Submodules should not reference non-existent docs/ files."""
    print("\n--- test_no_broken_internal_references ---")
    ref_pattern = re.compile(r"docs/([\w-]+\.md)")
    for doc in EXPECTED_DOCS:
        content = (SKILL_DIR / "docs" / doc).read_text(encoding="utf-8")
        refs = ref_pattern.findall(content)
        for ref in refs:
            path = SKILL_DIR / "docs" / ref
            assert_true(path.is_file(), f"docs/{doc} → docs/{ref} exists")


def test_markdown_code_blocks_balanced():
    """All Markdown files should have balanced code block fences."""
    print("\n--- test_markdown_code_blocks_balanced ---")
    all_files = [SKILL_DIR / "SKILL.md"] + [SKILL_DIR / "docs" / d for d in EXPECTED_DOCS]
    for filepath in all_files:
        content = filepath.read_text(encoding="utf-8")
        fence_count = len(re.findall(r"^```", content, re.MULTILINE))
        is_balanced = fence_count % 2 == 0
        assert_true(is_balanced, f"{filepath.name} has balanced code fences ({fence_count} fences)")


def main():
    print("=== prompt-helper static validation tests ===")
    test_skill_md_exists()
    test_docs_directory_exists()
    test_all_submodules_exist()
    test_no_unexpected_files()
    test_skill_md_has_frontmatter()
    test_skill_md_has_routes()
    test_skill_md_has_submodule_loading_rules()
    test_skill_md_index_table_completeness()
    test_route_submodule_references()
    test_context_anchors()
    test_state_checkpoints_in_workflows()
    test_facet_types_inline()
    test_three_universal_principles()
    test_no_broken_internal_references()
    test_markdown_code_blocks_balanced()
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    exit_code = main()
    sys.exit(1 if exit_code > 0 else 0)
