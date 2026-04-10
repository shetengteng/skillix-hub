#!/usr/bin/env python3
"""Knowledge Compiler — CLI 入口。"""

import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.commands import init, add, compile, query, lint, status, browse

app = typer.Typer(help="Knowledge Compiler — 将团队知识编译为结构化 Wiki")

for mod in [init, add, compile, query, lint, status, browse]:
    mod.register(app)

if __name__ == "__main__":
    app()
