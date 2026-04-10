"""kc compile — 编译知识库。"""

from datetime import date
from pathlib import Path
from typing import Optional

import typer

from ..common import find_project_root, load_state, save_state
from ..scanner import scan
from ..classifier import classify
from ..compiler import generate_compile_prompt, create_stub_article


def register(app: typer.Typer) -> None:
    app.command("compile")(compile_cmd)


def _update_index(root: Path) -> None:
    """Phase 4: 更新 wiki/INDEX.md。"""
    wiki_dir = root / "wiki"
    concepts_dir = wiki_dir / "concepts"
    if not concepts_dir.exists():
        return

    articles = sorted(concepts_dir.glob("*.md"))
    today = date.today().isoformat()

    lines = [
        "# Wiki Index",
        "",
        f"> 由 Knowledge Compiler 自动维护。上次编译: {today}",
        "> 编译: `kc compile` | 健康检查: `kc lint` | 查询: `kc query <question>`",
        "",
    ]

    if articles:
        lines.append("## Concepts")
        lines.append("")
        lines.append("| Topic | Coverage | Updated |")
        lines.append("|-------|----------|---------|")

        for a in articles:
            slug = a.stem
            content = a.read_text(encoding="utf-8")
            coverages = []
            for line in content.split("\n"):
                if "<!-- coverage:" in line:
                    cov = line.split("coverage:")[1].split("-->")[0].strip()
                    coverages.append(cov)

            if coverages:
                high = coverages.count("high")
                med = coverages.count("medium")
                low = coverages.count("low")
                cov_text = f"{high}H/{med}M/{low}L"
            else:
                cov_text = "—"

            lines.append(f"| [[{slug}]] | {cov_text} | {today} |")

        lines.append("")

    stats_high = 0
    stats_med = 0
    stats_low = 0
    for a in articles:
        content = a.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if "<!-- coverage: high -->" in line:
                stats_high += 1
            elif "<!-- coverage: medium -->" in line:
                stats_med += 1
            elif "<!-- coverage: low -->" in line:
                stats_low += 1

    lines.append("## Stats")
    lines.append("")
    lines.append(f"- Total concepts: {len(articles)}")
    lines.append(f"- High coverage: {stats_high} | Medium: {stats_med} | Low: {stats_low}")
    lines.append("")

    (wiki_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def _update_log(root: Path, scan_summary: str, topics_compiled: int, topics_new: int) -> None:
    """Phase 5: 追加 wiki/log.md。"""
    log_path = root / "wiki" / "log.md"
    today = date.today().isoformat()

    entry = f"\n## [{today}] compile\n- Files: {scan_summary}\n- Topics compiled: {topics_new} new, {topics_compiled - topics_new} updated\n"

    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Compile Log\n"
    log_path.write_text(existing + entry, encoding="utf-8")


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

        stub = create_stub_article(slug, files, root)
        article_path.write_text(stub, encoding="utf-8")

        status = "new" if is_new else "updated"
        if is_new:
            topics_new += 1
        typer.echo(f"  [{status}] wiki/concepts/{slug}.md")

    # Phase 4: Index
    typer.echo("\nPhase 4: 更新索引...")
    _update_index(root)
    typer.echo("  wiki/INDEX.md updated")

    # Phase 5: State + Log
    typer.echo("\nPhase 5: 更新状态...")
    state = load_state(root)
    all_scanned = (
        scan_result.new_files + scan_result.changed_files + scan_result.unchanged_files
    )
    files_state = {}
    for f in all_scanned:
        rel = str(f.relative_to(root))
        files_state[rel] = {
            "mtime": f.stat().st_mtime,
            "topics": [],
        }

    for slug, files in topic_map.items():
        for f in files:
            rel = str(f.relative_to(root))
            if rel in files_state:
                files_state[rel]["topics"].append(slug)

    state["last_compiled"] = date.today().isoformat()
    state["files"] = files_state
    save_state(root, state)

    _update_log(root, scan_result.summary(), len(topic_map), topics_new)

    typer.echo(f"\n编译完成: {topics_new} new, {len(topic_map) - topics_new} updated")
    typer.echo(f"编译 prompt 已保存到 .kc-compile-prompt.md，可用 AI Agent 执行精细编译。")
