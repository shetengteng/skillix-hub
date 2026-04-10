"""Phase 1: Scan — 扫描来源文件变更。

对比 .compile-state.json 中记录的 mtime，输出 new/changed/deleted 三个列表。
"""

from dataclasses import dataclass, field
from pathlib import Path

from .common import load_config, load_state


@dataclass
class ScanResult:
    new_files: list[Path] = field(default_factory=list)
    changed_files: list[Path] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    unchanged_files: list[Path] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.new_files or self.changed_files or self.deleted_files)

    def summary(self) -> str:
        parts = []
        if self.new_files:
            parts.append(f"{len(self.new_files)} new")
        if self.changed_files:
            parts.append(f"{len(self.changed_files)} changed")
        if self.deleted_files:
            parts.append(f"{len(self.deleted_files)} deleted")
        if self.unchanged_files:
            parts.append(f"{len(self.unchanged_files)} unchanged")
        return ", ".join(parts) if parts else "no files"


def scan(root: Path, full: bool = False) -> ScanResult:
    """扫描 raw/ 目录，对比 mtime 快照，返回变更结果。"""
    config = load_config(root)
    state = load_state(root)
    prev_files: dict[str, dict] = state.get("files", {})

    source_dirs = config.get("sources", ["raw"])
    exclude = set(config.get("exclude", []))

    result = ScanResult()
    seen_paths: set[str] = set()

    for src_dir_name in source_dirs:
        src_dir = root / src_dir_name
        if not src_dir.exists():
            continue

        for f in sorted(src_dir.rglob("*")):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".md", ".mdx", ".rst", ".txt"):
                continue

            rel = str(f.relative_to(root))
            if any(rel.startswith(ex) for ex in exclude):
                continue

            seen_paths.add(rel)
            current_mtime = f.stat().st_mtime

            if full:
                if rel in prev_files:
                    result.changed_files.append(f)
                else:
                    result.new_files.append(f)
            elif rel not in prev_files:
                result.new_files.append(f)
            elif current_mtime > prev_files[rel].get("mtime", 0):
                result.changed_files.append(f)
            else:
                result.unchanged_files.append(f)

    for prev_rel in prev_files:
        if prev_rel not in seen_paths:
            result.deleted_files.append(prev_rel)

    return result
