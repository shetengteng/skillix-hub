"""模板加载器：把 templates/ 下的文件读出来，提供轻量 substitute API。

设计取舍：
    - 使用标准库 ``string.Template`` ($var 语法)，零外部依赖
    - 文件级 LRU cache，开发期无感知；测试期可显式 ``clear_cache()``
    - 复杂结构（节点列表 / 行循环）由 Python 端逐条 render 后拼接，
      模板只负责"骨架填空"
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parent
FRAGMENTS_DIR = TEMPLATES_DIR / "fragments"


@lru_cache(maxsize=64)
def load(name: str) -> str:
    """读取模板文件原文。

    name 支持：
        - ``"base.css"`` / ``"run.html"`` 等顶层文件
        - ``"fragments/node_row.html"`` 子目录文件
    """
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"template not found: {name} (resolved: {path})")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=64)
def template(name: str) -> Template:
    """读取并构造 ``string.Template`` 对象。"""
    return Template(load(name))


def render(name: str, /, **kwargs: object) -> str:
    """加载模板并用 ``safe_substitute`` 渲染。

    使用 ``safe_substitute`` 而非 ``substitute``：缺失的占位符保留原样
    （便于排查），不会因为 KeyError 中断渲染。
    """
    return template(name).safe_substitute(**kwargs)


def render_fragment(name: str, /, **kwargs: object) -> str:
    """渲染 fragments/ 下的片段。"""
    return render(f"fragments/{name}", **kwargs)


def clear_cache() -> None:
    """开发/测试期手动清缓存。"""
    load.cache_clear()
    template.cache_clear()


__all__ = ["load", "template", "render", "render_fragment", "clear_cache", "TEMPLATES_DIR"]
