"""索引管理模块：add / list / remove / edit / import-project"""

import json
import os
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path


def read_index(data_dir: Path) -> list:
    index_file = data_dir / "raw" / "index.jsonl"
    entries = []
    if not index_file.exists():
        return entries
    with open(index_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def write_index(data_dir: Path, entries: list):
    index_file = data_dir / "raw" / "index.jsonl"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    with open(index_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


_id_counter = 0


def generate_id() -> str:
    global _id_counter
    now = datetime.now(timezone.utc)
    _id_counter += 1
    return f"kb-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{_id_counter:03d}"


EXT_TYPE_MAP = {
    ".md": "markdown", ".mdx": "markdown", ".markdown": "markdown", ".rst": "markdown",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".gif": "image", ".svg": "image", ".webp": "image",
    ".ico": "image", ".bmp": "image", ".tiff": "image",
    ".csv": "dataset", ".tsv": "dataset", ".parquet": "dataset",
    ".xlsx": "dataset", ".xls": "dataset",
    ".py": "code", ".js": "code", ".ts": "code", ".tsx": "code", ".jsx": "code",
    ".java": "code", ".go": "code", ".rs": "code", ".c": "code", ".cpp": "code",
    ".h": "code", ".hpp": "code", ".cs": "code", ".rb": "code", ".php": "code",
    ".swift": "code", ".kt": "code", ".scala": "code", ".lua": "code",
    ".sh": "code", ".bash": "code", ".zsh": "code", ".fish": "code",
    ".sql": "code", ".r": "code", ".m": "code",
    ".vue": "code", ".svelte": "code", ".html": "code", ".css": "code",
    ".scss": "code", ".less": "code", ".sass": "code",
    ".yaml": "config", ".yml": "config", ".toml": "config", ".ini": "config",
    ".cfg": "config", ".conf": "config", ".env": "config", ".properties": "config",
    ".json": "config", ".jsonl": "config", ".xml": "config",
    ".txt": "text", ".log": "text", ".tex": "text", ".rtf": "text",
    ".pdf": "binary", ".doc": "binary", ".docx": "binary", ".pptx": "binary",
    ".zip": "binary", ".tar": "binary", ".gz": "binary", ".7z": "binary",
    ".exe": "binary", ".dll": "binary", ".so": "binary", ".dylib": "binary",
    ".whl": "binary", ".egg": "binary",
    ".mp3": "binary", ".mp4": "binary", ".wav": "binary", ".avi": "binary",
}

TEXT_READABLE_TYPES = {"markdown", "code", "config", "text", "dataset"}


def detect_type(path: str) -> str:
    p = Path(path)
    if p.is_dir():
        return "repo" if (p / ".git").exists() else "directory"
    mapped = EXT_TYPE_MAP.get(p.suffix.lower())
    if mapped:
        return mapped
    if _is_text_file(p):
        return "text"
    return "binary"


def _is_text_file(p: Path, sample_size: int = 8192) -> bool:
    try:
        with open(p, "rb") as f:
            chunk = f.read(sample_size)
        if not chunk:
            return True
        if b"\x00" in chunk:
            return False
        return True
    except Exception:
        return False


def compute_hash(path: str, entry_type: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    try:
        if entry_type in TEXT_READABLE_TYPES:
            content = p.read_text(encoding="utf-8", errors="replace")
            return hashlib.md5(content.encode()).hexdigest()[:8]
        elif entry_type == "repo":
            readme = p / "README.md"
            if readme.exists():
                content = readme.read_text(encoding="utf-8", errors="replace")
                return hashlib.md5(content.encode()).hexdigest()[:8]
            return hashlib.md5(str(p).encode()).hexdigest()[:8]
        else:
            stat = p.stat()
            return hashlib.md5(f"{stat.st_size}-{stat.st_mtime}".encode()).hexdigest()[:8]
    except OSError:
        return ""


def extract_title(path: str, entry_type: str) -> str:
    p = Path(path)
    if entry_type == "markdown" and p.exists():
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
        except Exception:
            pass
    if entry_type in ("code", "config", "text", "binary"):
        return p.name
    return p.stem


def infer_category(path: str) -> str:
    parts = Path(path).parts
    for i, part in enumerate(parts):
        if part == "design" and i + 1 < len(parts):
            next_part = parts[i + 1]
            if not next_part.endswith(".md"):
                return next_part
    return "uncategorized"


# ─── 命令实现 ───


def cmd_add(args, data_dir: Path):
    path = os.path.abspath(args.path)

    entry_type = args.entry_type or detect_type(path)

    if not os.path.exists(path) and entry_type != "link":
        print(f"❌ 路径不存在: {path}")
        return

    if entry_type == "directory":
        _add_directory(args, data_dir, path)
        return

    entries = read_index(data_dir)

    for e in entries:
        if e["path"] == path:
            print(f"⚠ 已存在相同路径的索引: {e['id']} ({e['title']})")
            return

    entry = {
        "id": generate_id(),
        "title": args.title or extract_title(path, entry_type),
        "type": entry_type,
        "path": path,
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
        "category": args.category or infer_category(path),
        "summary": "",
        "content_hash": compute_hash(path, entry_type),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "compiled": False,
    }

    entries.append(entry)
    write_index(data_dir, entries)

    print(f"✅ 已添加: {entry['id']}")
    print(f"   标题: {entry['title']}")
    print(f"   类型: {entry['type']}")
    print(f"   分类: {entry['category']}")
    print(f"   标签: {', '.join(entry['tags']) if entry['tags'] else '无'}")


def _add_directory(args, data_dir: Path, dir_path: str):
    pattern = args.pattern or "*.md"
    p = Path(dir_path)

    files = list(p.rglob(pattern)) if args.recursive else list(p.glob(pattern))

    if not files:
        print(f"⚠ 目录中没有匹配 {pattern} 的文件: {dir_path}")
        return

    entries = read_index(data_dir)
    existing_paths = {e["path"] for e in entries}
    added = 0
    skipped = 0

    for f in sorted(files):
        abs_path = str(f.resolve())
        if abs_path in existing_paths:
            skipped += 1
            continue

        entry_type = detect_type(abs_path)
        entry = {
            "id": generate_id(),
            "title": extract_title(abs_path, entry_type),
            "type": entry_type,
            "path": abs_path,
            "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
            "category": args.category or infer_category(abs_path),
            "summary": "",
            "content_hash": compute_hash(abs_path, entry_type),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "compiled": False,
        }
        entries.append(entry)
        added += 1

    write_index(data_dir, entries)
    print(f"✅ 批量添加完成: {added} 个新条目, {skipped} 个已存在跳过")


def cmd_list(args, data_dir: Path):
    entries = read_index(data_dir)

    if args.filter_type:
        entries = [e for e in entries if e["type"] == args.filter_type]
    if args.tag:
        entries = [e for e in entries if args.tag in e.get("tags", [])]
    if args.category:
        entries = [e for e in entries if e["category"] == args.category]
    if args.pending:
        entries = [e for e in entries if not e.get("compiled", False)]

    if not entries:
        print("📭 没有匹配的索引条目")
        return

    by_category = {}
    for e in entries:
        cat = e.get("category", "uncategorized")
        by_category.setdefault(cat, []).append(e)

    total = len(entries)
    pending = sum(1 for e in entries if not e.get("compiled", False))

    print("=== Knowledge Base: 索引列表 ===\n")

    for cat, items in sorted(by_category.items()):
        print(f"📂 {cat} ({len(items)} 个)")
        for e in items:
            status = "⏳" if not e.get("compiled") else "✅"
            tags_str = f" [{', '.join(e['tags'])}]" if e.get("tags") else ""
            print(f"   {status} {e['id']} | {e['title']}{tags_str}")
        print()

    print(f"共 {total} 个条目 | {pending} 个待编译\n")
    print("💡 下一步:")
    if pending > 0:
        print("  - `kb compile --dry-run` — 预览待编译清单")
    print("  - `kb add <path>` — 添加新资料")
    print("  - `kb remove <id>` — 移除条目")


def cmd_remove(args, data_dir: Path):
    entries = read_index(data_dir)
    target_id = args.id

    new_entries = [e for e in entries if e["id"] != target_id]

    if len(new_entries) == len(entries):
        print(f"❌ 未找到 ID: {target_id}")
        return

    removed = [e for e in entries if e["id"] == target_id][0]
    write_index(data_dir, new_entries)
    print(f"✅ 已移除: {target_id} ({removed['title']})")


def cmd_edit(args, data_dir: Path):
    entries = read_index(data_dir)
    target_id = args.id

    found = False
    for e in entries:
        if e["id"] == target_id:
            found = True
            if args.title:
                e["title"] = args.title
            if args.tags:
                e["tags"] = [t.strip() for t in args.tags.split(",")]
            if args.category:
                e["category"] = args.category
            e["updated_at"] = datetime.now(timezone.utc).isoformat()
            print(f"✅ 已更新: {target_id}")
            print(f"   标题: {e['title']}")
            print(f"   标签: {', '.join(e['tags']) if e['tags'] else '无'}")
            print(f"   分类: {e['category']}")
            break

    if not found:
        print(f"❌ 未找到 ID: {target_id}")
        return

    write_index(data_dir, entries)


def cmd_import_project(args, data_dir: Path, skill_dir: Path):
    project_root = skill_dir.parent.parent
    target_dir = project_root / args.dir

    if not target_dir.exists():
        print(f"❌ 目录不存在: {target_dir}")
        return

    pattern = args.pattern
    files = list(target_dir.rglob(pattern))

    if not files:
        print(f"⚠ 目录中没有匹配 {pattern} 的文件: {target_dir}")
        return

    # 排除 refer/ 目录下的文件
    files = [f for f in files if "refer" not in f.parts]

    entries = read_index(data_dir)
    existing_paths = {e["path"] for e in entries}
    added = 0
    skipped = 0

    for f in sorted(files):
        abs_path = str(f.resolve())
        if abs_path in existing_paths:
            skipped += 1
            continue

        entry_type = detect_type(abs_path)
        entry = {
            "id": generate_id(),
            "title": extract_title(abs_path, entry_type),
            "type": entry_type,
            "path": abs_path,
            "tags": [],
            "category": infer_category(abs_path),
            "summary": "",
            "content_hash": compute_hash(abs_path, entry_type),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "compiled": False,
        }
        entries.append(entry)
        added += 1

    write_index(data_dir, entries)
    print(f"✅ 项目导入完成: {added} 个新条目, {skipped} 个已存在跳过")
    print(f"   来源目录: {target_dir}")
    print(f"   匹配模式: {pattern}")
