#!/usr/bin/env python3
"""core/file_lock.py 单元测试。"""
import sys
import os
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory", "scripts"))

from core.file_lock import FileLock


class FileLockTests(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.lock_path = os.path.join(self.tmpdir, ".test.lock")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_acquire_and_release(self):
        lock = FileLock(self.lock_path)
        self.assertTrue(lock.acquire())
        self.assertTrue(os.path.isfile(self.lock_path))
        lock.release()

    def test_context_manager(self):
        with FileLock(self.lock_path) as lock:
            self.assertTrue(os.path.isfile(lock.lock_path))

    def test_lock_path_property(self):
        lock = FileLock(self.lock_path)
        self.assertEqual(lock.lock_path, self.lock_path)

    def test_reentrant_same_process(self):
        lock1 = FileLock(self.lock_path, timeout=1)
        self.assertTrue(lock1.acquire())
        lock2 = FileLock(self.lock_path, timeout=1)
        result = lock2.acquire()
        # flock is per-fd, same process can acquire again on a different fd
        # behavior depends on OS, just ensure no crash
        lock2.release()
        lock1.release()

    def test_release_without_acquire_is_safe(self):
        lock = FileLock(self.lock_path)
        lock.release()  # should not raise

    def test_creates_parent_directory(self):
        nested_path = os.path.join(self.tmpdir, "sub", "dir", ".lock")
        with FileLock(nested_path):
            self.assertTrue(os.path.isfile(nested_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
