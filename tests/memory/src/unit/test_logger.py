#!/usr/bin/env python3
"""service/logger 单元测试。"""
import sys
import os
import logging
import tempfile
import shutil
import unittest
import glob

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory", "scripts"))

import service.logger.logger as logger_mod


class LoggerTests(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_log_dir = logger_mod._LOG_DIR
        self.orig_initialized = logger_mod._initialized
        self.orig_file_handler = logger_mod._file_handler
        log_dir = os.path.join(self.tmpdir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        logger_mod._LOG_DIR = log_dir
        logger_mod._initialized = False
        logger_mod._file_handler = None

    def tearDown(self):
        logger_mod._LOG_DIR = self.orig_log_dir
        logger_mod._initialized = self.orig_initialized
        logger_mod._file_handler = self.orig_file_handler
        for name in list(logging.Logger.manager.loggerDict):
            if name.startswith("memory.test_"):
                logging.Logger.manager.loggerDict.pop(name, None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_get_logger_returns_logger(self):
        log = logger_mod.get_logger("test_unit")
        self.assertIsInstance(log, logging.Logger)
        self.assertEqual(log.name, "memory.test_unit")

    def test_get_logger_creates_log_directory(self):
        logger_mod.get_logger("test_dir")
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, "logs")))

    def test_logger_writes_to_file(self):
        log = logger_mod.get_logger("test_write")
        log.info("测试日志消息")
        if logger_mod._file_handler:
            logger_mod._file_handler.flush()
        log_files = glob.glob(os.path.join(self.tmpdir, "logs", "*.log"))
        self.assertTrue(len(log_files) > 0, "应创建日志文件")
        with open(log_files[0], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("测试日志消息", content)

    def test_get_logger_idempotent(self):
        log1 = logger_mod.get_logger("test_idem")
        log2 = logger_mod.get_logger("test_idem")
        self.assertIs(log1, log2)
        self.assertEqual(len(log1.handlers), len(log2.handlers))


if __name__ == "__main__":
    unittest.main(verbosity=2)
