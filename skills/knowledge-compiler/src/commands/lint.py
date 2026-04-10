"""kc lint — 知识库健康检查。

执行 Hard/Soft Gate 检查，输出质量报告。
支持 --fix 自动修复安全问题（schema 同步等）。
"""

import typer

from ..common import find_project_root
from ..verifier import verify
from ..state import compute_concept_states
from ..schema import load_schema, update_schema


def register(app: typer.Typer) -> None:
    app.command("lint")(lint_cmd)


def lint_cmd(
    fix: bool = typer.Option(False, "--fix", help="自动修复安全问题"),
) -> None:
    """知识库健康检查。"""
    root = find_project_root()
    if root is None:
        typer.echo("错误: 未找到知识库。请先运行 kc init")
        raise typer.Exit(1)

    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists() or not list(concepts_dir.glob("*.md")):
        typer.echo("知识库为空，无需检查。")
        return

    typer.echo("🔍 执行质量检查...\n")

    report = verify(root)

    typer.echo("═══ Hard Gates ═══\n")
    hard_pass = [r for r in report.hard_results if r.passed]
    hard_fail = [r for r in report.hard_results if not r.passed]

    if hard_fail:
        for r in hard_fail:
            typer.echo(f"  ❌ [{r.article}] {r.check_name}: {r.message}")
    if hard_pass:
        pass_by_check = {}
        for r in hard_pass:
            pass_by_check.setdefault(r.check_name, 0)
            pass_by_check[r.check_name] += 1
        for check, count in pass_by_check.items():
            typer.echo(f"  ✅ {check}: {count} passed")

    typer.echo(f"\n  Hard: {len(hard_pass)} pass / {len(hard_fail)} fail\n")

    typer.echo("═══ Soft Gates ═══\n")
    soft_pass = [r for r in report.soft_results if r.passed]
    soft_warn = [r for r in report.soft_results if not r.passed]

    if soft_warn:
        for r in soft_warn:
            typer.echo(f"  ⚠️  [{r.article}] {r.check_name}: {r.message}")
    if soft_pass:
        pass_by_check = {}
        for r in soft_pass:
            pass_by_check.setdefault(r.check_name, 0)
            pass_by_check[r.check_name] += 1
        for check, count in pass_by_check.items():
            typer.echo(f"  ✅ {check}: {count} passed")

    typer.echo(f"\n  Soft: {len(soft_pass)} pass / {len(soft_warn)} warn\n")

    typer.echo("═══ 概念状态 ═══\n")
    states = compute_concept_states(root)
    status_counts = {}
    for s in states:
        status_counts.setdefault(s.status, 0)
        status_counts[s.status] += 1

    for status, count in sorted(status_counts.items()):
        icon = {"ok": "✅", "needs_recompile": "🔄", "aging": "⏳", "weak": "📉", "orphan": "🔗"}.get(status, "❓")
        typer.echo(f"  {icon} {status}: {count}")

    non_ok = [s for s in states if s.status != "ok"]
    if non_ok:
        typer.echo()
        for s in non_ok:
            typer.echo(f"  [{s.slug}] {s.status}: {s.reason}")

    if fix:
        typer.echo("\n═══ 自动修复 ═══\n")
        fixed = 0

        schema_fails = [r for r in hard_fail if r.check_name == "schema_consistent"]
        if schema_fails:
            schema = load_schema(root)
            missing_slugs = [r.article for r in schema_fails]
            update_schema(root, missing_slugs, schema)
            typer.echo(f"  ✅ 已将 {len(missing_slugs)} 个概念同步到 schema.md")
            fixed += len(missing_slugs)

        if fixed == 0:
            typer.echo("  没有可自动修复的问题。")
        else:
            typer.echo(f"\n  修复了 {fixed} 个问题。")

    typer.echo()
    overall = "✅ PASS" if report.hard_pass else "❌ FAIL"
    typer.echo(f"总结: {overall} | {report.summary()}")
