"""graph 命令。"""

from typing import Optional
import typer
from ._common import A, data_dir
from ..graph import cmd_graph


def register(app: typer.Typer):
    @app.command()
    def graph(
        format: str = typer.Option("json", help="输出格式: json/mermaid"),
        center: Optional[str] = typer.Option(None, help="以某概念为中心"),
        depth: int = typer.Option(2, help="子图深度"),
    ):
        """知识图谱。"""
        a = A()
        a.format, a.center, a.depth = format, center, depth
        cmd_graph(a, data_dir())
