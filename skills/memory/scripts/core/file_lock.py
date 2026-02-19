"""
基于文件的互斥锁

防止管理工具与 Hook 脚本并发写入 JSONL 文件。
使用 fcntl.flock (Unix) 实现，获取失败时在 timeout 内重试。
"""
import os
import time
import fcntl
import errno


class FileLock:
    """
    文件锁，支持 context manager 和手动 acquire/release。

    用法:
        with FileLock("/path/to/.manage.lock", timeout=10):
            # 受保护的操作
    """

    def __init__(self, lock_path: str, timeout: float = 10.0):
        self._lock_path = lock_path
        self._timeout = timeout
        self._fd = None

    @property
    def lock_path(self) -> str:
        return self._lock_path

    def acquire(self) -> bool:
        """获取锁。成功返回 True，超时返回 False。"""
        os.makedirs(os.path.dirname(self._lock_path) or ".", exist_ok=True)
        self._fd = open(self._lock_path, "w")

        deadline = time.monotonic() + self._timeout
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._fd.write(str(os.getpid()))
                self._fd.flush()
                return True
            except OSError as e:
                if e.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    self._fd.close()
                    self._fd = None
                    return False
                time.sleep(0.1)

    def release(self):
        """释放锁"""
        if self._fd:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                self._fd.close()
            except OSError:
                pass
            finally:
                self._fd = None

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(
                f"无法获取文件锁 {self._lock_path}（超时 {self._timeout}s），另一个操作正在进行"
            )
        return self

    def __exit__(self, *exc):
        self.release()
        return False
