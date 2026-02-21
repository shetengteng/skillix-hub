"""
会话状态管理模块

统一管理 session_state/ 目录下的会话状态文件，跟踪每个会话的保存状态。
所有读写操作通过 FileLock 保护并发访问。
"""
import os
import json

from core.file_lock import FileLock
from core.utils import iso_now
from service.logger import get_logger

log = get_logger("session_state")


def _state_path(memory_dir: str, session_id: str) -> str:
    return os.path.join(memory_dir, "session_state", f"{session_id}.json")


def _lock_path(memory_dir: str, session_id: str) -> str:
    return os.path.join(memory_dir, "session_state", f".{session_id}.lock")


# --- 读取操作（带降级）---

def read_session_state(memory_dir: str, session_id: str) -> dict:
    """读取会话状态，不存在返回空 dict，异常时降级返回空 dict + 日志告警"""
    path = _state_path(memory_dir, session_id)
    if not os.path.exists(path):
        return {}
    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            with open(path, "r") as f:
                return json.load(f)
    except (TimeoutError, json.JSONDecodeError, OSError) as e:
        log.warning("读取会话状态失败 session=%s: %s（降级为空状态）", session_id[:12], e)
        return {}


def is_summary_saved(memory_dir: str, session_id: str) -> bool:
    """检查该会话是否已保存过摘要（异常时保守返回 False，允许重试保存）"""
    state = read_session_state(memory_dir, session_id)
    return state.get("summary_saved", False)


# --- 写入操作（加锁）---

def mark_summary_saved(memory_dir: str, session_id: str, source: str):
    """标记该会话摘要已保存（加锁写入）"""
    state_dir = os.path.join(memory_dir, "session_state")
    os.makedirs(state_dir, exist_ok=True)
    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            path = _state_path(memory_dir, session_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    state = json.load(f)
            else:
                state = {"session_id": session_id, "created_at": iso_now()}

            state["summary_saved"] = True
            state["summary_source"] = source
            state["updated_at"] = iso_now()

            with open(path, "w") as f:
                json.dump(state, ensure_ascii=False, fp=f)
    except (TimeoutError, OSError) as e:
        log.warning("标记摘要已保存失败 session=%s: %s", session_id[:12], e)


def update_fact_count(memory_dir: str, session_id: str, memory_type: str):
    """更新会话状态中的 fact/阶段摘要计数（加锁写入）"""
    if not session_id:
        return
    state_dir = os.path.join(memory_dir, "session_state")
    os.makedirs(state_dir, exist_ok=True)
    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            path = _state_path(memory_dir, session_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    state = json.load(f)
            else:
                state = {"session_id": session_id, "summary_saved": False, "created_at": iso_now()}

            if memory_type == "S":
                state["stage_summary_count"] = state.get("stage_summary_count", 0) + 1
            else:
                state["fact_count"] = state.get("fact_count", 0) + 1
            state["updated_at"] = iso_now()

            with open(path, "w") as f:
                json.dump(state, ensure_ascii=False, fp=f)
    except (TimeoutError, OSError) as e:
        log.warning("更新 fact 计数失败 session=%s: %s", session_id[:12], e)


# --- 全局文件锁（sessions.jsonl 写入串行化）---

def _sessions_lock_path(memory_dir: str) -> str:
    return os.path.join(memory_dir, ".sessions.lock")


# --- 原子操作 ---

class SaveResult:
    """save_summary_atomic 的返回结果，区分 already_saved 与 error"""
    SAVED = "saved"
    EXISTS = "exists"
    ERROR = "error"

    def __init__(self, status: str, reason: str = ""):
        self.status = status
        self.reason = reason

    @property
    def ok(self) -> bool:
        return self.status == self.SAVED

    def to_dict(self) -> dict:
        d = {"status": self.status}
        if self.reason:
            d["reason"] = self.reason
        return d


def save_summary_atomic(memory_dir: str, session_id: str, source: str,
                        write_fn) -> SaveResult:
    """
    在会话锁 + 全局文件锁内完成"检查已保存 → 写 sessions.jsonl → 标记已保存"。

    参数：
        write_fn: callable，无参数，执行实际的 sessions.jsonl 写入。仅在未保存时调用。
    返回：
        SaveResult(status="saved|exists|error", reason="...")
    """
    state_dir = os.path.join(memory_dir, "session_state")
    os.makedirs(state_dir, exist_ok=True)

    try:
        with FileLock(_lock_path(memory_dir, session_id), timeout=5):
            path = _state_path(memory_dir, session_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    state = json.load(f)
                if state.get("summary_saved"):
                    log.info("摘要已存在（原子检查），跳过 session=%s", session_id[:12])
                    return SaveResult(SaveResult.EXISTS, "already_saved")
            else:
                state = {"session_id": session_id, "created_at": iso_now()}

            with FileLock(_sessions_lock_path(memory_dir), timeout=5):
                write_fn()

            state["summary_saved"] = True
            state["summary_source"] = source
            state["updated_at"] = iso_now()

            with open(path, "w") as f:
                json.dump(state, ensure_ascii=False, fp=f)

            return SaveResult(SaveResult.SAVED)

    except TimeoutError as e:
        log.warning("原子保存摘要锁超时 session=%s: %s", session_id[:12], e)
        return SaveResult(SaveResult.ERROR, f"lock_timeout: {e}")
    except (OSError, json.JSONDecodeError) as e:
        log.warning("原子保存摘要 I/O 异常 session=%s: %s", session_id[:12], e)
        return SaveResult(SaveResult.ERROR, f"io_error: {e}")
