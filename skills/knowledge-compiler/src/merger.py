"""Section-level merge — 编译器生成内容与用户手工编辑的合并策略。

核心规则：
- 含 [source: ...] 标注的 section 视为"编译器生成"，重编译可更新
- 不含 [source: ...] 且有实质内容的 section 视为"用户手工编辑"，保留不动
- ## Related 和 ## Sources 是自动管理的 section
- 用户在编译器生成 section 中添加的无 [source:] 段落也会被保留
"""

import re
from dataclasses import dataclass, field


SOURCE_REF_PATTERN = re.compile(r"\[source:\s*[^\]]+\]")
SECTION_SPLIT_PATTERN = re.compile(r"^(## .+)$", re.MULTILINE)
AUTO_MANAGED_SECTIONS = {"## Related", "## Sources"}


@dataclass
class Section:
    heading: str
    body: str
    is_compiler_generated: bool = False
    is_auto_managed: bool = False

    @property
    def has_content(self) -> bool:
        text = re.sub(r"<!--.*?-->", "", self.body).strip()
        return bool(text) and text not in ("待编译。",)


def parse_sections(body: str) -> list[Section]:
    """将文章正文拆分为 Section 列表。

    第一个 section 是标题区域（# 标题 + 引用摘要），heading 为空。
    """
    parts = SECTION_SPLIT_PATTERN.split(body)
    sections: list[Section] = []

    if parts and parts[0].strip():
        sections.append(Section(heading="", body=parts[0].strip()))

    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        section_body = parts[i + 1] if i + 1 < len(parts) else ""

        has_source_ref = bool(SOURCE_REF_PATTERN.search(section_body))
        is_auto = heading in AUTO_MANAGED_SECTIONS

        sections.append(Section(
            heading=heading,
            body=section_body,
            is_compiler_generated=has_source_ref,
            is_auto_managed=is_auto,
        ))
        i += 2

    if len(parts) > 1 and len(parts) % 2 == 0:
        last = parts[-1]
        if last.strip():
            sections.append(Section(heading="", body=last.strip()))

    return sections


def merge_sections(old_sections: list[Section], new_sections: list[Section]) -> list[Section]:
    """合并旧文章和新编译结果的 section。

    策略：
    - 用户手工 section：保留旧版
    - 编译器生成 section：用新版替换，但保留旧版中无 [source:] 的段落
    - 自动管理 section (Related/Sources)：用新版替换
    - 新文章独有的 section：追加
    - 旧文章独有的用户 section：保留
    """
    old_map = {s.heading: s for s in old_sections if s.heading}
    new_map = {s.heading: s for s in new_sections if s.heading}

    all_headings = []
    seen = set()
    for s in new_sections:
        if s.heading and s.heading not in seen:
            all_headings.append(s.heading)
            seen.add(s.heading)
    for s in old_sections:
        if s.heading and s.heading not in seen:
            all_headings.append(s.heading)
            seen.add(s.heading)

    merged: list[Section] = []

    header = next((s for s in new_sections if not s.heading), None)
    if not header:
        header = next((s for s in old_sections if not s.heading), None)
    if header:
        merged.append(header)

    for heading in all_headings:
        old_sec = old_map.get(heading)
        new_sec = new_map.get(heading)

        if old_sec and new_sec:
            if old_sec.is_auto_managed or new_sec.is_auto_managed:
                merged.append(new_sec)
            elif not old_sec.is_compiler_generated and old_sec.has_content:
                merged.append(old_sec)
            elif old_sec.is_compiler_generated and new_sec.is_compiler_generated:
                user_paras = _extract_user_paragraphs(old_sec.body)
                if user_paras:
                    combined_body = new_sec.body.rstrip() + "\n\n" + user_paras + "\n"
                    merged.append(Section(
                        heading=heading,
                        body=combined_body,
                        is_compiler_generated=True,
                    ))
                else:
                    merged.append(new_sec)
            else:
                merged.append(new_sec)
        elif old_sec and not new_sec:
            merged.append(old_sec)
        elif new_sec and not old_sec:
            merged.append(new_sec)

    return merged


def render_sections(sections: list[Section]) -> str:
    """将 Section 列表渲染回 Markdown 正文。"""
    parts = []
    for s in sections:
        if s.heading:
            parts.append(f"{s.heading}\n{s.body}")
        else:
            parts.append(s.body)
    return "\n".join(parts)


def generate_related_section(related_slugs: list[str]) -> str:
    """基于 frontmatter relations.related 生成 ## Related 正文。"""
    if not related_slugs:
        return ""
    links = "\n".join(f"- [[{slug}]]" for slug in sorted(related_slugs))
    return f"\n{links}\n"


def _extract_user_paragraphs(section_body: str) -> str:
    """从编译器生成的 section 中提取用户手工添加的段落（无 [source:] 标注）。"""
    paragraphs = re.split(r"\n\n+", section_body)
    user_paras = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para.startswith("<!-- coverage:"):
            continue
        if SOURCE_REF_PATTERN.search(para):
            continue
        if para in ("待编译。",):
            continue
        user_paras.append(para)
    return "\n\n".join(user_paras)
