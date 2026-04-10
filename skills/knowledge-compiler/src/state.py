"""Phase 5: State — 编译状态管理。

职责：
- 更新 .compile-state.json（mtime 快照 + 概念状态）
- 追加 wiki/log.md
- 计算概念级状态：needs_recompile / aging / weak / orphan
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .common import load_state, save_state
from .compiler import _parse_frontmatter


@dataclass
class ConceptState:
    slug: str
    status: str  # "ok" | "needs_recompile" | "aging" | "weak" | "orphan"
    reason: str = ""


def update_compile_state(
    root: Path,
    scanned_files: list[Path],
    topic_map: dict[str, list[Path]],
) -> None:
    """更新 .compile-state.json。"""
    state = load_state(root)

    files_state: dict[str, dict] = {}
    for f in scanned_files:
        rel = str(f.relative_to(root))
        files_state[rel] = {
            "mtime": f.stat().st_mtime,
            "topics": [],
        }

    for slug, files in topic_map.items():
        for f in files:
            rel = str(f.relative_to(root))
            if rel in files_state:
                files_state[rel]["topics"].append(slug)

    state["last_compiled"] = date.today().isoformat()
    state["files"] = files_state
    save_state(root, state)


def append_log(
    root: Path,
    scan_summary: str,
    topics_compiled: int,
    topics_new: int,
    verify_summary: str = "",
) -> None:
    """追加 wiki/log.md 编译日志。"""
    log_path = root / "wiki" / "log.md"
    today = date.today().isoformat()

    entry = f"\n## [{today}] compile\n"
    entry += f"- Files: {scan_summary}\n"
    entry += f"- Topics compiled: {topics_new} new, {topics_compiled - topics_new} updated\n"
    if verify_summary:
        entry += f"- Verify: {verify_summary}\n"

    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Compile Log\n"
    log_path.write_text(existing + entry, encoding="utf-8")


def compute_concept_states(root: Path) -> list[ConceptState]:
    """计算所有概念的状态。"""
    concepts_dir = root / "wiki" / "concepts"
    if not concepts_dir.exists():
        return []

    state = load_state(root)
    files_state = state.get("files", {})

    results: list[ConceptState] = []
    today = date.today()

    for article_path in sorted(concepts_dir.glob("*.md")):
        slug = article_path.stem
        content = article_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)

        sources = meta.get("sources", [])
        if not sources:
            results.append(ConceptState(slug, "orphan", "no sources"))
            continue

        stale_sources = []
        for src in sources:
            src_info = files_state.get(src, {})
            recorded_mtime = src_info.get("mtime", 0)
            src_path = root / src
            if src_path.exists():
                current_mtime = src_path.stat().st_mtime
                if current_mtime > recorded_mtime:
                    stale_sources.append(src)

        if stale_sources:
            results.append(ConceptState(
                slug, "needs_recompile",
                f"stale sources: {', '.join(stale_sources)}"
            ))
            continue

        updated_str = meta.get("updated", "")
        if updated_str:
            try:
                updated_date = date.fromisoformat(str(updated_str))
                age = (today - updated_date).days
                if age > 30:
                    results.append(ConceptState(slug, "aging", f"last updated {age} days ago"))
                    continue
            except (ValueError, TypeError):
                pass

        coverages = []
        for line in body.split("\n"):
            if "<!-- coverage:" in line:
                cov = line.split("coverage:")[1].split("-->")[0].strip()
                coverages.append(cov)

        if coverages:
            low_ratio = coverages.count("low") / len(coverages)
            if low_ratio >= 0.7:
                results.append(ConceptState(slug, "weak", f"{int(low_ratio * 100)}% low coverage"))
                continue

        results.append(ConceptState(slug, "ok"))

    return results
