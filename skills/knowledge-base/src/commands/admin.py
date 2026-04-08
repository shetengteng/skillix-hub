"""skill-store 协议命令：install / update / uninstall。"""

from pathlib import Path
from typing import Optional

import typer

from ._common import SKILL_DIR, ensure_data_dirs, copy_source


def register(app: typer.Typer):
    @app.command()
    def install(target: Optional[str] = typer.Option(None, help="安装目标路径")):
        """安装初始化。"""
        t = Path(target).resolve() if target else SKILL_DIR
        dd = t.parent / "knowledge-base-data"
        ensure_data_dirs(dd)
        if target and t.resolve() != SKILL_DIR.resolve():
            copy_source(SKILL_DIR, t)
        typer.echo(f"✅ Knowledge Base Skill 安装完成")
        typer.echo(f"   Skill 路径: {t}")
        typer.echo(f"   数据目录: {dd}")

    @app.command()
    def update(target: Optional[str] = typer.Option(None, help="更新目标路径")):
        """更新代码。"""
        t = Path(target).resolve() if target else SKILL_DIR
        if target and t.resolve() != SKILL_DIR.resolve():
            copy_source(SKILL_DIR, t)
        dd = t.parent / "knowledge-base-data"
        ensure_data_dirs(dd)
        typer.echo(f"✅ Knowledge Base Skill 更新完成")
        typer.echo(f"   Skill 路径: {t}")

    @app.command()
    def uninstall():
        """卸载。"""
        typer.echo("⚠ Knowledge Base Skill 已标记为卸载")
        typer.echo("  数据目录需手动删除: knowledge-base-data/")
