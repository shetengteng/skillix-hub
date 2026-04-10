"""kc compile — 编译知识库。"""

from datetime import date
from pathlib import Path
from typing import Optional

import typer

from ..common import find_project_root
from ..scanner import scan
from ..classifier import classify
from ..compiler import generate_compile_prompt, create_stub_article, _parse_frontmatter, _render_frontmatter
from ..schema import load_schema, update_schema
from ..indexer import update_index
from ..verifier import verify
from ..state import update_compile_state, append_log


def _auto_fill_relations(root: Path, concepts_dir: Path) -> None:
    """扫描所有概念文章，自动检测正文中出现的其他 slug 并填充 relations.related。"""
    if not concepts_dir.exists():
        return

    all_slugs = {f.stem for f in concepts_dir.glob("*.md")}
    if not all_slugs:
        return

    updated_count = 0
    for f in sorted(concepts_dir.glob("*.md")):
        slug = f.stem
        content = f.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)

        body_lower = body.lower()
        detected = set()
        for other in all_slugs:
            if other == slug:
                continue
            if other in body_lower or f"[[{other}]]" in body_lower:
                detected.add(other)

        relations = meta.get("relations", {})
        if isinstance(relations, str):
            relations = {}
        existing_related = set(relations.get("related", []))
        depends_on = relations.get("depends_on", [])

        merged = existing_related | detected
        if merged != existing_related:
            relations["related"] = sorted(merged)
            relations["depends_on"] = depends_on
            meta["relations"] = relations
            new_content = _render_frontmatter(meta) + "\n" + body
            f.write_text(new_content, encoding="utf-8")
            added = merged - existing_related
            typer.echo(f"  [{slug}] +relations: {sorted(added)}")
            updated_count += 1

    typer.echo(f"  {updated_count} 篇概念文章的 relations 已更新")


def register(app: typer.Typer) -> None:
    app.command("compile")(compile_cmd)


def compile_cmd(
    full: bool = typer.Option(False, "--full", help="全量重编译"),
    dry_run: bool = typer.Option(False, "--dry-run", help="预览变更，不写入"),
    topic: Optional[str] = typer.Option(None, "--topic", help="只编译指定概念"),
) -> None:
    """编译知识库 Wiki。"""
    root = find_project_root()
    if root is None:
        typer.echo("错误: 未找到知识库。请先运行 kc init")
        raise typer.Exit(1)

    # Phase 1: Scan
    typer.echo("Phase 1: 扫描变更...")
    scan_result = scan(root, full=full)
    typer.echo(f"  {scan_result.summary()}")

    if not scan_result.has_changes and not full:
        typer.echo("没有变更，无需编译。")
        return

    # Phase 2: Classify
    changed = scan_result.new_files + scan_result.changed_files
    typer.echo(f"\nPhase 2: 分类 {len(changed)} 个文件...")
    topic_map = classify(changed, root)

    if topic and topic not in topic_map:
        all_sources = scan_result.new_files + scan_result.changed_files + scan_result.unchanged_files
        topic_map_full = classify(all_sources, root)
        if topic in topic_map_full:
            topic_map = {topic: topic_map_full[topic]}
        else:
            typer.echo(f"概念 '{topic}' 未找到")
            raise typer.Exit(1)
    elif topic:
        topic_map = {topic: topic_map[topic]}

    for slug, files in topic_map.items():
        file_names = [f.name for f in files]
        typer.echo(f"  {slug}: {file_names}")

    if dry_run:
        typer.echo(f"\n[dry-run] 将编译 {len(topic_map)} 个概念，不写入文件。")
        return

    # Phase 3: Compile
    typer.echo(f"\nPhase 3: 编译 {len(topic_map)} 个概念...")
    concepts_dir = root / "wiki" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    topics_new = 0
    for slug, files in topic_map.items():
        article_path = concepts_dir / f"{slug}.md"
        is_new = not article_path.exists()

        existing_content = None
        if article_path.exists():
            existing_content = article_path.read_text(encoding="utf-8")

        prompt = generate_compile_prompt(slug, files, root, existing_content)

        prompt_path = root / ".kc-compile-prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        if existing_content:
            old_meta, old_body = _parse_frontmatter(existing_content)
            source_paths = [str(f.relative_to(root)) for f in files]
            old_meta["sources"] = source_paths
            old_meta["updated"] = date.today().isoformat()
            old_meta["compile_count"] = old_meta.get("compile_count", 0) + 1
            updated = _render_frontmatter(old_meta) + "\n" + old_body
            article_path.write_text(updated, encoding="utf-8")
        else:
            stub = create_stub_article(slug, files, root)
            article_path.write_text(stub, encoding="utf-8")

        status = "new" if is_new else "updated"
        if is_new:
            topics_new += 1
        typer.echo(f"  [{status}] wiki/concepts/{slug}.md")

    # Phase 3+: Auto-detect relations
    typer.echo("\nPhase 3+: 自动检测 relations...")
    _auto_fill_relations(root, concepts_dir)

    # Phase 3.5: Schema
    typer.echo("\nPhase 3.5: 更新 Schema...")
    schema = load_schema(root)
    update_schema(root, list(topic_map.keys()), schema)
    typer.echo("  wiki/schema.md updated")

    # Phase 4: Index + Verify
    typer.echo("\nPhase 4: 更新索引 + 质量检查...")
    update_index(root)
    typer.echo("  wiki/INDEX.md updated")

    report = verify(root)
    typer.echo(f"  Verify: {report.summary()}")

    if report.hard_failures:
        typer.echo("\n  ⚠️ Hard Gate failures:")
        for r in report.hard_failures:
            typer.echo(f"    [{r.article}] {r.check_name}: {r.message}")

    if report.soft_warnings:
        typer.echo("\n  💡 Soft Gate warnings:")
        for r in report.soft_warnings:
            typer.echo(f"    [{r.article}] {r.check_name}: {r.message}")

    critical_failures = [
        r for r in report.hard_failures
        if r.check_name in ("frontmatter_complete", "source_refs_valid")
    ]
    if critical_failures:
        typer.echo("\n  ❌ 编译因 Hard Gate 关键失败而中止:")
        for r in critical_failures:
            typer.echo(f"    [{r.article}] {r.check_name}: {r.message}")
        typer.echo("  请修复上述问题后重新编译。")
        raise typer.Exit(1)

    # Phase 5: State + Log
    typer.echo("\nPhase 5: 更新状态...")
    all_scanned = scan_result.new_files + scan_result.changed_files + scan_result.unchanged_files
    update_compile_state(root, all_scanned, topic_map)
    append_log(root, scan_result.summary(), len(topic_map), topics_new, report.summary())

    typer.echo(f"\n编译完成: {topics_new} new, {len(topic_map) - topics_new} updated")
    typer.echo("编译 prompt 已保存到 .kc-compile-prompt.md，可用 AI Agent 执行精细编译。")
