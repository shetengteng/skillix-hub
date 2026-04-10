"""Phase 3: Compile — 内容编译。

读取概念所有来源全文，生成/更新概念文章。
标记覆盖度，标注来源引用，保留用户手动编辑。

编译策略：
- 生成一个包含所有来源信息的 prompt 文本
- 输出 prompt 供 AI Agent 执行实际的概念合成
- 这保留了 llm-wiki 的"AI 驱动编译"设计本质
"""

import re
from datetime import date
from pathlib import Path

import yaml

from .common import read_template


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 Markdown frontmatter，返回 (metadata, body)。"""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end < 0:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()
    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, body


def _render_frontmatter(meta: dict) -> str:
    """渲染 YAML frontmatter。"""
    lines = ["---"]
    for key in ["id", "title", "tags", "sources", "relations", "created", "updated", "compile_count"]:
        if key in meta:
            val = meta[key]
            if isinstance(val, list):
                if val:
                    lines.append(f"{key}:")
                    for item in val:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: []")
            elif isinstance(val, dict):
                lines.append(f"{key}:")
                for k, v in val.items():
                    if isinstance(v, list):
                        if v:
                            lines.append(f"  {k}:")
                            for item in v:
                                lines.append(f"    - {item}")
                        else:
                            lines.append(f"  {k}: []")
                    else:
                        lines.append(f"  {k}: {v}")
            else:
                lines.append(f'{key}: "{val}"' if isinstance(val, str) else f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines)


def generate_compile_prompt(
    slug: str,
    source_files: list[Path],
    root: Path,
    existing_article: str | None = None,
) -> str:
    """生成编译 prompt，供 AI Agent 执行概念合成。

    返回一个结构化的 prompt 字符串，包含：
    - 所有来源文件的全文
    - 目标概念文章模板
    - 编译指令（覆盖度标记规则等）
    """
    sources_text = []
    source_paths = []
    for f in source_files:
        rel = str(f.relative_to(root))
        source_paths.append(rel)
        content = f.read_text(encoding="utf-8")
        sources_text.append(f"### Source: {rel}\n\n{content}")

    all_sources = "\n\n---\n\n".join(sources_text)

    today = date.today().isoformat()
    template = read_template("article.md")
    template = template.replace("{{topic-slug}}", slug)
    template = template.replace("{{Topic Title}}", slug.replace("-", " ").title())
    template = template.replace("{{YYYY-MM-DD}}", today)

    existing_note = ""
    if existing_article:
        existing_note = f"""
## 已有文章内容（需保留用户手动编辑）

```markdown
{existing_article}
```

重要：如果已有文章中存在没有 [source: ...] 标注的段落，这些是用户手动添加的内容，必须保留。
只更新有 [source: ...] 标注的编译器生成内容。
"""

    prompt = f"""# 概念编译任务

## 目标概念: {slug}

## 来源文件 ({len(source_files)} 个)

{all_sources}

{existing_note}

## 编译指令

基于以上来源文件，生成或更新概念文章 `wiki/concepts/{slug}.md`。

### 格式要求
使用以下模板结构（YAML frontmatter + Markdown 正文）：

```markdown
{template}
```

### 覆盖度标记规则
为每个 Section 标记覆盖度（放在 Section 标题下一行）：
- `<!-- coverage: high -->` — 多个来源对此内容有一致描述
- `<!-- coverage: medium -->` — 仅一个来源覆盖，或覆盖不完整
- `<!-- coverage: low -->` — 由编译器推断，来源中无直接论述

### 来源引用
在引用具体信息时标注来源：`[source: {source_paths[0] if source_paths else 'raw/path/to/file.md'}]`

### 来源矛盾处理
如果多个来源对同一主题存在矛盾描述（如不同的技术选型、不一致的架构决策），请：
- 在对应 Section 中标注 `⚠️ 来源冲突`，并列出矛盾的各方观点和来源
- 将该 Section 的 coverage 标记为 `medium`（而非 high），表示需要人工确认

### frontmatter 要求
- id: "{slug}"
- sources: {source_paths}
- created: "{today}"
- updated: "{today}"
- compile_count: 1（如果是更新，在已有值上 +1）

请直接输出完整的概念文章内容（包含 frontmatter），不要输出其他说明。
"""
    return prompt


def create_stub_article(
    slug: str,
    source_files: list[Path],
    root: Path,
    existing_content: str | None = None,
) -> str:
    """创建一个骨架概念文章（当 AI 编译不可用时的 fallback）。

    如果 existing_content 非空，保留原始 created 日期并递增 compile_count。
    """
    today = date.today().isoformat()
    source_paths = [str(f.relative_to(root)) for f in source_files]

    old_meta: dict = {}
    if existing_content:
        old_meta, _ = _parse_frontmatter(existing_content)

    meta = {
        "id": slug,
        "title": old_meta.get("title", slug.replace("-", " ").title()),
        "tags": old_meta.get("tags", []),
        "sources": source_paths,
        "relations": old_meta.get("relations", {"related": [], "depends_on": []}),
        "created": old_meta.get("created", today),
        "updated": today,
        "compile_count": old_meta.get("compile_count", 0) + 1,
    }

    fm = _render_frontmatter(meta)
    title = meta["title"]

    source_refs = "\n".join(f"- [source: {s}]" for s in source_paths)

    previews = []
    for f in source_files:
        content = f.read_text(encoding="utf-8")
        _, body = _parse_frontmatter(content)
        preview = body[:200].strip()
        rel = str(f.relative_to(root))
        previews.append(f"来自 {rel}：{preview}...")

    preview_text = "\n\n".join(previews) if previews else "待编译。"

    body = f"""
# {title}

> 待 AI 编译完善。

## Summary
<!-- coverage: low -->

{preview_text}

## Key Decisions
<!-- coverage: low -->

待编译。

## Current State
<!-- coverage: low -->

待编译。

## Gotchas
<!-- coverage: low -->

待编译。

## Open Questions
<!-- coverage: low -->

待编译。

## Related

## Sources
{source_refs}
"""
    return fm + "\n" + body
