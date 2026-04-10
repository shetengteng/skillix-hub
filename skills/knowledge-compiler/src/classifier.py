"""Phase 2: Classify — 主题发现与分类。

读取变更文件的标题和摘要，推断 topic slug，匹配已有概念。
输出 topic_map: {slug: [file_paths]}。

增强：
- 受 schema deprecated 约束（已废弃主题自动映射到合并目标）
- 使用 preview 辅助匹配（标题匹配不足时用内容关键词补充）
"""

import re
from pathlib import Path

from .schema import load_schema, Schema


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


def _find_best_match(
    slug: str,
    title: str,
    preview: str,
    existing: dict[str, str],
) -> str | None:
    """尝试匹配已有概念。优先级：完全匹配 > 子串匹配 > preview 关键词匹配。"""
    if slug in existing:
        return slug

    slug_words = set(slug.split("-"))

    best_match = None
    best_score = 0

    for ex_slug, ex_title in existing.items():
        ex_words = set(ex_slug.split("-"))
        overlap = slug_words & ex_words
        score = len(overlap)

        if score >= max(1, len(slug_words) // 2):
            if score > best_score:
                best_score = score
                best_match = ex_slug

    if best_match:
        return best_match

    if preview:
        preview_lower = preview.lower()
        for ex_slug in existing:
            ex_words = ex_slug.split("-")
            if len(ex_words) >= 2 and all(w in preview_lower for w in ex_words):
                return ex_slug

    return None


def _resolve_deprecated(slug: str, schema: Schema) -> str:
    """如果 slug 已被废弃，返回合并目标；否则返回原 slug。"""
    if schema.is_deprecated(slug):
        merged_into = schema.deprecated.get(slug, "")
        if merged_into:
            return merged_into
    return slug


def _normalize_slug(slug: str) -> str:
    """按 naming conventions 标准化 slug（kebab-case，去重复连字符）。"""
    slug = slug.lower().strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    slug = re.sub(r"[^\w-]", "", slug)
    return slug or "untitled"


def _match_taxonomy_slug(slug: str, schema: Schema) -> str | None:
    """尝试在 taxonomy 中找到匹配的已有 slug（词集重叠匹配）。"""
    known = schema.all_known_slugs
    if slug in known:
        return slug

    slug_words = set(slug.split("-"))
    best_match = None
    best_score = 0

    for known_slug in known:
        known_words = set(known_slug.split("-"))
        overlap = slug_words & known_words
        score = len(overlap)
        if score >= max(1, len(slug_words) // 2) and score > best_score:
            best_score = score
            best_match = known_slug

    return best_match


def classify(
    files: list[Path],
    root: Path,
) -> dict[str, list[Path]]:
    """将文件分类到主题。返回 {topic_slug: [file_paths]}。"""
    wiki_dir = root / "wiki"
    existing = _load_existing_concepts(wiki_dir)
    schema = load_schema(root)
    topic_map: dict[str, list[Path]] = {}

    for f in files:
        content = f.read_text(encoding="utf-8")
        title = _extract_title(content, f.name)
        preview = _extract_preview(content)
        slug = _title_to_slug(title)
        slug = _normalize_slug(slug)

        slug = _resolve_deprecated(slug, schema)

        matched = _find_best_match(slug, title, preview, existing)
        if not matched:
            matched = _match_taxonomy_slug(slug, schema)
        target_slug = matched if matched else slug

        target_slug = _resolve_deprecated(target_slug, schema)
        target_slug = _normalize_slug(target_slug)

        if target_slug not in topic_map:
            topic_map[target_slug] = []
        topic_map[target_slug].append(f)

    return topic_map
