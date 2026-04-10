"""Phase 2: Classify — 主题发现与分类。

读取变更文件的标题和摘要，推断 topic slug，匹配已有概念。
输出 topic_map: {slug: [file_paths]}。
"""

import re
from pathlib import Path


def _extract_title(content: str, filename: str) -> str:
    """提取 Markdown 文件的标题（H1 或文件名）。"""
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            return stripped[2:].strip()
    return Path(filename).stem.replace("-", " ").replace("_", " ").title()


def _extract_preview(content: str, max_chars: int = 500) -> str:
    """提取前 max_chars 字符作为摘要（跳过 frontmatter）。"""
    text = content
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            text = text[end + 3:]
    text = text.strip()
    return text[:max_chars]


def _title_to_slug(title: str) -> str:
    """将标题转为 kebab-case slug。"""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"


def _load_existing_concepts(wiki_dir: Path) -> dict[str, str]:
    """加载已有概念的 slug → title 映射。"""
    concepts: dict[str, str] = {}
    concepts_dir = wiki_dir / "concepts"
    if not concepts_dir.exists():
        return concepts

    for f in concepts_dir.glob("*.md"):
        slug = f.stem
        content = f.read_text(encoding="utf-8")
        title = _extract_title(content, f.name)
        concepts[slug] = title

    return concepts


def _find_best_match(slug: str, title: str, existing: dict[str, str]) -> str | None:
    """尝试匹配已有概念。完全匹配或子串匹配。"""
    if slug in existing:
        return slug

    slug_words = set(slug.split("-"))
    for ex_slug in existing:
        ex_words = set(ex_slug.split("-"))
        overlap = slug_words & ex_words
        if len(overlap) >= max(1, len(slug_words) // 2):
            return ex_slug

    return None


def classify(
    files: list[Path],
    root: Path,
) -> dict[str, list[Path]]:
    """将文件分类到主题。返回 {topic_slug: [file_paths]}。"""
    wiki_dir = root / "wiki"
    existing = _load_existing_concepts(wiki_dir)
    topic_map: dict[str, list[Path]] = {}

    for f in files:
        content = f.read_text(encoding="utf-8")
        title = _extract_title(content, f.name)
        slug = _title_to_slug(title)

        matched = _find_best_match(slug, title, existing)
        target_slug = matched if matched else slug

        if target_slug not in topic_map:
            topic_map[target_slug] = []
        topic_map[target_slug].append(f)

    return topic_map
