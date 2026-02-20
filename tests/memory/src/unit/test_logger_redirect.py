#!/usr/bin/env python3
"""logger 模块扩展测试：redirect_to_project、_get_log_dir、_cleanup_old_logs、_DailyFileHandler"""
import sys
import os
import logging
import tempfile
import shutil
import unittest
import glob
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory", "scripts"))

import service.logger.logger as logger_mod


class _LoggerTestBase(unittest.TestCase):
    """logger 测试基类：隔离全局状态"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_LOG_DIR = logger_mod._LOG_DIR
        self._orig_initialized = logger_mod._initialized
        self._orig_file_handler = logger_mod._file_handler
        self._orig_env_log = os.environ.get("MEMORY_LOG_DIR")
        self._orig_env_proj = os.environ.get("MEMORY_PROJECT_PATH")
        logger_mod._LOG_DIR = None
        logger_mod._initialized = False
        logger_mod._file_handler = None

    def tearDown(self):
        logger_mod._LOG_DIR = self._orig_LOG_DIR
        logger_mod._initialized = self._orig_initialized
        logger_mod._file_handler = self._orig_file_handler
        for env_key, orig_val in [("MEMORY_LOG_DIR", self._orig_env_log),
                                   ("MEMORY_PROJECT_PATH", self._orig_env_proj)]:
            if orig_val is not None:
                os.environ[env_key] = orig_val
            else:
                os.environ.pop(env_key, None)
        for name in list(logging.Logger.manager.loggerDict):
            if name.startswith("memory.test_lr_"):
                logging.Logger.manager.loggerDict.pop(name, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class TestGetLogDir(_LoggerTestBase):

    def test_env_var_takes_priority(self):
        env_dir = os.path.join(self.tmpdir, "env_logs")
        os.makedirs(env_dir, exist_ok=True)
        os.environ["MEMORY_LOG_DIR"] = env_dir
        result = logger_mod._get_log_dir()
        self.assertEqual(result, env_dir)

    def test_project_path_env_takes_second_priority(self):
        os.environ.pop("MEMORY_LOG_DIR", None)
        project = os.path.join(self.tmpdir, "my_project")
        os.makedirs(project, exist_ok=True)
        os.environ["MEMORY_PROJECT_PATH"] = project
        result = logger_mod._get_log_dir()
        self.assertIn(project, result)
        self.assertTrue(result.endswith("logs"))

    def test_fallback_to_cwd_based(self):
        os.environ.pop("MEMORY_LOG_DIR", None)
        os.environ.pop("MEMORY_PROJECT_PATH", None)
        old_cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)
            result = logger_mod._get_log_dir()
            self.assertIn(self.tmpdir, result)
            self.assertTrue(result.endswith("logs"))
        finally:
            os.chdir(old_cwd)

    def test_log_dir_priority_ignores_project_path_when_log_dir_set(self):
        env_dir = os.path.join(self.tmpdir, "explicit_logs")
        os.makedirs(env_dir, exist_ok=True)
        os.environ["MEMORY_LOG_DIR"] = env_dir
        os.environ["MEMORY_PROJECT_PATH"] = os.path.join(self.tmpdir, "project")
        result = logger_mod._get_log_dir()
        self.assertEqual(result, env_dir)

    def test_caches_result(self):
        env_dir = os.path.join(self.tmpdir, "cached_logs")
        os.makedirs(env_dir, exist_ok=True)
        os.environ["MEMORY_LOG_DIR"] = env_dir
        r1 = logger_mod._get_log_dir()
        os.environ["MEMORY_LOG_DIR"] = "/different/path"
        r2 = logger_mod._get_log_dir()
        self.assertEqual(r1, r2)

    def test_creates_directory(self):
        target = os.path.join(self.tmpdir, "new_dir", "logs")
        os.environ["MEMORY_LOG_DIR"] = target
        logger_mod._get_log_dir()
        self.assertTrue(os.path.isdir(target))


class TestCleanupOldLogs(_LoggerTestBase):

    def test_removes_old_logs(self):
        log_dir = os.path.join(self.tmpdir, "logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        open(os.path.join(log_dir, f"{old_date}.log"), "w").close()
        open(os.path.join(log_dir, f"{today}.log"), "w").close()

        logger_mod._cleanup_old_logs()

        remaining = os.listdir(log_dir)
        self.assertNotIn(f"{old_date}.log", remaining)
        self.assertIn(f"{today}.log", remaining)

    def test_ignores_non_date_files(self):
        log_dir = os.path.join(self.tmpdir, "logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        open(os.path.join(log_dir, "random.log"), "w").close()
        logger_mod._cleanup_old_logs()
        self.assertIn("random.log", os.listdir(log_dir))


class TestRedirectToProject(_LoggerTestBase):

    def test_redirect_changes_log_dir(self):
        initial_dir = os.path.join(self.tmpdir, "initial", "logs")
        os.makedirs(initial_dir, exist_ok=True)
        logger_mod._LOG_DIR = initial_dir

        project_path = os.path.join(self.tmpdir, "project")
        os.makedirs(project_path, exist_ok=True)

        logger_mod.redirect_to_project(project_path)

        expected = os.path.join(project_path, ".cursor", "skills", "memory-data", "logs")
        self.assertEqual(logger_mod._LOG_DIR, expected)
        self.assertTrue(os.path.isdir(expected))

    def test_redirect_noop_when_same_dir(self):
        project_path = os.path.join(self.tmpdir, "project")
        expected = os.path.join(project_path, ".cursor", "skills", "memory-data", "logs")
        os.makedirs(expected, exist_ok=True)
        logger_mod._LOG_DIR = expected

        logger_mod.redirect_to_project(project_path)
        self.assertEqual(logger_mod._LOG_DIR, expected)

    def test_redirect_updates_file_handler(self):
        initial_dir = os.path.join(self.tmpdir, "initial", "logs")
        os.makedirs(initial_dir, exist_ok=True)
        os.environ["MEMORY_LOG_DIR"] = initial_dir

        log = logger_mod.get_logger("test_lr_redirect")
        log.info("before redirect")
        self.assertIsNotNone(logger_mod._file_handler)

        project_path = os.path.join(self.tmpdir, "project2")
        os.makedirs(project_path, exist_ok=True)
        logger_mod.redirect_to_project(project_path)

        expected_dir = os.path.join(project_path, ".cursor", "skills", "memory-data", "logs")
        self.assertEqual(logger_mod._file_handler._log_dir, expected_dir)
        self.assertIn(expected_dir, logger_mod._file_handler.baseFilename)
        self.assertIsNone(logger_mod._file_handler._stream)

    def test_redirect_before_any_emit_prevents_wrong_dir_file(self):
        wrong_dir = os.path.join(self.tmpdir, "wrong", "logs")
        os.makedirs(wrong_dir, exist_ok=True)
        os.environ["MEMORY_LOG_DIR"] = wrong_dir

        logger_mod.get_logger("test_lr_no_wrong_file")
        self.assertIsNotNone(logger_mod._file_handler)
        wrong_files = glob.glob(os.path.join(wrong_dir, "*.log"))
        self.assertEqual(len(wrong_files), 0, "No log file should be created before emit")

        project_path = os.path.join(self.tmpdir, "correct_project")
        os.makedirs(project_path, exist_ok=True)
        logger_mod.redirect_to_project(project_path)

        log = logger_mod.get_logger("test_lr_no_wrong_file")
        log.info("after redirect")

        wrong_files = glob.glob(os.path.join(wrong_dir, "*.log"))
        self.assertEqual(len(wrong_files), 0, "No log file should exist in wrong dir")

        correct_dir = os.path.join(project_path, ".cursor", "skills", "memory-data", "logs")
        correct_files = glob.glob(os.path.join(correct_dir, "*.log"))
        self.assertTrue(len(correct_files) > 0, "Log file should be in correct dir")


class TestDailyFileHandler(_LoggerTestBase):

    def test_creates_today_log_file(self):
        log_dir = os.path.join(self.tmpdir, "handler_logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        handler = logger_mod._DailyFileHandler()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.assertIn(today, handler.baseFilename)
        handler.close()

    def test_lazy_init_no_file_before_emit(self):
        log_dir = os.path.join(self.tmpdir, "lazy_logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        handler = logger_mod._DailyFileHandler()
        self.assertIsNone(handler._stream)
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        self.assertEqual(len(log_files), 0)
        handler.close()

    def test_emit_writes_record(self):
        log_dir = os.path.join(self.tmpdir, "emit_logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        handler = logger_mod._DailyFileHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="handler_test_message", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.flush()

        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        self.assertTrue(len(log_files) > 0)
        with open(log_files[0], "r", encoding="utf-8") as f:
            self.assertIn("handler_test_message", f.read())
        handler.close()

    def test_emit_creates_stream_on_first_write(self):
        log_dir = os.path.join(self.tmpdir, "stream_logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        handler = logger_mod._DailyFileHandler()
        self.assertIsNone(handler._stream)

        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="first_write", args=(), exc_info=None,
        )
        handler.emit(record)
        self.assertIsNotNone(handler._stream)
        self.assertFalse(handler._stream.closed)
        handler.close()

    def test_close_sets_stream_to_none(self):
        log_dir = os.path.join(self.tmpdir, "close_logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        handler = logger_mod._DailyFileHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.close()
        self.assertIsNone(handler._stream)


class TestEnsureInit(_LoggerTestBase):

    def test_init_runs_once(self):
        log_dir = os.path.join(self.tmpdir, "init_logs")
        os.makedirs(log_dir)
        logger_mod._LOG_DIR = log_dir

        logger_mod._ensure_init()
        self.assertTrue(logger_mod._initialized)

        logger_mod._ensure_init()
        self.assertTrue(logger_mod._initialized)


class TestInitHookContext(_LoggerTestBase):
    """init_hook_context 统一入口函数测试"""

    def test_returns_project_path_from_event(self):
        from service.config import init_hook_context
        event = {"workspace_roots": [self.tmpdir]}
        result = init_hook_context(event)
        self.assertEqual(result, self.tmpdir)

    def test_sets_env_variable(self):
        from service.config import init_hook_context
        os.environ.pop("MEMORY_PROJECT_PATH", None)
        event = {"workspace_roots": [self.tmpdir]}
        init_hook_context(event)
        self.assertEqual(os.environ.get("MEMORY_PROJECT_PATH"), self.tmpdir)

    def test_redirects_log_dir(self):
        from service.config import init_hook_context
        initial_dir = os.path.join(self.tmpdir, "initial", "logs")
        os.makedirs(initial_dir, exist_ok=True)
        logger_mod._LOG_DIR = initial_dir

        project = os.path.join(self.tmpdir, "project")
        os.makedirs(project, exist_ok=True)
        event = {"workspace_roots": [project]}
        init_hook_context(event)

        expected = os.path.join(project, ".cursor", "skills", "memory-data", "logs")
        self.assertEqual(logger_mod._LOG_DIR, expected)

    def test_falls_back_to_cwd_when_no_roots(self):
        from service.config import init_hook_context
        result = init_hook_context({})
        self.assertEqual(result, os.getcwd())


if __name__ == "__main__":
    unittest.main(verbosity=2)
