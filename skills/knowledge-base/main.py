#!/usr/bin/env python3
"""Knowledge Base Skill 命令入口。"""

import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.commands import (
    admin, add, list, remove, edit, import_project,
    compile, browse, read, source,
    search, status, check, graph,
    concept, category,
)

app = typer.Typer(help="Knowledge Base Skill — 本地知识资料索引与 Wiki 编译")

for mod in [
    admin, add, list, remove, edit, import_project,
    compile, browse, read, source,
    search, status, check, graph,
    concept, category,
]:
    mod.register(app)

if __name__ == "__main__":
    app()
