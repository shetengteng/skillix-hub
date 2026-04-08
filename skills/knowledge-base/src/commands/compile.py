"""compile 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..compiler import cmd_compile


def register(app: typer.Typer):
    @app.command()
    def compile(
        full: bool = typer.Option(False, help="全量重新编译"),
        dry_run: bool = typer.Option(False, "--dry-run", help="预览待编译清单"),
        finalize: bool = typer.Option(False, help="编译后处理"),
        id: Optional[str] = typer.Option(None, "--id", help="编译指定条目"),
    ):
        """编译 Wiki。"""
        a = A()
        a.full, a.dry_run, a.finalize, a.target_id = full, dry_run, finalize, id
        cmd_compile(a, data_dir())
