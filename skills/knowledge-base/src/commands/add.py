"""add 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..indexer import cmd_add


def register(app: typer.Typer):
    @app.command()
    def add(
        path: str = typer.Argument(help="资料路径（文件或目录）"),
        title: Optional[str] = typer.Option(None, help="标题（默认从文件提取）"),
        tags: Optional[str] = typer.Option(None, help="标签，逗号分隔"),
        type: Optional[str] = typer.Option(None, "--type", help="资料类型"),
        category: Optional[str] = typer.Option(None, help="分类（默认从路径推断）"),
        pattern: Optional[str] = typer.Option(None, help="目录匹配模式"),
        recursive: bool = typer.Option(False, help="递归扫描目录"),
    ):
        """添加资料索引。"""
        a = A()
        a.path, a.title, a.tags = path, title, tags
        a.entry_type, a.category = type, category
        a.pattern, a.recursive = pattern, recursive
        cmd_add(a, data_dir())
