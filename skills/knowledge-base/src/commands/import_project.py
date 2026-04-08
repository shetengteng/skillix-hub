"""import-project 命令。"""

import typer
from ._common import A, SKILL_DIR, data_dir
from ..indexer import cmd_import_project


def register(app: typer.Typer):
    @app.command("import-project")
    def import_project(
        dir: str = typer.Option("design", help="要导入的目录名"),
        pattern: str = typer.Option("*.md", help="文件匹配模式"),
    ):
        """快捷导入项目 design/ 目录。"""
        a = A()
        a.dir, a.pattern = dir, pattern
        cmd_import_project(a, data_dir(), SKILL_DIR)
