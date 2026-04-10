"""kc init — 初始化知识库。"""

from datetime import date
from pathlib import Path

import typer

from ..common import (
    CONFIG_FILENAME, DEFAULT_CONFIG, save_config, read_template,
)

import json


def register(app: typer.Typer) -> None:
    app.command("init")(init_cmd)


def init_cmd(
    target: Path = typer.Argument(Path("."), help="目标目录，默认当前目录"),
) -> None:
    """初始化知识库，创建 raw/ + wiki/ + 配置。"""
    root = target.resolve()

    if (root / CONFIG_FILENAME).exists():
        typer.echo(f"知识库已存在于 {root}")
        raise typer.Exit(1)

    raw_dirs = ["designs", "decisions", "research", "notes", "assets"]
    for d in raw_dirs:
        (root / "raw" / d).mkdir(parents=True, exist_ok=True)

    wiki_dir = root / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    (wiki_dir / "concepts").mkdir(exist_ok=True)

    default_cfg = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    save_config(root, default_cfg)

    today = date.today().isoformat()

    index_tpl = read_template("index.md")
    index_content = index_tpl.replace("{{YYYY-MM-DD}}", today)
    (wiki_dir / "INDEX.md").write_text(index_content, encoding="utf-8")

    schema_tpl = read_template("schema.md")
    schema_content = schema_tpl.replace("{{YYYY-MM-DD}}", today)
    (wiki_dir / "schema.md").write_text(schema_content, encoding="utf-8")

    (wiki_dir / "log.md").write_text("# Compile Log\n", encoding="utf-8")

    typer.echo(f"知识库已初始化于 {root}")
    typer.echo()
    typer.echo("目录结构:")
    typer.echo("  raw/designs/    — 设计文档")
    typer.echo("  raw/decisions/  — 架构决策")
    typer.echo("  raw/research/   — 技术调研")
    typer.echo("  raw/notes/      — 会议纪要、笔记")
    typer.echo("  raw/assets/     — 图片等（排除编译）")
    typer.echo("  wiki/           — 编译产物")
    typer.echo()
    typer.echo("下一步: 添加材料到 raw/，然后运行 kc compile")
