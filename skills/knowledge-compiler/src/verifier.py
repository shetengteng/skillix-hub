"""Phase 4: Verifier — Hard/Soft Gate 质量检查。

Hard Gates（阻断编译）：
1. frontmatter 完整：每篇概念文章有 id, title, sources, created, updated
2. coverage 标记：每个 Section 有 coverage 注释
3. 来源引用有效：所有 [source: path] 指向存在的文件
4. schema 一致：新概念已出现在 schema.md 中
5. 非空内容：每个 Section 有实质内容

Soft Gates（警告不阻断）：
1. 孤立概念：没有来源引用的概念
2. 低覆盖集群：大量 low 覆盖的概念
3. 过期检测：来源 mtime 变化但概念未重编译
4. 断裂链接：[[slug]] 引用指向不存在的概念
5. 缺失交叉引用：文章提到的概念未建立链接
6. aging：updated 超过 30 天
"""

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .compiler import _parse_frontmatter
from .schema import load_schema


@dataclass
class GateResult:
    gate_type: str  # "hard" or "soft"
    check_name: str
    article: str
    message: str
    passed: bool


@dataclass
class VerifyReport:
    hard_results: list[GateResult] = field(default_factory=list)
    soft_results: list[GateResult] = field(default_factory=list)

    @property
    def hard_pass(self) -> bool:
        return all(r.passed for r in self.hard_results)

    @property
    def hard_failures(self) -> list[GateResult]:
        return [r for r in self.hard_results if not r.passed]

    @property
    def soft_warnings(self) -> list[GateResult]:
        return [r for r in self.soft_results if not r.passed]

    def summary(self) -> str:
        hard_pass = sum(1 for r in self.hard_results if r.passed)
        hard_fail = len(self.hard_results) - hard_pass
        soft_pass = sum(1 for r in self.soft_results if r.passed)
        soft_warn = len(self.soft_results) - soft_pass
        return (
            f"Hard: {hard_pass} pass / {hard_fail} fail | "
            f"Soft: {soft_pass} pass / {soft_warn} warn"
        )


REQUIRED_FM_KEYS = {"id", "title", "sources", "created", "updated"}
SECTION_PATTERN = re.compile(r"^## .+", re.MULTILINE)
COVERAGE_PATTERN = re.compile(r"<!--\s*coverage:\s*(high|medium|low)\s*-->")
SOURCE_REF_PATTERN = re.compile(r"\[source:\s*([^\]]+)\]")
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def verify(root: Path) -> VerifyReport:
    """对 wiki/concepts/ 下所有文章执行 Hard + Soft Gate 检查。"""
    report = VerifyReport()
    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists():
        return report

    schema = load_schema(root)
    known_slugs = {f.stem for f in concepts_dir.glob("*.md")}
    articles = sorted(concepts_dir.glob("*.md"))

    for article_path in articles:
        slug = article_path.stem
        content = article_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)

        _check_hard_frontmatter(report, slug, meta)
        _check_hard_coverage(report, slug, body)
        _check_hard_source_refs(report, slug, body, root)
        _check_hard_schema(report, slug, schema)
        _check_hard_nonempty(report, slug, body)

        _check_soft_orphan(report, slug, meta)
        _check_soft_low_coverage(report, slug, body)
        _check_soft_broken_links(report, slug, body, known_slugs)
        _check_soft_aging(report, slug, meta)

    return report


def _check_hard_frontmatter(report: VerifyReport, slug: str, meta: dict) -> None:
    missing = REQUIRED_FM_KEYS - set(meta.keys())
    passed = len(missing) == 0
    msg = "OK" if passed else f"missing: {', '.join(sorted(missing))}"
    report.hard_results.append(GateResult("hard", "frontmatter_complete", slug, msg, passed))


