"""category 子命令组。"""

import typer
from ._common import A, data_dir
from ..graph import cmd_category

category_app = typer.Typer(help="分类管理")


def register(app: typer.Typer):
    app.add_typer(category_app, name="category")


@category_app.command("list")
def category_list():
    """列出所有分类。"""
    a = A()
    a.action = "list"
    cmd_category(a, data_dir())


@category_app.command("rename")
def category_rename(
    old_name: str = typer.Argument(help="旧名称"),
    new_name: str = typer.Argument(help="新名称"),
):
    """重命名分类。"""
    a = A()
    a.action, a.old_name, a.new_name = "rename", old_name, new_name
    cmd_category(a, data_dir())
