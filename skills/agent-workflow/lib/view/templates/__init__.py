"""SPA 模板存放点。

这里只放静态文件（index.html / workflow.html / CSS / JS），
view 命令的 ``_install_static`` 会把它们拷到 ``.agent-workflow/views/``。
数据渲染全部由浏览器侧 JS 完成；Python 端不再做 HTML 模板替换。
"""
from __future__ import annotations

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent

__all__ = ["TEMPLATES_DIR"]
