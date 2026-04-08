"""edit 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..indexer import cmd_edit


def register(app: typer.Typer):
    @app.command()
    def edit(
        id: str = typer.Argument(help="条目 ID"),
        title: Optional[str] = typer.Option(None, help="新标题"),
        tags: Optional[str] = typer.Option(None, help="新标签"),
        category: Optional[str] = typer.Option(None, help="新分类"),
    ):
        """更新索引元数据。"""
        a = A()
        a.id, a.title, a.tags, a.category = id, title, tags, category
        cmd_edit(a, data_dir())
