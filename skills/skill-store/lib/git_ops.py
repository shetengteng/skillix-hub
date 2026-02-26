from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: str | Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "git command timed out"
    except FileNotFoundError:
        return -1, "", "git not found in PATH"


def clone(url: str, target_dir: Path, depth: int = 1, branch: str = "main") -> tuple[bool, str]:
    args = ["clone", "--depth", str(depth), "--branch", branch, url, str(target_dir)]
    code, stdout, stderr = run_git(args)
    if code == 0:
        return True, f"Cloned {url} to {target_dir}"
    return False, stderr


def pull(repo_dir: Path) -> tuple[bool, str]:
    code, stdout, stderr = run_git(["pull", "--ff-only"], cwd=repo_dir)
    if code == 0:
        return True, stdout or "Already up to date."
    return False, stderr


def get_latest_commit(repo_dir: Path, path: str | None = None) -> str | None:
    args = ["log", "-1", "--format=%H"]
    if path:
        args += ["--", path]
    code, stdout, _ = run_git(args, cwd=repo_dir)
    if code == 0 and stdout:
        return stdout
    return None


def get_commit_date(repo_dir: Path, path: str | None = None) -> str | None:
    args = ["log", "-1", "--format=%aI"]
    if path:
        args += ["--", path]
    code, stdout, _ = run_git(args, cwd=repo_dir)
    if code == 0 and stdout:
        return stdout
    return None


def get_current_branch(repo_dir: Path) -> str | None:
    code, stdout, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    if code == 0 and stdout:
        return stdout
    return None


def is_git_repo(path: Path) -> bool:
    return (path / ".git").is_dir()
