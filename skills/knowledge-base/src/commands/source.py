"""source 命令。"""

import typer
from ._common import A, data_dir
from ..browser import cmd_source


def register(app: typer.Typer):
    @app.command()
    def source(id: str = typer.Argument(help="资料 ID")):
        """查看原始资料。"""
        a = A()
        a.id = id
        cmd_source(a, data_dir())
