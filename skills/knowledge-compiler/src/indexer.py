"""Phase 4: Indexer — 生成 wiki/INDEX.md。

按 schema.md 中的分类聚合概念，展示覆盖度摘要。
"""

from datetime import date
from pathlib import Path

from .compiler import _parse_frontmatter
from .schema import load_schema


def _scan_concepts(root: Path) -> list[dict]:
    """扫描 wiki/concepts/ 下的所有文章，提取元数据。"""
    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists():
        return []

    infos = []
    for f in sorted(concepts_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)

        coverages = {"high": 0, "medium": 0, "low": 0}
        for line in body.split("\n"):
            if "<!-- coverage:" in line:
                cov = line.split("coverage:")[1].split("-->")[0].strip()
                if cov in coverages:
                    coverages[cov] += 1

        infos.append({
            "slug": f.stem,
            "title": meta.get("title", f.stem.replace("-", " ").title()),
            "updated": meta.get("updated", ""),
            "sources": meta.get("sources", []),
            "coverage": coverages,
        })

    return infos


def generate_index(root: Path) -> str:
    """生成完整的 INDEX.md 内容。"""
    schema = load_schema(root)
    concepts = _scan_concepts(root)
    today = date.today().isoformat()

    concept_map = {c["slug"]: c for c in concepts}

    categorized: dict[str, list[dict]] = {}
    uncategorized: list[dict] = []

    for c in concepts:
        cat = schema.find_category(c["slug"])
        if cat:
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(c)
        else:
            uncategorized.append(c)

    lines = [
        "# Wiki Index",
        "",
        f"> 由 Knowledge Compiler 自动维护。上次编译: {today}",
        "> 编译: `kc compile` | 健康检查: `kc lint` | 查询: `kc query <question>`",
        "",
    ]

    total_high = sum(c["coverage"]["high"] for c in concepts)
    total_med = sum(c["coverage"]["medium"] for c in concepts)
    total_low = sum(c["coverage"]["low"] for c in concepts)
    total_sources = sum(len(c["sources"]) for c in concepts)

    lines.extend([
        "## Stats",
        "",
        f"- Total concepts: {len(concepts)}",
        f"- High coverage: {total_high} | Medium: {total_med} | Low: {total_low}",
        f"- Sources indexed: {total_sources} files",
        "",
    ])

    ordered_cats = [cat for cat in schema.taxonomy if cat in categorized]
    for cat in ordered_cats:
        items = categorized[cat]
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| Topic | Coverage | Updated |")
        lines.append("|-------|----------|---------|")
        for c in items:
            cov = c["coverage"]
            cov_text = f"{cov['high']}H/{cov['medium']}M/{cov['low']}L"
            lines.append(f"| [[{c['slug']}]] | {cov_text} | {c['updated']} |")
        lines.append("")

    if uncategorized:
        lines.append("## Uncategorized")
        lines.append("")
        lines.append("| Topic | Coverage | Updated |")
        lines.append("|-------|----------|---------|")
        for c in uncategorized:
            cov = c["coverage"]
            cov_text = f"{cov['high']}H/{cov['medium']}M/{cov['low']}L"
            lines.append(f"| [[{c['slug']}]] | {cov_text} | {c['updated']} |")
        lines.append("")

    return "\n".join(lines)


def update_index(root: Path) -> None:
    """重新生成 wiki/INDEX.md。"""
    content = generate_index(root)
    index_path = root / "wiki" / "INDEX.md"
    index_path.write_text(content, encoding="utf-8")
