"""命令层公共工具。"""

import json
import shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SKILL_DIR.parent.parent
EXCLUDE_COPY = {"__pycache__", ".pyc", "node_modules", ".git", ".DS_Store"}


class A:
    """轻量 args 容器。"""
    pass


def get_data_dir() -> Path:
    config_path = SKILL_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return PROJECT_ROOT / config["data_dir_path"]


def ensure_data_dirs(data_dir: Path):
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
    (data_dir / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
    (data_dir / "wiki" / "categories").mkdir(parents=True, exist_ok=True)
    (data_dir / "compile").mkdir(parents=True, exist_ok=True)
    index_file = data_dir / "raw" / "index.jsonl"
    if not index_file.exists():
        index_file.touch()


def data_dir() -> Path:
    d = get_data_dir()
    ensure_data_dirs(d)
    return d


def copy_source(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE_COPY or item.suffix == ".pyc":
            continue
        dest_item = dst / item.name
        if item.is_dir():
            if dest_item.exists():
                shutil.rmtree(dest_item)
            shutil.copytree(item, dest_item, ignore=shutil.ignore_patterns(*EXCLUDE_COPY))
        else:
            shutil.copy2(item, dest_item)
