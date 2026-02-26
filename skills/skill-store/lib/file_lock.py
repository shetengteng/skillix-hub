import fcntl
import json
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(filepath: Path):
    lock_path = filepath.with_suffix(filepath.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


def locked_read_json(filepath: Path, default: dict) -> dict:
    with file_lock(filepath):
        if not filepath.exists():
            return json.loads(json.dumps(default))
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return json.loads(json.dumps(default))


def locked_write_json(filepath: Path, data: dict):
    with file_lock(filepath):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def locked_update_json(filepath: Path, default: dict, updater):
    with file_lock(filepath):
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = json.loads(json.dumps(default))
        else:
            data = json.loads(json.dumps(default))

        updater(data)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
