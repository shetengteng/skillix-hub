"""concept 子命令组。"""

import typer
from ._common import A, data_dir
from ..graph import cmd_concept

concept_app = typer.Typer(help="概念管理")


def register(app: typer.Typer):
    app.add_typer(concept_app, name="concept")


@concept_app.command("list")
def concept_list():
    """列出所有概念。"""
    a = A()
    a.action = "list"
    cmd_concept(a, data_dir())


@concept_app.command("remove")
def concept_remove(concept_id: str = typer.Argument(help="概念 ID")):
    """删除概念。"""
    a = A()
    a.action, a.concept_id = "remove", concept_id
    cmd_concept(a, data_dir())


@concept_app.command("merge")
def concept_merge(
    concept_id: str = typer.Argument(help="保留的概念 ID"),
    concept_id2: str = typer.Argument(help="要合并的概念 ID"),
):
    """合并概念。"""
    a = A()
    a.action, a.concept_id, a.concept_id2 = "merge", concept_id, concept_id2
    cmd_concept(a, data_dir())


@concept_app.command("rename")
def concept_rename(
    concept_id: str = typer.Argument(help="概念 ID"),
    new_title: str = typer.Argument(help="新标题"),
):
    """重命名概念。"""
    a = A()
    a.action, a.concept_id, a.new_title = "rename", concept_id, new_title
    cmd_concept(a, data_dir())
