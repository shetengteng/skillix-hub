"""kc add — 添加材料到知识库。"""

import shutil
from pathlib import Path
from typing import Optional

import typer

from ..common import find_project_root, load_config


def register(app: typer.Typer) -> None:
    app.command("add")(add_cmd)


def _detect_category(path: Path) -> str:
    """根据文件扩展名和路径推断默认分类。"""
    name_lower = path.name.lower()
    stem_lower = path.stem.lower()

    if any(k in name_lower for k in ("design", "设计")):
        return "designs"
    if any(k in name_lower for k in ("adr", "decision", "决策")):
        return "decisions"
    if any(k in name_lower for k in ("research", "调研", "survey")):
        return "research"
    return "notes"


def add_cmd(
    source: Path = typer.Argument(..., help="要添加的文件或目录"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="逗号分隔的标签"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="目标子目录 (designs/decisions/research/notes)"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="递归添加目录"),
    pattern: str = typer.Option("*.md", "--pattern", "-p", help="递归时的文件匹配模式"),
) -> None:
    """添加文件/目录到知识库的 raw/ 中。"""
    root = find_project_root()
    if root is None:
        typer.echo("错误: 未找到知识库。请先运行 kc init")
        raise typer.Exit(1)

    source = source.resolve()
    if not source.exists():
        typer.echo(f"错误: 路径不存在 {source}")
        raise typer.Exit(1)

    config = load_config(root)
    added = []

    if source.is_file():
        cat = category or _detect_category(source)
        dest_dir = root / "raw" / cat
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / source.name

        if dest.exists():
            typer.echo(f"跳过: {source.name} 已存在于 raw/{cat}/")
        else:
            shutil.copy2(source, dest)
            added.append(f"raw/{cat}/{source.name}")

    elif source.is_dir():
        if not recursive:
            typer.echo("提示: 添加目录请使用 --recursive 参数")
            raise typer.Exit(1)

        cat = category or _detect_category(source)
        dest_dir = root / "raw" / cat
        dest_dir.mkdir(parents=True, exist_ok=True)

        for f in sorted(source.rglob(pattern)):
            if f.is_file():
                rel = f.relative_to(source)
                target = dest_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    typer.echo(f"  跳过: {rel}")
                else:
                    shutil.copy2(f, target)
                    added.append(f"raw/{cat}/{rel}")

    if added:
        typer.echo(f"已添加 {len(added)} 个文件:")
        for f in added:
            typer.echo(f"  + {f}")
        if tags:
            typer.echo(f"标签: {tags}")
        typer.echo()
        typer.echo("运行 kc compile 编译知识库")
    else:
        typer.echo("没有新文件被添加")
