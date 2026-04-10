"""kc status — 知识库状态总览。"""

import json
from pathlib import Path

import typer

from ..common import find_project_root, load_state
from ..compiler import _parse_frontmatter
from ..state import compute_concept_states
from ..schema import load_schema


def register(app: typer.Typer) -> None:
    app.command("status")(status_cmd)


def status_cmd() -> None:
    """知识库状态总览。"""
    root = find_project_root()
    if root is None:
        typer.echo("错误: 未找到知识库。请先运行 kc init")
        raise typer.Exit(1)

    config_path = root / ".kc-config.json"
    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    state = load_state(root)
    schema = load_schema(root)

    typer.echo("═══ Knowledge Compiler Status ═══\n")

    typer.echo(f"  📁 Root: {root}")
    typer.echo(f"  🔧 Session mode: {config.get('session_mode', 'staging')}")
    typer.echo(f"  📅 Last compiled: {state.get('last_compiled', 'never')}")
    typer.echo()

    raw_dir = root / "raw"
    raw_count = 0
    if raw_dir.exists():
        raw_count = sum(1 for f in raw_dir.rglob("*") if f.is_file() and f.suffix in (".md", ".mdx", ".rst", ".txt"))
    typer.echo(f"  📄 Source files: {raw_count}")

    concepts_dir = root / "wiki" / "concepts"
    concept_files = list(concepts_dir.glob("*.md")) if concepts_dir.exists() else []
    typer.echo(f"  📚 Concepts: {len(concept_files)}")

    cat_count = sum(1 for cat, topics in schema.taxonomy.items() if topics)
    typer.echo(f"  🏷️  Categories: {cat_count}")
    typer.echo()

    if concept_files:
        total_h = total_m = total_l = 0
        for f in concept_files:
            content = f.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if "<!-- coverage: high -->" in line:
                    total_h += 1
                elif "<!-- coverage: medium -->" in line:
                    total_m += 1
                elif "<!-- coverage: low -->" in line:
                    total_l += 1

        total = total_h + total_m + total_l
        typer.echo("  Coverage distribution:")
        if total > 0:
            typer.echo(f"    🟢 high:   {total_h} ({total_h * 100 // total}%)")
            typer.echo(f"    🟡 medium: {total_m} ({total_m * 100 // total}%)")
            typer.echo(f"    🔴 low:    {total_l} ({total_l * 100 // total}%)")
        else:
            typer.echo("    No coverage tags found")
        typer.echo()

    states = compute_concept_states(root)
    if states:
        status_groups = {}
        for s in states:
            status_groups.setdefault(s.status, []).append(s)

        typer.echo("  Concept health:")
        icons = {"ok": "✅", "needs_recompile": "🔄", "aging": "⏳", "weak": "📉", "orphan": "🔗"}
        for status in ["ok", "needs_recompile", "aging", "weak", "orphan"]:
            items = status_groups.get(status, [])
            if items:
                typer.echo(f"    {icons.get(status, '❓')} {status}: {len(items)}")

        problem_states = [s for s in states if s.status != "ok"]
        if problem_states:
            typer.echo()
            typer.echo("  Issues:")
            for s in problem_states[:10]:
                typer.echo(f"    [{s.slug}] {s.status}: {s.reason}")
            if len(problem_states) > 10:
                typer.echo(f"    ... and {len(problem_states) - 10} more")
