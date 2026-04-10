"""Session Injector — 自动上下文注入。

功能：
- 向上查找 .kc-config.json 定位知识库
- 根据 session_mode 注入上下文到 AI Agent
- 支持 staging / recommended / primary 三种模式

staging: Wiki 可用，按需查阅
recommended: 先读 Wiki 再读原始文件
primary: Wiki 为主，low 覆盖才看 raw/
"""

import json
from pathlib import Path

from ..compiler import _parse_frontmatter


def find_kb_root(start: Path | None = None) -> Path | None:
    """向上查找 .kc-config.json，返回知识库根目录。"""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".kc-config.json").exists():
            return parent
    return None


def load_session_mode(root: Path) -> str:
    """读取 session_mode 配置。"""
    config_path = root / ".kc-config.json"
    if not config_path.exists():
        return "staging"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        return config.get("session_mode", "staging")
    except (json.JSONDecodeError, KeyError):
        return "staging"


def generate_context(root: Path) -> str | None:
    """根据 session_mode 生成注入上下文。

    返回适合作为系统消息注入的字符串，或 None（无知识库时）。
    """
    mode = load_session_mode(root)

    index_path = root / "wiki" / "INDEX.md"
    if not index_path.exists():
        return None

    index_content = index_path.read_text(encoding="utf-8")

    concepts_dir = root / "wiki" / "concepts"
    concept_count = len(list(concepts_dir.glob("*.md"))) if concepts_dir.exists() else 0

    if concept_count == 0:
        return None

    lines = [
        "# Knowledge Base Context",
        "",
        f"Mode: {mode}",
        f"Location: {root}",
        f"Concepts: {concept_count}",
        "",
    ]

    if mode == "staging":
        lines.extend([
            "知识库已就绪，可按需查阅。",
            "使用 `kc query <question>` 查询知识库。",
            "",
            "## 知识库索引",
            "",
            index_content,
        ])
    elif mode == "recommended":
        lines.extend([
            "建议优先参考知识库中的信息。",
            "回答问题前，先查阅相关概念文章。",
            "",
            "## 知识库索引",
            "",
            index_content,
            "",
            _get_concept_summaries(root, max_concepts=10),
        ])
    elif mode == "primary":
        lines.extend([
            "知识库为主要信息源。",
            "仅当概念覆盖度为 low 时，才需要回查 raw/ 原始文件。",
            "",
            "## 知识库索引",
            "",
            index_content,
            "",
            _get_concept_summaries(root, max_concepts=20),
        ])

    return "\n".join(lines)


def _get_concept_summaries(root: Path, max_concepts: int = 10) -> str:
    """获取概念文章摘要。"""
    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists():
        return ""

    lines = ["## 概念摘要", ""]
    for i, f in enumerate(sorted(concepts_dir.glob("*.md"))):
        if i >= max_concepts:
            remaining = len(list(concepts_dir.glob("*.md"))) - max_concepts
            lines.append(f"\n... 还有 {remaining} 个概念，使用 `kc query` 查询")
            break

        content = f.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)
        title = meta.get("title", f.stem)
        preview = body[:200].replace("\n", " ").strip()
        lines.append(f"### {title}")
        lines.append(f"{preview}...")
        lines.append("")

    return "\n".join(lines)


def inject_hook_output() -> None:
    """Cursor hook 入口：检测知识库并输出注入上下文。

    供 Cursor session-start hook 调用。
    静默失败：无知识库时不输出任何内容。
    """
    root = find_kb_root()
    if root is None:
        return

    context = generate_context(root)
    if context:
        print(context)
