import json
import os
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent

_data_dir_override = os.environ.get("SKILL_STORE_DATA_DIR")
DATA_DIR = Path(_data_dir_override) if _data_dir_override else Path.home() / ".cursor" / "skills" / "skill-store-data"

CONFIG_FILE = DATA_DIR / "config.json"
INDEX_FILE = DATA_DIR / "index.json"
INSTALLED_FILE = DATA_DIR / "installed.json"
STATUS_FILE = DATA_DIR / "status.json"
REPOS_DIR = DATA_DIR / "repos"
WORKER_PID_FILE = DATA_DIR / "worker.pid"

DEFAULT_CONFIG = {
    "registries": [],
    "settings": {
        "clone_depth": 1
    }
}

DEFAULT_INDEX = {
    "updated_at": None,
    "skills": []
}

DEFAULT_INSTALLED = {
    "installations": []
}

DEFAULT_STATUS = {
    "last_sync": None,
    "sync_in_progress": False,
    "pending_updates": [],
    "orphaned_skills": [],
    "sync_errors": []
}

EXCLUDE_PATTERNS = {
    ".git", "node_modules", "__pycache__", ".pyc",
    "data", ".DS_Store", ".env"
}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPOS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(filepath: Path, default: dict) -> dict:
    if not filepath.exists():
        return json.loads(json.dumps(default))
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(default))


def save_json(filepath: Path, data: dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config() -> dict:
    return load_json(CONFIG_FILE, DEFAULT_CONFIG)


def save_config(config: dict):
    save_json(CONFIG_FILE, config)


def load_index() -> dict:
    return load_json(INDEX_FILE, DEFAULT_INDEX)


def save_index(index: dict):
    save_json(INDEX_FILE, index)


def load_installed() -> dict:
    return load_json(INSTALLED_FILE, DEFAULT_INSTALLED)


def save_installed(installed: dict):
    save_json(INSTALLED_FILE, installed)


def load_status() -> dict:
    return load_json(STATUS_FILE, DEFAULT_STATUS)


def save_status(status: dict):
    save_json(STATUS_FILE, status)


def output_result(result=None, error=None):
    print(json.dumps({"result": result, "error": error}, ensure_ascii=False, indent=2))
