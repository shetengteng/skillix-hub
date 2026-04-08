"""list 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..indexer import cmd_list


def register(app: typer.Typer):
    @app.command("list")
    def list_entries(
        type: Optional[str] = typer.Option(None, "--type", help="按类型过滤"),
        tag: Optional[str] = typer.Option(None, help="按标签过滤"),
        category: Optional[str] = typer.Option(None, help="按分类过滤"),
        pending: bool = typer.Option(False, help="只显示待编译条目"),
    ):
        """列出索引。"""
        a = A()
        a.filter_type, a.tag, a.category, a.pending = type, tag, category, pending
        cmd_list(a, data_dir())
