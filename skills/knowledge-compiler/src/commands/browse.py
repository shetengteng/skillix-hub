"""kc browse — 知识地图浏览。"""

from pathlib import Path
from typing import Optional

import typer

from ..common import find_project_root
from ..compiler import _parse_frontmatter
from ..schema import load_schema


def register(app: typer.Typer) -> None:
    app.command("browse")(browse_cmd)


def browse_cmd(
    category: Optional[str] = typer.Argument(None, help="查看指定分类的详情"),
) -> None:
    """知识地图浏览。"""
    root = find_project_root()
    if root is None:
        typer.echo("错误: 未找到知识库。请先运行 kc init")
        raise typer.Exit(1)

    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists() or not list(concepts_dir.glob("*.md")):
        typer.echo("知识库为空。")
        return

    schema = load_schema(root)

    concept_data = {}
    for f in sorted(concepts_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)
        slug = f.stem

        coverages = []
        for line in body.split("\n"):
            if "<!-- coverage:" in line:
                cov = line.split("coverage:")[1].split("-->")[0].strip()
                coverages.append(cov)

        concept_data[slug] = {
            "title": meta.get("title", slug.replace("-", " ").title()),
            "tags": meta.get("tags", []),
            "sources": meta.get("sources", []),
            "updated": meta.get("updated", ""),
            "coverage": coverages,
        }

    if category:
        _browse_category(category, schema, concept_data)
    else:
        _browse_overview(schema, concept_data)


def _browse_overview(schema, concept_data: dict) -> None:
    """显示知识地图总览。"""
    typer.echo("═══ Knowledge Map ═══\n")

    categorized_slugs = set()
    for cat, topics in schema.taxonomy.items():
        if not topics:
            continue

        existing = [s for s in topics if s in concept_data]
        if not existing:
            continue

        categorized_slugs.update(existing)

        typer.echo(f"📂 {cat} ({len(existing)} concepts)")
        for slug in existing:
            data = concept_data[slug]
            cov = data["coverage"]
            h, m, l = cov.count("high"), cov.count("medium"), cov.count("low")
            tags_str = ", ".join(str(t) for t in data["tags"][:3]) if data["tags"] else ""
            tag_display = f" [{tags_str}]" if tags_str else ""
            typer.echo(f"  - [{slug}] {data['title']}{tag_display} ({h}H/{m}M/{l}L)")
        typer.echo()

    uncategorized = [s for s in concept_data if s not in categorized_slugs]
    if uncategorized:
        typer.echo(f"📂 Uncategorized ({len(uncategorized)} concepts)")
        for slug in uncategorized:
            data = concept_data[slug]
            cov = data["coverage"]
            h, m, l = cov.count("high"), cov.count("medium"), cov.count("low")
            typer.echo(f"  - [{slug}] {data['title']} ({h}H/{m}M/{l}L)")
        typer.echo()

    typer.echo(f"Total: {len(concept_data)} concepts")
    typer.echo("💡 Use `kc browse <category>` for details")


def _browse_category(category: str, schema, concept_data: dict) -> None:
    """显示指定分类的详情。"""
    topics = schema.taxonomy.get(category, [])
    existing = [s for s in topics if s in concept_data]

    if not existing:
        all_cats = [c for c, t in schema.taxonomy.items() if t]
        typer.echo(f"分类 '{category}' 不存在或为空。")
        if all_cats:
            typer.echo(f"可用分类: {', '.join(all_cats)}")
        return

    typer.echo(f"═══ {category} ═══\n")

    for slug in existing:
        data = concept_data[slug]
        cov = data["coverage"]
        h, m, l = cov.count("high"), cov.count("medium"), cov.count("low")

        typer.echo(f"## {data['title']} (`{slug}`)")
        typer.echo(f"  Coverage: {h}H/{m}M/{l}L")
        typer.echo(f"  Updated: {data['updated']}")
        if data["tags"]:
            typer.echo(f"  Tags: {', '.join(str(t) for t in data['tags'])}")
        if data["sources"]:
            typer.echo(f"  Sources: {len(data['sources'])} files")
            for src in data["sources"][:5]:
                typer.echo(f"    - {src}")
        typer.echo()
