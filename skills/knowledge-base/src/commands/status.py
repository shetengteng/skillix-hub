"""status 命令。"""

import typer
from ._common import A, data_dir
from ..searcher import cmd_status


def register(app: typer.Typer):
    @app.command()
    def status():
        """知识库健康状态。"""
        cmd_status(A(), data_dir())
