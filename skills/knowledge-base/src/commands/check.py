"""check 命令。"""

import typer
from ._common import A, data_dir
from ..searcher import cmd_check


def register(app: typer.Typer):
    @app.command()
    def check():
        """路径有效性检查。"""
        cmd_check(A(), data_dir())
