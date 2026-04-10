"""kc query — 基于 Wiki 回答问题。

读取 INDEX.md 定位相关概念，读取概念文章，
low 覆盖章节自动回查 raw/ 来源，合成回答 + 引用。

支持 --save 将查询结果落盘为新概念文章。
"""

import re
from datetime import date
from pathlib import Path
from typing import Optional

import typer

from ..common import find_project_root
from ..compiler import _parse_frontmatter, _render_frontmatter
from ..classifier import _title_to_slug
from ..schema import load_schema, update_schema
from ..indexer import update_index


def register(app: typer.Typer) -> None:
    app.command("query")(query_cmd)


def _load_all_concepts(root: Path) -> list[dict]:
    """加载所有概念文章的元数据和内容。"""
    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists():
        return []

    concepts = []
    for f in sorted(concepts_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)
        concepts.append({
            "slug": f.stem,
            "title": meta.get("title", f.stem),
            "tags": meta.get("tags", []),
            "sources": meta.get("sources", []),
            "body": body,
            "meta": meta,
            "path": f,
        })
    return concepts


def _score_relevance(question: str, concept: dict) -> int:
    """简单关键词匹配打分。"""
    q_lower = question.lower()
    words = re.findall(r"\w+", q_lower)

    score = 0
    title_lower = concept["title"].lower()
    slug_lower = concept["slug"].lower()
    body_lower = concept["body"][:2000].lower()
    tags_lower = " ".join(str(t) for t in concept["tags"]).lower()

    for w in words:
        if len(w) < 2:
            continue
        if w in title_lower:
            score += 10
        if w in slug_lower:
            score += 8
        if w in tags_lower:
            score += 5
        if w in body_lower:
            score += 2

    return score


def _extract_low_coverage_sections(body: str) -> list[str]:
    """提取覆盖度为 low 的 section 标题。"""
    sections = []
    lines = body.split("\n")
    current_section = None
    for line in lines:
        if line.startswith("## "):
            current_section = line[3:].strip()
        elif "<!-- coverage: low -->" in line and current_section:
            sections.append(current_section)
    return sections


def _save_query_concept(
    question: str,
    relevant: list[dict],
    root: Path,
) -> None:
    """将查询结果落盘为新概念文章到 wiki/concepts/。"""
    slug = _title_to_slug(question)
    concepts_dir = root / "wiki" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    target = concepts_dir / f"{slug}.md"
    if target.exists():
        typer.echo(f"概念 {slug} 已存在，跳过保存。使用 kc compile 更新已有概念。")
        return

    today = date.today().isoformat()
    source_concepts = [c["slug"] for c in relevant]

    meta = {
        "id": slug,
        "title": question,
        "tags": [],
        "sources": [],
        "relations": {"related": source_concepts, "depends_on": []},
        "created": today,
        "updated": today,
        "compile_count": 0,
    }
    fm = _render_frontmatter(meta)

    summaries = []
    for c in relevant:
        preview = c["body"][:500].replace("\n", " ").strip()
        summaries.append(f"### {c['title']}\n\n{preview}...")

    body = f"""
# {question}

> 由 kc query --save 自动生成，待 AI 编译完善。

## Summary
<!-- coverage: low -->

基于以下 {len(relevant)} 个相关概念汇总：

{chr(10).join(summaries)}

## Key Decisions
<!-- coverage: low -->

待编译。

## Related

{chr(10).join(f'- [[{s}]]' for s in source_concepts)}

## Sources

无直接来源文件。由查询结果合成。
"""
    content = fm + "\n" + body
    target.write_text(content, encoding="utf-8")
    typer.echo(f"✅ 新概念已保存: wiki/concepts/{slug}.md")
    typer.echo(f"   关联概念: {', '.join(source_concepts)}")
    typer.echo("   建议运行 kc compile 完善内容。")


def _build_query_prompt(
    question: str,
    relevant_concepts: list[dict],
    root: Path,
) -> str:
    """生成查询 prompt，供 AI Agent 执行回答合成。"""
    parts = [
        f"# 知识库查询\n\n## 问题\n{question}\n",
        f"## 相关概念 ({len(relevant_concepts)} 个)\n",
    ]

    for c in relevant_concepts:
        parts.append(f"### {c['title']} (`{c['slug']}`)\n")
        parts.append(c["body"][:3000])

        low_sections = _extract_low_coverage_sections(c["body"])
        if low_sections:
            parts.append(f"\n⚠️ 以下章节覆盖度为 low，建议回查原始来源: {', '.join(low_sections)}")

            for src in c["sources"][:3]:
                src_path = root / src
                if src_path.exists():
                    src_content = src_path.read_text(encoding="utf-8")[:2000]
                    parts.append(f"\n#### 来源补充: {src}\n{src_content}")

        parts.append("\n---\n")

    parts.append("""
## 回答要求

1. 基于上述概念文章内容回答问题
2. 引用来源：使用 `[source: path]` 标注
3. 标注覆盖度：如果答案主要来自 low 覆盖内容，注明"此信息覆盖度较低，建议确认"
4. 如果知识库中没有足够信息回答，明确说明
""")

    return "\n".join(parts)


def query_cmd(
    question: str = typer.Argument(..., help="要查询的问题"),
    save: bool = typer.Option(False, "--save", help="将回答保存为新概念文章"),
    top_k: int = typer.Option(5, "--top", help="最多返回的相关概念数"),
) -> None:
    """基于 Wiki 回答问题。"""
    root = find_project_root()
    if root is None:
        typer.echo("错误: 未找到知识库。请先运行 kc init")
        raise typer.Exit(1)

    concepts = _load_all_concepts(root)
    if not concepts:
        typer.echo("知识库为空，请先添加材料并编译。")
        raise typer.Exit(1)

    scored = [(c, _score_relevance(question, c)) for c in concepts]
    scored.sort(key=lambda x: x[1], reverse=True)

    relevant = [c for c, s in scored[:top_k] if s > 0]
    if not relevant:
        typer.echo("未找到相关概念。尝试更具体的关键词。")
        raise typer.Exit(1)

    typer.echo(f"找到 {len(relevant)} 个相关概念:")
    for c in relevant:
        typer.echo(f"  - {c['title']} ({c['slug']})")

    prompt = _build_query_prompt(question, relevant, root)

    prompt_path = root / ".kc-query-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    typer.echo(f"\n查询 prompt 已保存到 .kc-query-prompt.md")

    if save:
        _save_query_concept(question, relevant, root)
        slug = _title_to_slug(question)
        schema = load_schema(root)
        update_schema(root, [slug], schema)
        update_index(root)
        typer.echo("  schema + INDEX.md 已同步")

    typer.echo("\n--- 概念摘要 ---\n")
    for c in relevant:
        body_preview = c["body"][:300].replace("\n", " ")
        typer.echo(f"## {c['title']}")
        typer.echo(f"{body_preview}...")
        low_sections = _extract_low_coverage_sections(c["body"])
        if low_sections:
            typer.echo(f"  ⚠️ low 覆盖: {', '.join(low_sections)}")
        typer.echo()
