"""Phase 3.5: Schema — 读取和维护 wiki/schema.md。

schema.md 是知识库的结构契约：
- Topic Taxonomy：定义分类及其包含的主题
- Naming Conventions：slug 命名规则
- Cross-Reference Rules：交叉引用规则
- Deprecated Topics：已废弃主题

编译器读取 schema 作为输入约束，同时增量更新新发现的主题。
用户手动编辑优先保留。
"""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class Schema:
    taxonomy: dict[str, list[str]] = field(default_factory=dict)
    deprecated: dict[str, str] = field(default_factory=dict)
    cross_refs: list[tuple[str, str]] = field(default_factory=list)
    raw_content: str = ""

    @property
    def all_known_slugs(self) -> set[str]:
        slugs: set[str] = set()
        for topics in self.taxonomy.values():
            slugs.update(topics)
        return slugs

    def find_category(self, slug: str) -> str | None:
        for cat, topics in self.taxonomy.items():
            if slug in topics:
                return cat
        return None

    def is_deprecated(self, slug: str) -> bool:
        return slug in self.deprecated


def load_schema(root: Path) -> Schema:
    """从 wiki/schema.md 解析 Schema。"""
    schema_path = root / "wiki" / "schema.md"
    if not schema_path.exists():
        return Schema()

    content = schema_path.read_text(encoding="utf-8")
    schema = Schema(raw_content=content)

    taxonomy = _parse_taxonomy(content)
    schema.taxonomy = taxonomy

    deprecated = _parse_deprecated(content)
    schema.deprecated = deprecated

    cross_refs = _parse_cross_refs(content)
    schema.cross_refs = cross_refs

    return schema


def _parse_taxonomy(content: str) -> dict[str, list[str]]:
    """解析 Topic Taxonomy 部分。

    格式：
    ### Category Name
    - topic-slug-1
    - topic-slug-2
    """
    taxonomy: dict[str, list[str]] = {}
    in_taxonomy = False
    current_category: str | None = None

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped == "## Topic Taxonomy":
            in_taxonomy = True
            continue

        if in_taxonomy and stripped.startswith("## ") and not stripped.startswith("### "):
            break

        if not in_taxonomy:
            continue

        if stripped.startswith("### "):
            current_category = stripped[4:].strip()
            if current_category not in taxonomy:
                taxonomy[current_category] = []
        elif stripped.startswith("- ") and current_category:
            slug = stripped[2:].strip()
            slug = re.sub(r"\s*<!--.*?-->", "", slug).strip()
            if slug:
                taxonomy[current_category].append(slug)

    return taxonomy


def _parse_deprecated(content: str) -> dict[str, str]:
    """解析 Deprecated Topics 表格。返回 {old_slug: merged_into}。"""
    deprecated: dict[str, str] = {}
    in_deprecated = False
    header_passed = False

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped == "## Deprecated Topics":
            in_deprecated = True
            continue

        if in_deprecated and stripped.startswith("## "):
            break

        if not in_deprecated:
            continue

        if stripped.startswith("|") and "---" in stripped:
            header_passed = True
            continue

        if header_passed and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")]
            cols = [c for c in cols if c]
            if len(cols) >= 2 and cols[0] and cols[1]:
                deprecated[cols[0]] = cols[1]

    return deprecated


def _parse_cross_refs(content: str) -> list[tuple[str, str]]:
    """解析 Cross-Reference Rules，返回 [(slug_a, slug_b)]。"""
    refs: list[tuple[str, str]] = []
    in_xref = False

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped == "## Cross-Reference Rules":
            in_xref = True
            continue

        if in_xref and stripped.startswith("## "):
            break

        if not in_xref:
            continue

        match = re.match(r"(\S+)\s*<->\s*(\S+)", stripped)
        if match:
            refs.append((match.group(1), match.group(2)))

    return refs


def update_schema(root: Path, topic_slugs: list[str], schema: Schema) -> None:
    """增量更新 schema.md，将新主题添加到 Uncategorized 分类。

    只添加未出现在任何分类中且未被废弃的新主题。
    保留用户手动编辑的内容。
    """
    known = schema.all_known_slugs
    new_slugs = [s for s in topic_slugs if s not in known and not schema.is_deprecated(s)]
    if not new_slugs:
        return

    schema_path = root / "wiki" / "schema.md"
    content = schema_path.read_text(encoding="utf-8") if schema_path.exists() else ""

    new_entries = "\n".join(f"- {s}" for s in sorted(new_slugs))

    if "### Uncategorized" in content:
        uncategorized_idx = content.index("### Uncategorized")
        next_section = content.find("\n## ", uncategorized_idx + 1)
        next_h3 = content.find("\n### ", uncategorized_idx + 1)

        insert_before = len(content)
        if next_section > 0:
            insert_before = min(insert_before, next_section)
        if next_h3 > 0:
            insert_before = min(insert_before, next_h3)

        content = content[:insert_before].rstrip() + "\n" + new_entries + "\n" + content[insert_before:]
    else:
        content = content.rstrip() + f"\n\n### Uncategorized\n{new_entries}\n"

    today = date.today().isoformat()
    content = re.sub(r'updated:\s*"[^"]*"', f'updated: "{today}"', content)

    schema_path.write_text(content, encoding="utf-8")

    if "Uncategorized" not in schema.taxonomy:
        schema.taxonomy["Uncategorized"] = []
    schema.taxonomy["Uncategorized"].extend(new_slugs)