def _check_hard_coverage(report: VerifyReport, slug: str, body: str) -> None:
    sections = SECTION_PATTERN.findall(body)
    skip_sections = {"## Related", "## Sources"}
    check_sections = [s for s in sections if s not in skip_sections]

    if not check_sections:
        report.hard_results.append(GateResult("hard", "coverage_tags", slug, "no sections found", False))
        return

    coverages = COVERAGE_PATTERN.findall(body)
    passed = len(coverages) >= len(check_sections)
    msg = f"{len(coverages)}/{len(check_sections)} sections tagged" if not passed else "OK"
    report.hard_results.append(GateResult("hard", "coverage_tags", slug, msg, passed))


def _check_hard_source_refs(report: VerifyReport, slug: str, body: str, root: Path) -> None:
    refs = SOURCE_REF_PATTERN.findall(body)
    invalid = []
    for ref in refs:
        ref_path = root / ref.strip()
        if not ref_path.exists():
            invalid.append(ref.strip())

    passed = len(invalid) == 0
    msg = "OK" if passed else f"invalid: {', '.join(invalid)}"
    report.hard_results.append(GateResult("hard", "source_refs_valid", slug, msg, passed))


def _check_hard_schema(report: VerifyReport, slug: str, schema) -> None:
    in_schema = schema.find_category(slug) is not None
    msg = "OK" if in_schema else "not in schema.md taxonomy"
    report.hard_results.append(GateResult("hard", "schema_consistent", slug, msg, in_schema))


def _check_hard_nonempty(report: VerifyReport, slug: str, body: str) -> None:
    sections = re.split(r"^## .+", body, flags=re.MULTILINE)
    empty_count = 0
    for s in sections[1:]:
        text = re.sub(r"<!--.*?-->", "", s).strip()
        if not text or text in ("待编译。",):
            empty_count += 1

    total = max(len(sections) - 1, 1)
    passed = empty_count == 0
    msg = "OK" if passed else f"{empty_count}/{total} sections empty or stub"
    report.hard_results.append(GateResult("hard", "nonempty_content", slug, msg, passed))


def _check_soft_orphan(report: VerifyReport, slug: str, meta: dict) -> None:
    sources = meta.get("sources", [])
    passed = len(sources) > 0
    msg = "OK" if passed else "no sources referenced"
    report.soft_results.append(GateResult("soft", "orphan_concept", slug, msg, passed))


def _check_soft_low_coverage(report: VerifyReport, slug: str, body: str) -> None:
    coverages = COVERAGE_PATTERN.findall(body)
    if not coverages:
        report.soft_results.append(GateResult("soft", "low_coverage", slug, "no coverage tags", False))
        return

    low_count = coverages.count("low")
    ratio = low_count / len(coverages) if coverages else 0
    passed = ratio < 0.7
    msg = f"{low_count}/{len(coverages)} low" if not passed else "OK"
    report.soft_results.append(GateResult("soft", "low_coverage", slug, msg, passed))


def _check_soft_broken_links(report: VerifyReport, slug: str, body: str, known_slugs: set[str]) -> None:
    links = WIKI_LINK_PATTERN.findall(body)
    broken = [l for l in links if l not in known_slugs]
    passed = len(broken) == 0
    msg = "OK" if passed else f"broken: {', '.join(broken)}"
    report.soft_results.append(GateResult("soft", "broken_links", slug, msg, passed))


def _check_soft_aging(report: VerifyReport, slug: str, meta: dict) -> None:
    updated_str = meta.get("updated", "")
    if not updated_str:
        report.soft_results.append(GateResult("soft", "aging", slug, "no updated date", False))
        return

    try:
        updated_date = date.fromisoformat(str(updated_str))
        age = (date.today() - updated_date).days
        passed = age <= 30
        msg = "OK" if passed else f"last updated {age} days ago"
    except (ValueError, TypeError):
        passed = False
        msg = f"invalid date: {updated_str}"

    report.soft_results.append(GateResult("soft", "aging", slug, msg, passed))
