"""remove 命令。"""

import typer
from ._common import A, data_dir
from ..indexer import cmd_remove


def register(app: typer.Typer):
    @app.command()
    def remove(id: str = typer.Argument(help="条目 ID")):
        """移除索引条目。"""
        a = A()
        a.id = id
        cmd_remove(a, data_dir())
