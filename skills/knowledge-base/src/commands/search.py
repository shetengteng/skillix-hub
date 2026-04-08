"""search 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..searcher import cmd_search


def register(app: typer.Typer):
    @app.command()
    def search(
        query: str = typer.Argument("", help="搜索关键词"),
        tag: Optional[str] = typer.Option(None, "--tag", help="按标签搜索"),
        category: Optional[str] = typer.Option(None, "--category", help="按分类筛选"),
    ):
        """搜索知识库。"""
        a = A()
        a.query, a.search_tag, a.search_category = query, tag, category
        cmd_search(a, data_dir())
