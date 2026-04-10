#!/usr/bin/env python3
"""Knowledge Compiler — CLI 入口。"""

import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.commands import init, add, compile

app = typer.Typer(help="Knowledge Compiler — 将团队知识编译为结构化 Wiki")

for mod in [init, add, compile]:
    mod.register(app)

if __name__ == "__main__":
    app()
