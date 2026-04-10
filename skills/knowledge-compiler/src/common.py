"""共用工具函数。"""

import json
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
DEFAULT_CONFIG = SKILL_DIR / "config.json"

CONFIG_FILENAME = ".kc-config.json"
STATE_FILENAME = ".compile-state.json"


def find_project_root(start: Path | None = None) -> Path | None:
    """向上查找包含 .kc-config.json 的目录。"""
    d = (start or Path.cwd()).resolve()
    while d != d.parent:
        if (d / CONFIG_FILENAME).exists():
            return d
        d = d.parent
    return None


def load_config(root: Path) -> dict:
    cfg_path = root / CONFIG_FILENAME
    if not cfg_path.exists():
        return {}
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def save_config(root: Path, config: dict) -> None:
    cfg_path = root / CONFIG_FILENAME
    cfg_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_state(root: Path) -> dict:
    state_path = root / STATE_FILENAME
    if not state_path.exists():
        return {"last_compiled": None, "files": {}}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(root: Path, state: dict) -> None:
    state_path = root / STATE_FILENAME
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_template(name: str) -> str:
    tpl_path = TEMPLATES_DIR / name
    return tpl_path.read_text(encoding="utf-8")
