"""browse 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..browser import cmd_browse


def register(app: typer.Typer):
    @app.command()
    def browse(category: Optional[str] = typer.Argument(None, help="分类名称")):
        """浏览知识库。"""
        a = A()
        a.category = category
        cmd_browse(a, data_dir())
