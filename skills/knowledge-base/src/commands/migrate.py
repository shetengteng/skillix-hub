"""migrate 命令：批量修复索引中的路径。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..indexer import cmd_migrate


def register(app: typer.Typer):
    @app.command()
    def migrate(
        old_base: Optional[str] = typer.Option(None, "--old-base", help="旧的项目根路径"),
        new_base: Optional[str] = typer.Option(None, "--new-base", help="新的项目根路径"),
        to_relative: bool = typer.Option(False, "--to-relative", help="将绝对路径转为相对路径"),
        dry_run: bool = typer.Option(False, "--dry-run", help="预览变更，不实际执行"),
    ):
        """批量修复索引中的路径。"""
        a = A()
        a.old_base, a.new_base = old_base, new_base
        a.to_relative, a.dry_run = to_relative, dry_run
        cmd_migrate(a, data_dir())
