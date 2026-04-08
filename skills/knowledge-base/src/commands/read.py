"""read 命令。"""

import typer
from ._common import A, data_dir
from ..browser import cmd_read


def register(app: typer.Typer):
    @app.command()
    def read(id: str = typer.Argument(help="概念 ID")):
        """读取概念条目。"""
        a = A()
        a.id = id
        cmd_read(a, data_dir())
